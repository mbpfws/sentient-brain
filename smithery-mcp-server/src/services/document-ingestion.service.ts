// import { PrismaClient, Document, Project, PendingDocument, PendingDocumentStatus } from '../generated/prisma'; // Weaviate replaces Prisma for these
import crypto from 'crypto';
import { genAI } from '../lib/gemini-client.js'; // Import shared Gemini client
import { weaviateClient, addDocumentSource, addDocumentChunk, getDocumentChunkBatcher } from '../lib/weaviate.service.js';

// Interface for the context required to call other MCP tools
export interface ToolCallingContext {
    callTool: (
        targetServer: string, // e.g., '@smithery/toolbox'
        toolName: string,     // e.g., 'use_tool'
        toolArgs: any         // Arguments for the tool being called
    ) => Promise<any>; // The expected structure of the tool's response
}

// const prisma = new PrismaClient(); // Prisma client removed

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
    // More sophisticated chunking can be added later (e.g., by token count, respecting headings)
    const paragraphs = markdown.split(/\n\s*\n/);
    return paragraphs.map((p, index) => ({
        content: p.trim(),
        order: index,
    })).filter(chunk => chunk.content.length > 0); // Filter out empty chunks
}

interface DiscoveredPageInfo {
    url: string;
    title?: string;
    depth?: number;
}

// --- Helper to create DocumentSource objects from discovered pages ---
async function createDocumentSourcesFromDiscovery(
    projectAlias: string, // Changed from projectId to projectAlias
    pages: DiscoveredPageInfo[],
    discoveryMethod: string
): Promise<void> {
    let createdCount = 0;
    for (const page of pages) {
        try {
            // Check if a DocumentSource with this URL already exists for this projectAlias
            // Weaviate's GraphQL query would be used here. For now, we'll assume we create or update.
            // A more robust check would query Weaviate for an existing DocumentSource with the same URL and projectAlias.
            // const existing = await weaviateClient.graphql.get()... (implementation detail for later)

            const documentSourceData = {
                url: page.url,
                title: page.title || page.url,
                sourceType: discoveryMethod, // e.g., 'sitemap_crawl', 'firecrawl_map'
                projectId: projectAlias, // Using alias as projectId in Weaviate
                lastCrawledAt: new Date(),
                status: 'DISCOVERED', // Initial status
                // depth: page.depth, // Add if 'depth' is part of DocumentSource schema
                techStack: [], // Placeholder, can be enriched later
            };
            await addDocumentSource(documentSourceData);
            createdCount++;
        } catch (error) {
            console.error(`[DocDiscovery] Error creating DocumentSource for URL '${page.url}':`, error);
        }
    }
    console.log(`[DocDiscovery] Processed ${pages.length} discovered pages. Created/updated ${createdCount} DocumentSource entries using ${discoveryMethod}.`);
}

// --- Site Mapping Strategy 1: Firecrawl 'map' tool ---
async function attemptFirecrawlMap(
    ctx: ToolCallingContext,
    baseUrl: string
): Promise<DiscoveredPageInfo[]> {
    try {
        console.log(`[DocDiscovery] Attempt 1: Mapping site with Firecrawl 'map' for ${baseUrl}`);
        const toolboxResponse = await ctx.callTool(
            '@smithery/toolbox',
            'use_tool',
            {
                target_server_id: 'firecrawl-mcp-server',
                tool_name: 'map',
                tool_args: { url: baseUrl, sitemapOnly: false, includeSubdomains: false, limit: 500 }
            }
        );
        if (toolboxResponse && toolboxResponse.content && toolboxResponse.content[0] && toolboxResponse.content[0].type === 'application/json') {
            const firecrawlResult = JSON.parse(toolboxResponse.content[0].content);
            if (firecrawlResult.success && Array.isArray(firecrawlResult.data)) {
                // Assuming firecrawl 'map' returns an array of strings (URLs)
                // For titles, we might need another step or a different tool if 'map' doesn't provide them.
                // For now, we'll use the URL as the title if not available.
                const pages: DiscoveredPageInfo[] = firecrawlResult.data.map((item: string | {url: string, title?: string}) => {
                    if (typeof item === 'string') return { url: item, title: item };
                    return { url: item.url, title: item.title || item.url }; 
                });
                console.log(`[DocDiscovery] Firecrawl 'map' found ${pages.length} URLs.`);
                return pages;
            }
        }
        console.warn(`[DocDiscovery] Firecrawl 'map' failed or returned unexpected data for ${baseUrl}.`);
        return [];
    } catch (error: any) {
        console.error(`[DocDiscovery] Error during Firecrawl 'map' for ${baseUrl}:`, error);
        return [];
    }
}

// --- Site Mapping Strategy 2: Google Search via Gemini ---
async function attemptGoogleSearchSiteMap(
    baseUrl: string
): Promise<DiscoveredPageInfo[]> {
    try {
        console.log(`[DocDiscovery] Attempt 2: Mapping site with Google Search (site:${baseUrl})`);
        const model = genAI.getGenerativeModel({ 
            model: 'gemini-1.5-flash', 
            tools: [{googleSearchRetrieval: {}}]
        });
        const prompt = `Find all unique documentation pages available under the URL path starting with ${baseUrl}. List their full URLs and page titles. Focus on HTML pages, not PDFs or other file types unless they are primary documentation.`;
        
        const result = await model.generateContent(prompt);
        const response = result.response;
        const functionCalls = response.functionCalls();

        if (functionCalls && functionCalls.length > 0) {
            // Assuming the model makes a Google Search call and we need to process its results.
            // This part is highly dependent on how Gemini structures search results in function calls.
            // For now, we'll assume it returns a list of URLs and titles in a structured way.
            // This is a placeholder and needs refinement based on actual Gemini output.
            console.warn("[DocDiscovery] Google Search via Gemini needs specific parsing for search results. This is a placeholder.");
            // Example of what we might expect (needs validation):
            // const searchResults = functionCalls[0].args.results; // Fictional structure
            // return searchResults.map(r => ({ url: r.url, title: r.title }));
            return []; 
        }
        console.warn(`[DocDiscovery] Google Search via Gemini did not produce actionable function calls for ${baseUrl}.`);
        return [];
    } catch (error: any) {
        console.error(`[DocDiscovery] Error during Google Search site map for ${baseUrl}:`, error);
        return [];
    }
}

// --- Site Mapping Strategy 3: Firecrawl 'crawl' (shallow) ---
async function attemptFirecrawlShallowCrawl(
    ctx: ToolCallingContext,
    baseUrl: string
): Promise<DiscoveredPageInfo[]> {
    try {
        console.log(`[DocDiscovery] Attempt 3: Mapping site with Firecrawl 'crawl' (shallow) for ${baseUrl}`);
        const toolboxResponse = await ctx.callTool(
            '@smithery/toolbox',
            'use_tool',
            {
                target_server_id: 'firecrawl-mcp-server',
                tool_name: 'crawl',
                tool_args: { url: baseUrl, maxDepth: 1, limit: 100, scrapeOptions: { formats: ['links'] } } // Get links only
            }
        );
        if (toolboxResponse && toolboxResponse.content && toolboxResponse.content[0] && toolboxResponse.content[0].type === 'application/json') {
            const firecrawlResult = JSON.parse(toolboxResponse.content[0].content);
            // The 'crawl' tool's output structure needs to be inspected to correctly extract URLs and titles.
            // This is a placeholder based on a general idea.
            if (Array.isArray(firecrawlResult) && firecrawlResult.length > 0) {
                 const pages: DiscoveredPageInfo[] = firecrawlResult.reduce((acc: DiscoveredPageInfo[], pageData: any) => {
                    if (pageData.url) {
                        acc.push({ url: pageData.url, title: pageData.metadata?.title || pageData.url });
                    }
                    return acc;
                }, []);
                console.log(`[DocDiscovery] Firecrawl shallow crawl found ${pages.length} URLs.`);
                return pages;
            }
        }
        console.warn(`[DocDiscovery] Firecrawl shallow crawl failed or returned unexpected data for ${baseUrl}.`);
        return [];
    } catch (error: any) {
        console.error(`[DocDiscovery] Error during Firecrawl shallow crawl for ${baseUrl}:`, error);
        return [];
    }
}

export interface DiscoverDocumentStructureInput {
    project_alias: string;
    base_url: string; // e.g., https://docs.example.com/
}

export async function discoverDocumentStructure(
    ctx: ToolCallingContext,
    input: DiscoverDocumentStructureInput
): Promise<{ success: boolean; message: string; discovered_count?: number }> {
    const { project_alias, base_url } = input;
    // Project existence check via Prisma is removed. project_alias is used directly.
    // const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    // if (!project) {
    //     return { success: false, message: `Project with alias '${project_alias}' not found.` };
    // }

    let discoveredPages: DiscoveredPageInfo[] = [];
    let discoveryMethodUsed = '';

    // Attempt 1: Firecrawl 'map'
    discoveredPages = await attemptFirecrawlMap(ctx, base_url);
    discoveryMethodUsed = 'firecrawl_map';

    // Attempt 2: Google Search (if first attempt fails or yields few results)
    if (discoveredPages.length < 5) { 
        console.log("[DocDiscovery] Firecrawl 'map' yielded few results. Trying Google Search.");
        const searchPages = await attemptGoogleSearchSiteMap(base_url);
        if (searchPages.length > discoveredPages.length) {
            discoveredPages = searchPages;
            discoveryMethodUsed = 'google_search_gemini';
        }
    }

    // Attempt 3: Firecrawl shallow 'crawl' (if previous attempts fail or yield few results)
    if (discoveredPages.length < 5) {
        console.log("[DocDiscovery] Previous methods yielded few results. Trying Firecrawl shallow 'crawl'.");
        const crawlPages = await attemptFirecrawlShallowCrawl(ctx, base_url);
         if (crawlPages.length > discoveredPages.length) {
            discoveredPages = crawlPages;
            discoveryMethodUsed = 'firecrawl_shallow_crawl';
        }
    }

    if (discoveredPages.length > 0) {
        await createDocumentSourcesFromDiscovery(project_alias, discoveredPages, discoveryMethodUsed);
        return { success: true, message: `Successfully discovered ${discoveredPages.length} pages using ${discoveryMethodUsed}.`, discovered_count: discoveredPages.length };
    }

    return { success: false, message: 'All discovery attempts failed to find any pages.' };
}


// --- Scrape Strategy 1: Gemini URL Grounding (Free Tier) ---
async function scrapeWithGeminiUrl(
    url: string
): Promise<{ success: boolean; data?: { markdown: string; title?: string }; error?: string }> {
    try {
        console.log(`[DocIngestion] Attempt 1: Scraping with Gemini URL grounding for ${url}`);
        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

        const prompt = `Please act as a web scraper. Fetch the content from the provided URL and return the full, clean Markdown representation of the main content. Also, provide the document's primary title.\n\nURL: ${url}\n\nRespond in a JSON format with two keys: "title" and "markdownContent".`;

        const result = await model.generateContent({
            contents: [{ parts: [{ text: prompt }] }],
            tools: [{ googleSearchRetrieval: {} }]
        });
        const responseText = result.response.text();

        const jsonMatch = responseText.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch && jsonMatch[1]) {
            const parsed = JSON.parse(jsonMatch[1]);
            const markdown = parsed.markdownContent;
            const title = parsed.title;

            if (markdown && markdown.trim().length > 100) { // Basic check for non-trivial content
                console.log(`[DocIngestion] Gemini scrape successful for ${url}`);
                return { success: true, data: { markdown, title } };
            }
        }
        
        console.warn(`[DocIngestion] Gemini did not return valid JSON or content was trivial for ${url}.`);
        return { success: false, error: 'Gemini returned no or trivial markdown content.' };

    } catch (error: any) {
        console.error(`[DocIngestion] Gemini URL grounding failed for ${url}:`, error);
        return { success: false, error: error.message || 'Unknown Gemini error' };
    }
}

// --- Scrape Strategy 2: Firecrawl via Toolbox (Paid, Robust) ---
async function realFirecrawlScrape(
    ctx: ToolCallingContext,
    url: string
): Promise<{ success: boolean; data?: { markdown: string; title?: string }; error?: string }> {
    try {
        console.log(`[DocIngestion] Attempt 2: Scraping with Firecrawl via @smithery/toolbox for ${url}`);
        const toolboxResponse = await ctx.callTool(
            '@smithery/toolbox',
            'use_tool',
            {
                target_server_id: 'firecrawl-mcp-server',
                tool_name: 'scrape',
                tool_args: {
                    url: url,
                    formats: ['markdown'],
                    onlyMainContent: true,
                }
            }
        );

        if (toolboxResponse && toolboxResponse.content && toolboxResponse.content[0] && toolboxResponse.content[0].type === 'application/json') {
            const firecrawlResult = JSON.parse(toolboxResponse.content[0].content);
            
            if (firecrawlResult.data && firecrawlResult.data.markdown) {
                return {
                    success: true,
                    data: {
                        markdown: firecrawlResult.data.markdown,
                        title: firecrawlResult.data.title || firecrawlResult.data.metadata?.title,
                    },
                };
            } else {
                const errorMessage = firecrawlResult.error || 'Unknown firecrawl response structure';
                return { success: false, error: errorMessage };
            }
        } else {
            return { success: false, error: 'Unexpected response structure from @smithery/toolbox' };
        }
    } catch (error: any) {
        console.error(`[DocIngestion] Error calling @smithery/toolbox to scrape ${url}:`, error);
        return { success: false, error: error.message || 'Unknown error during toolbox call' };
    }
}

export interface IngestWebDocumentInput {
    project_alias: string;
    url: string;
}

// --- Main Ingestion Orchestrator ---
export async function ingestWebDocument(
    ctx: ToolCallingContext,
    input: IngestWebDocumentInput
): Promise<{ success: boolean; documentSourceId?: string; sourceUrl?: string; message?: string } | null> {
    const { project_alias, url } = input;

    // Prisma project lookup removed. project_alias is used directly.
    // const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    // if (!project) {
    //     console.error(`[DocIngestion] Project with alias '${project_alias}' not found.`);
    //     return null;
    // }

    console.log(`[DocIngestion] Starting ingestion for URL: ${url} for project ${project_alias}`);

    let scrapeResult = await scrapeWithGeminiUrl(url);

    if (!scrapeResult.success) {
        console.log(`[DocIngestion] Gemini scrape failed. Falling back to Firecrawl.`);
        scrapeResult = await realFirecrawlScrape(ctx, url);
    }

    // TODO: Add 3rd and 4th fallback attempts for scraping here in the future.

    if (!scrapeResult.success || !scrapeResult.data?.markdown) {
        console.error(`[DocIngestion] All scraping attempts failed for URL '${url}': ${scrapeResult.error || 'No markdown content'}`);
        return null;
    }

    const markdownContent = scrapeResult.data.markdown;
    const documentTitle = scrapeResult.data.title || url;

    // Content hash can still be useful for DocumentSource metadata if desired, but Weaviate handles its own IDing.
    // const contentHash = crypto.createHash('sha256').update(markdownContent).digest('hex');

    // TODO: Implement a check if this DocumentSource (URL + project_alias) already exists and has up-to-date content.
    // This might involve querying Weaviate for the DocumentSource and comparing a content hash or last updated timestamp.
    // For now, we'll create/update the DocumentSource and its chunks.

    try {
        const documentSourceData = {
            url: url,
            title: documentTitle,
            sourceType: 'web_scrape', // Or derive from context if available
            projectId: project_alias,
            lastCrawledAt: new Date(),
            status: 'INGESTED',
            // techStack: [], // Placeholder
            // rawContentHash: contentHash, // Optional: store hash for quick change detection
        };
        const sourceResult = await addDocumentSource(documentSourceData);
        const documentSourceId = sourceResult.id; // Assuming addDocumentSource returns the created object with its ID

        if (!documentSourceId) {
            console.error(`[DocIngestion] Failed to create or retrieve DocumentSource for URL '${url}'.`);
            return { success: false, sourceUrl: url, message: 'Failed to create DocumentSource.' };
        }

        const chunks = chunkMarkdownContent(markdownContent);
        if (chunks.length === 0) {
            console.warn(`[DocIngestion] No content chunks generated for URL '${url}'. DocumentSource created but no chunks added.`);
            return { success: true, documentSourceId, sourceUrl: url, message: 'DocumentSource created, but no content chunks to add.' };
        }

        let chunkBatcher = getDocumentChunkBatcher();
        let chunkCount = 0;

        for (const chunk of chunks) {
            const chunkData = {
                content: chunk.content,
                order: chunk.order,
                sourceUrl: url, // For quick reference, though linked via DocumentSource
                // fromDocumentSource: [{ beacon: `weaviate://localhost/DocumentSource/${documentSourceId}` }], // Handled by addDocumentChunk
                // metadataTags: [], // Placeholder
                // headings: [], // Placeholder, can be extracted during advanced chunking
            };
            // addDocumentChunk will handle linking to the sourceId
            chunkBatcher = chunkBatcher.withObject(await addDocumentChunk(chunkData, documentSourceId, true)); 
            chunkCount++;
        }

        if (chunkCount > 0) {
            const batchResult = await chunkBatcher.do();
            // console.log('[DocIngestion] Chunk batch import result:', batchResult);
            // Check batchResult for errors if necessary
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
