import { PlaywrightCrawler, Dataset, PlaywrightCrawlingContext, Dictionary } from 'crawlee';
import { URL } from 'url';
import { genAI } from '../lib/gemini-client.js';
import { weaviateClient, addDocumentSource, getDocumentChunkBatcher } from '../lib/weaviate.service.js';

// Interface for the context required to call other MCP tools
export interface ToolCallingContext {
    server: any; // We pass the full McpServer instance
}

// Define and export input schemas for tools
export interface DiscoverDocumentStructureInput {
    project_alias: string;
    base_url: string;
}

export interface IngestWebDocumentInput {
    project_alias: string;
    url: string;
}

// --- Helper to chunk markdown content ---
interface MarkdownChunk {
    content: string;
    order: number;
}

function chunkMarkdownContent(markdown: string): MarkdownChunk[] {
    if (!markdown || markdown.trim() === '') {
        return [];
    }
    const paragraphs = markdown.split(/\n\s*\n/);
    return paragraphs.map((p, index) => ({
        content: p.trim(),
        order: index,
    })).filter(chunk => chunk.content.length > 0);
}

interface DiscoveredPageInfo {
    url: string;
    title?: string;
}

async function createDocumentSourcesFromDiscovery(
    projectAlias: string,
    pages: DiscoveredPageInfo[],
    discoveryMethod: string
): Promise<void> {
    const batcher = weaviateClient.batch.objectsBatcher();
    let createdCount = 0;

    for (const page of pages) {
        const documentSourceData = {
            class: 'DocumentSource',
            properties: {
                projectAlias,
                url: page.url,
                title: page.title || 'Untitled',
                sourceType: 'documentation',
                status: 'discovered',
                lastCrawledAt: new Date(),
            }
        };
        batcher.withObject(documentSourceData);
        createdCount++;
    }

    if (createdCount > 0) {
        await batcher.do();
    }
    console.log(`[DocIngestion] Batched ${createdCount} DocumentSource entries from discovery.`);
}

// --- Main Tool: discover_document_structure ---
export async function discoverDocumentStructure(
    ctx: ToolCallingContext,
    input: DiscoverDocumentStructureInput
): Promise<{ success: boolean; discovered_count: number; message: string; }> {
    const { project_alias, base_url } = input;
    console.log(`[DocIngestion] Starting discovery for project '${project_alias}' at base URL '${base_url}'...`);

    try {
        const crawler = new PlaywrightCrawler({
            maxRequestsPerCrawl: 100,
            async requestHandler({ request, page, log }: PlaywrightCrawlingContext) {
                const title = await page.title();
                log.info(`Discovered: ${title}`, { url: request.loadedUrl });
                await Dataset.pushData({ url: request.loadedUrl, title });
            },
        });

        await crawler.run([base_url]);
        const dataset = await Dataset.open();
        const { items } = await dataset.getData();

        if (items.length === 0) {
            return { success: true, discovered_count: 0, message: 'Discovery ran, but no pages were found.' };
        }

        const discoveredPages: DiscoveredPageInfo[] = items.map((item: Dictionary) => ({
            url: item.url as string,
            title: item.title as string,
        }));

        await createDocumentSourcesFromDiscovery(project_alias, discoveredPages, 'sitemap_crawl');

        console.log(`[DocIngestion] Discovery complete for '${base_url}'. Found ${items.length} pages.`);
        return { success: true, discovered_count: items.length, message: `Discovery complete. Found ${items.length} pages.` };

    } catch (error) {
        console.error(`[DocIngestion] Error during document structure discovery for '${base_url}':`, error);
        return { success: false, discovered_count: 0, message: 'An error occurred during crawling: ' + (error instanceof Error ? error.message : String(error)) };
    }
}

// --- Gemini Helper for Summarization (example) ---
async function summarizeContentWithGemini(content: string): Promise<string> {
    try {
        const prompt = `Summarize the following content concisely for a technical audience:\n\n---\n${content}\n---\n\nSummary:`;
        const result = await genAI.models.generateContent({
            model: "gemini-2.5-flash", // KEEP this model unchanged
            contents: [{ role: "user", parts: [{ text: prompt }] }],
        });
        const text = result.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!text) {
            console.error("[DocIngestion] Gemini response is empty or has an unexpected structure:", JSON.stringify(result, null, 2));
            return "";
        }
        return text;
    } catch (error) {
        console.error("[DocIngestion] Error summarizing content with Gemini:", error);
        return "";
    }
}

// --- Main Tool: ingest_web_document ---
export async function ingestWebDocument(
    ctx: ToolCallingContext,
    input: IngestWebDocumentInput
): Promise<{ success: boolean; documentSourceId?: string; sourceUrl: string; message: string; }> {
    const { project_alias, url } = input;
    console.log(`[DocIngestion] Starting ingestion for URL: ${url}`);

    try {
        let documentContent = '';
        let documentTitle = '';

        const crawler = new PlaywrightCrawler({
            maxRequestsPerCrawl: 1,
            async requestHandler({ page, request, log }: PlaywrightCrawlingContext) {
                log.info(`Scraping content from: ${request.loadedUrl}`);
                documentTitle = await page.title();
                const bodyText = await page.evaluate(() => document.body.innerText);
                documentContent = bodyText.replace(/\n{2,}/g, '\n\n');
            },
        });

        await crawler.run([url]);

        if (!documentContent) {
            console.warn(`[DocIngestion] No content was scraped from URL: ${url}`);
            return { success: false, sourceUrl: url, message: 'Failed to scrape any content from the URL.' };
        }

        console.log(`[DocIngestion] Scraped content from '${documentTitle}'. Content length: ${documentContent.length}. Now processing for Weaviate.`);

        const documentSourceData = {
            projectAlias: project_alias,
            url: url,
            title: documentTitle,
            sourceType: 'documentation',
            status: 'ingested',
            lastCrawledAt: new Date(),
        };

        const documentSourceId = await addDocumentSource(documentSourceData);

        const chunks = chunkMarkdownContent(documentContent);
        if (chunks.length === 0) {
            console.log(`[DocIngestion] DocumentSource created for '${documentTitle}', but no content chunks were generated.`);
            return { success: true, documentSourceId, sourceUrl: url, message: 'DocumentSource created, but no content chunks to add.' };
        }

        let chunkBatcher = getDocumentChunkBatcher();
        let chunkCount = 0;

        for (const chunk of chunks) {
            const chunkData = {
                class: 'DocumentChunk',
                properties: {
                    content: chunk.content,
                    chunkOrder: chunk.order,
                    sourceUrl: url,
                    fromDocumentSource: [{
                        beacon: `weaviate://localhost/DocumentSource/${documentSourceId}`
                    }]
                }
            };
            chunkBatcher.withObject(chunkData);
            chunkCount++;
        }

        if (chunkCount > 0) {
            const batchResult = await chunkBatcher.do();
            batchResult.forEach(item => {
                if (item.result?.errors) {
                    console.error(`[DocIngestion] Error importing chunk for ${url}:`, item.result.errors);
                }
            });
        }

        console.log(`[DocIngestion] Successfully ingested document '${documentTitle}' (Source ID: ${documentSourceId}) from URL '${url}', ${chunkCount} chunks added.`);
        return { success: true, documentSourceId, sourceUrl: url, message: `Ingested ${chunkCount} chunks.` };

    } catch (error) {
        console.error(`[DocIngestion] Error saving document and chunks from URL '${url}' to Weaviate:`, error);
        return { success: false, sourceUrl: url, message: 'Error during Weaviate operation: ' + (error instanceof Error ? error.message : String(error)) };
    }
}
