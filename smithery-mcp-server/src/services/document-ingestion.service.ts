import { PrismaClient, Document, Project, PendingDocument, PendingDocumentStatus } from '../generated/prisma';
import crypto from 'crypto';
import { genAI } from '../lib/gemini-client.js'; // Import shared Gemini client

// Interface for the context required to call other MCP tools
export interface ToolCallingContext {
    callTool: (
        targetServer: string, // e.g., '@smithery/toolbox'
        toolName: string,     // e.g., 'use_tool'
        toolArgs: any         // Arguments for the tool being called
    ) => Promise<any>; // The expected structure of the tool's response
}

const prisma = new PrismaClient();

interface DiscoveredPageInfo {
    url: string;
    title?: string;
    depth?: number;
}

/**
 * Upserts a list of discovered pages as pending documents for a project.
 *
 * For each page, creates or updates a pending document entry keyed by project ID and URL, setting its status to DISCOVERED along with metadata such as title, discovery method, and depth.
 */
async function upsertPendingDocuments(
    projectId: number,
    pages: DiscoveredPageInfo[],
    discoveryMethod: string
): Promise<void> {
    const operations = pages.map(page => 
        prisma.pendingDocument.upsert({
            where: { project_id_url: { project_id: projectId, url: page.url } },
            update: {
                title: page.title || page.url,
                status: PendingDocumentStatus.DISCOVERED,
                discovery_method: discoveryMethod,
                depth: page.depth,
                updated_at: new Date(),
            },
            create: {
                project_id: projectId,
                url: page.url,
                title: page.title || page.url,
                status: PendingDocumentStatus.DISCOVERED,
                discovery_method: discoveryMethod,
                depth: page.depth,
            }
        })
    );
    await prisma.$transaction(operations);
    console.log(`[DocDiscovery] Upserted ${pages.length} pending documents using ${discoveryMethod}.`);
}

/**
 * Attempts to discover documentation pages under a base URL using the Firecrawl 'map' tool.
 *
 * Calls the Firecrawl 'map' tool via the provided context to retrieve a list of URLs (and optionally titles) from the target site. Returns an array of discovered page information, using the URL as the title if no title is provided. Returns an empty array if the tool fails or returns unexpected data.
 *
 * @param baseUrl - The base URL of the site to map for documentation pages
 * @returns An array of discovered page information with URLs and titles
 */
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

/**
 * Attempts to discover documentation pages under a given base URL using Google Search via the Gemini generative model.
 *
 * Sends a prompt to Gemini to find unique documentation pages, focusing on HTML content, and expects structured results with URLs and titles. Currently returns an empty array as parsing of Gemini's function call output is not implemented.
 *
 * @param baseUrl - The base URL to search for documentation pages under
 * @returns An array of discovered page information, or an empty array if no actionable results are found
 */
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

/**
 * Attempts to discover documentation pages by performing a shallow crawl of the given base URL using the Firecrawl 'crawl' tool.
 *
 * Returns an array of discovered page information, including URLs and titles when available. If the crawl fails or returns unexpected data, returns an empty array.
 */
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

/**
 * Discovers documentation pages under a base URL using multiple strategies and records them as pending documents for a project.
 *
 * Attempts discovery via Firecrawl's 'map' tool, Google Search via Gemini, and Firecrawl's shallow 'crawl', selecting the method that yields the most results. Upserts discovered pages into the project's pending documents. Returns the outcome and the number of pages discovered.
 *
 * @returns An object indicating success, a message, and the count of discovered pages if successful.
 */
export async function discoverDocumentStructure(
    ctx: ToolCallingContext,
    input: DiscoverDocumentStructureInput
): Promise<{ success: boolean; message: string; discovered_count?: number }> {
    const { project_alias, base_url } = input;
    const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    if (!project) {
        return { success: false, message: `Project with alias '${project_alias}' not found.` };
    }

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
        await upsertPendingDocuments(project.id, discoveredPages, discoveryMethodUsed);
        return { success: true, message: `Successfully discovered ${discoveredPages.length} pages using ${discoveryMethodUsed}.`, discovered_count: discoveredPages.length };
    }

    return { success: false, message: 'All discovery attempts failed to find any pages.' };
}


/**
 * Attempts to scrape the main content and title from a web page using Gemini AI with Google Search retrieval.
 *
 * Fetches the specified URL, prompting Gemini to return the primary title and a Markdown representation of the main content in JSON format. Validates that the returned Markdown content is non-trivial.
 *
 * @param url - The URL of the web page to scrape.
 * @returns An object indicating success and, if successful, the Markdown content and title; otherwise, an error message.
 */
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

/**
 * Scrapes the main content of a web page as Markdown using the Firecrawl tool via the toolbox service.
 *
 * Attempts to extract the page's Markdown content and title from the Firecrawl response. Returns an error message if scraping fails or the response structure is unexpected.
 *
 * @param url - The URL of the web page to scrape
 * @returns An object indicating success, with the scraped Markdown and optional title if successful, or an error message if not
 */
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

/**
 * Ingests a web document into the project database by scraping its content and storing it as a Markdown document.
 *
 * Attempts to scrape the specified URL using multiple strategies (Gemini, then Firecrawl). If successful, deduplicates by content hash and creates a new document record associated with the given project. Returns the created or existing document, or null if ingestion fails.
 *
 * @param input - Contains the project alias and the URL of the web document to ingest
 * @returns The ingested Document entity, or null if ingestion was unsuccessful
 */
export async function ingestWebDocument(
    ctx: ToolCallingContext,
    input: IngestWebDocumentInput
): Promise<Document | null> {
    const { project_alias, url } = input;

    const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    if (!project) {
        console.error(`[DocIngestion] Project with alias '${project_alias}' not found.`);
        return null;
    }

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

    const contentHash = crypto.createHash('sha256').update(markdownContent).digest('hex');

    const existingDocument = await prisma.document.findUnique({
        where: { content_hash: contentHash },
    });

    if (existingDocument) {
        console.log(`[DocIngestion] Document with URL '${url}' and hash '${contentHash}' already exists (ID: ${existingDocument.id}). Skipping.`);
        return existingDocument;
    }

    try {
        const newDocument = await prisma.document.create({
            data: {
                project_id: project.id,
                source_url: url,
                title: documentTitle,
                markdown_content: markdownContent,
                content_hash: contentHash,
            },
        });
        console.log(`[DocIngestion] Successfully ingested document '${newDocument.title}' (ID: ${newDocument.id}) from URL '${url}'.`);
        
        return newDocument;
    } catch (error) {
        console.error(`[DocIngestion] Error saving document from URL '${url}' to database:`, error);
        return null;
    }
}
