// import { PrismaClient, Document, Project, PendingDocument, PendingDocumentStatus } from '../generated/prisma'; // Weaviate replaces Prisma for these
import crypto from 'crypto';
import { genAI } from '../lib/gemini-client.js'; // Import shared Gemini client
import { weaviateClient, addDocumentSource, addDocumentChunk, getDocumentChunkBatcher } from '../lib/weaviate.service.js';
import { PlaywrightCrawler, Dataset } from 'crawlee';
import { URL } from 'url';

// Interface for the context required to call other MCP tools
export interface ToolCallingContext {
    server: any; // We pass the full McpServer instance
}

// --- Helper to chunk markdown content ---
interface MarkdownChunk {
    content: string;
    order: number;
    // Potentially add other metadata like headings later
}

function chunkMarkdownContent(markdown: string): MarkdownChunk[] {
    if (!markdown || markdown.trim() === '') {
        return [];
    }
    // Simple split by double newlines (paragraphs)
    const paragraphs = markdown.split(/\n\s*\n/);
    return paragraphs.map((p, index) => ({
        content: p.trim(),
        order: index,
    })).filter(chunk => chunk.content.length > 0);
}

interface DiscoveredPageInfo {
    url: string;
    title?: string;
    depth?: number;
}

// --- Helper to create DocumentSource objects from discovered pages ---
async function createDocumentSourcesFromDiscovery(
    projectAlias: string,
    pages: DiscoveredPageInfo[],
    discoveryMethod: string
): Promise<void> {
    let createdCount = 0;
    for (const page of pages) {
        try {
            const documentSourceData = {
                projectAlias,
                url: page.url,
                title: page.title || 'Untitled',
                type: 'documentation',
                status: 'discovered',
                discoveryMethod,
                lastCrawledAt: new Date(),
            };
            await addDocumentSource(documentSourceData);
            createdCount++;
        } catch (error) {
            console.error(`[DocDiscovery] Failed to create DocumentSource for ${page.url}:`, error);
        }
    }
    console.log(`[DocDiscovery] Successfully created ${createdCount} DocumentSource entries.`);
}

// =================================================================
// TOOL: discover_document_structure
// =================================================================
// This tool now uses Crawlee for robust site discovery.

export async function discoverDocumentStructure(
    params: { project_alias: string; base_url: string },
    ctx: ToolCallingContext
): Promise<{ success: boolean; message: string; discoveredPages?: DiscoveredPageInfo[] }> {
    const { project_alias: projectAlias, base_url: baseUrl } = params;
    console.log(`[DocDiscovery] Starting Crawlee-based discovery for ${baseUrl}`);

    try {
        const discoveredPages: DiscoveredPageInfo[] = [];
        const crawler = new PlaywrightCrawler({
            maxRequestsPerCrawl: 500, // Limit pages to avoid excessive crawling
            maxConcurrency: 5,
            requestHandler: async ({ request, page, enqueueLinks, log }) => {
                const title = await page.title();
                log.info(`Crawled ${request.url}: ${title}`);
                discoveredPages.push({
                    url: request.loadedUrl || request.url,
                    title,
                    depth: request.userData.depth,
                });

                // Enqueue links that are likely part of the documentation.
                await enqueueLinks({
                    // Flexible patterns to find doc links
                    globs: [
                        `${new URL(baseUrl).origin}/**/docs/**`,
                        `${new URL(baseUrl).origin}/**/doc/**`,
                        `${new URL(baseUrl).origin}/**/documentation/**`,
                        `${new URL(baseUrl).origin}/**/api/**`,
                        `${new URL(baseUrl).origin}/**/guide/**`,
                        `${new URL(baseUrl).origin}/**/reference/**`,
                    ],
                    // Exclude common non-content links
                    exclude: [
                        '**/blog/**',
                        '**/news/**',
                        '**/changelog/**',
                        '**/*.{zip,pdf,jpg,png,svg}',
                    ],
                });
            },
        });

        await crawler.run([baseUrl]);

        if (discoveredPages.length === 0) {
            return { success: false, message: 'Crawlee discovery ran but found no pages. The site might be heavily JavaScript-driven or have a non-standard structure.' };
        }

        console.log(`[DocDiscovery] Crawlee discovered ${discoveredPages.length} pages.`);
        await createDocumentSourcesFromDiscovery(projectAlias, discoveredPages, 'crawlee-discovery');

        return {
            success: true,
            message: `Successfully discovered ${discoveredPages.length} pages.`,
            discoveredPages,
        };
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`[DocDiscovery] Crawlee discovery failed for ${baseUrl}:`, error);
        return { success: false, message: `Crawlee discovery failed: ${errorMessage}` };
    }
}


// =================================================================
// TOOL: ingest_web_document
// =================================================================

interface IngestionResult {
    success: boolean;
    sourceUrl: string;
    message: string;
    documentSourceId?: string;
}

// --- Scraping Helpers ---

// New primary scraper using Crawlee
async function scrapeWithCrawlee(url: string): Promise<{ title: string; markdown: string } | null> {
    console.log(`[DocIngestion] Attempting to scrape with Crawlee for ${url}`);
    try {
        let content: { title: string, markdown: string } | null = null;
        const crawler = new PlaywrightCrawler({
            maxRequests: 1, // Only process the single starting URL
            requestHandler: async ({ page }) => {
                const title = await page.title();
                // A more robust solution would use a library like `turndown` or `markdownify`
                // For now, we'll extract the main content's text.
                const mainContent = await page.evaluate(() => {
                    const main = document.querySelector('main, article, [role="main"]');
                    return main ? main.innerText : document.body.innerText;
                });
                content = { title, markdown: mainContent };
            },
        });
        await crawler.run([url]);
        return content;
    } catch (error) {
        console.error(`[DocIngestion] Crawlee scrape failed for ${url}:`, error);
        return null;
    }
}

// Updated Gemini scraper using the new SDK
async function scrapeWithGemini(url: string): Promise<{ title: string; markdown: string } | null> {
    console.log(`[DocIngestion] Attempting to scrape with Gemini for ${url}`);
    try {
        const modelName = 'gemini-2.5-flash-lite-preview-06-17'; // As requested
        const prompt = `Please extract the main content from the URL provided, format it as clean Markdown, and include the page title. The URL is: ${url}`;

        const result = await genAI.models.generateContent({
            model: modelName,
            contents: [{
                role: "user",
                parts: [{ text: prompt }]
            }],
        });

        const responseText = result.response.text();
        
        const titleMatch = responseText.match(/^Title:\s*(.*)/m);
        const title = titleMatch ? titleMatch[1] : 'Untitled';
        const markdown = responseText.substring(titleMatch ? titleMatch[0].length : 0).trim();

        return { title, markdown };
    } catch (error) {
        console.error(`[DocIngestion] Gemini scrape failed for ${url}:`, error);
        // Fallback model attempt
        try {
            console.log(`[DocIngestion] Falling back to gemini-2.5-flash model.`);
            const fallbackModelName = 'gemini-2.5-flash';
            const result = await genAI.models.generateContent({ model: fallbackModelName, contents: [{ role: "user", parts: [{ text: `Extract content from ${url} as Markdown.` }] }] });
            const responseText = result.response.text();
            const titleMatch = responseText.match(/^Title:\s*(.*)/m);
            const title = titleMatch ? titleMatch[1] : 'Untitled';
            const markdown = responseText.substring(titleMatch ? titleMatch[0].length : 0).trim();
            return { title, markdown };
        } catch (fallbackError) {
            console.error(`[DocIngestion] Gemini fallback scrape also failed for ${url}:`, fallbackError);
            return null;
        }
    }
}


export async function ingestWebDocument(
    params: { project_alias: string; url: string },
    ctx: ToolCallingContext
): Promise<IngestionResult> {
    const { project_alias: projectAlias, url } = params;
    console.log(`[DocIngestion] Starting ingestion for URL: ${url} for project ${projectAlias}`);

    let scrapeResult: { title: string; markdown: string } | null = null;

    // Attempt 1: Scrape with Gemini (as it might provide cleaner, summarized content)
    scrapeResult = await scrapeWithGemini(url);

    // Attempt 2: Fallback to Crawlee for robust raw content extraction
    if (!scrapeResult || !scrapeResult.markdown) {
        console.log('[DocIngestion] Gemini scrape failed or returned no content. Falling back to Crawlee.');
        scrapeResult = await scrapeWithCrawlee(url);
    }

    if (!scrapeResult || !scrapeResult.markdown) {
        return { success: false, sourceUrl: url, message: 'All scraping attempts (Gemini, Crawlee) failed to retrieve content.' };
    }

    const { title: documentTitle, markdown: documentContent } = scrapeResult;

    try {
        const documentSourceData = {
            projectAlias,
            url,
            title: documentTitle,
            type: 'documentation',
            status: 'ingested',
            discoveryMethod: 'direct-ingestion',
            lastCrawledAt: new Date(),
        };

        const sourceResult = await addDocumentSource(documentSourceData);
        const documentSourceId = sourceResult.id;

        const chunks = chunkMarkdownContent(documentContent);
        if (chunks.length === 0) {
            console.log(`[DocIngestion] DocumentSource created for '${documentTitle}', but no content chunks were generated from the scraped markdown.`);
            return { success: true, documentSourceId, sourceUrl: url, message: 'DocumentSource created, but no content chunks to add.' };
        }

        let chunkBatcher = getDocumentChunkBatcher();
        let chunkCount = 0;

        for (const chunk of chunks) {
            const chunkData = {
                content: chunk.content,
                order: chunk.order,
                sourceUrl: url,
            };
            chunkBatcher = chunkBatcher.withObject(await addDocumentChunk(chunkData, documentSourceId, true));
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
