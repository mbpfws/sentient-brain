import { PrismaClient, Document, Project } from '../generated/prisma';
import crypto from 'crypto';

// Interface for the context required to call other MCP tools
export interface ToolCallingContext {
    callTool: (
        targetServer: string, // e.g., '@smithery/toolbox'
        toolName: string,     // e.g., 'use_tool'
        toolArgs: any         // Arguments for the tool being called
    ) => Promise<any>; // The expected structure of the tool's response
}

const prisma = new PrismaClient();

async function realFirecrawlScrape(
    ctx: ToolCallingContext,
    url: string
): Promise<{ success: boolean; data?: { markdown: string; title?: string }; error?: string }> {
    try {
        console.log(`[DocIngestion] Attempting to scrape URL via @smithery/toolbox: ${url}`);
        const toolboxResponse = await ctx.callTool(
            '@smithery/toolbox', // Target the Smithery Toolbox server
            'use_tool',          // The tool on the Toolbox to execute other MCP tool calls
            {
                // Arguments for 'use_tool'
                target_server_id: 'firecrawl-mcp-server', // The actual server we want to use
                tool_name: 'scrape',                      // The tool on firecrawl-mcp-server
                tool_args: {                              // Arguments for firecrawl's 'scrape' tool
                    url: url,
                    formats: ['markdown'],
                    onlyMainContent: true, // Good default to get cleaner content
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
                const errorMessage = firecrawlResult.error || (firecrawlResult.data ? 'No markdown content in firecrawl response' : 'Unknown firecrawl response structure');
                console.error(`[DocIngestion] Firecrawl scrape via Toolbox failed for ${url}: ${errorMessage}`, firecrawlResult);
                return { success: false, error: errorMessage };
            }
        } else {
            console.error(`[DocIngestion] Unexpected response structure from @smithery/toolbox for ${url}:`, toolboxResponse);
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

// Updated to accept ToolCallingContext
export async function ingestWebDocument(
    ctx: ToolCallingContext, // Added context parameter
    input: IngestWebDocumentInput
): Promise<Document | null> {
    const { project_alias, url } = input;

    const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    if (!project) {
        console.error(`[DocIngestion] Project with alias '${project_alias}' not found.`);
        return null;
    }

    console.log(`[DocIngestion] Starting ingestion for URL: ${url} for project ${project_alias}`);

    const scrapeResult = await realFirecrawlScrape(ctx, url); // Pass context

    if (!scrapeResult.success || !scrapeResult.data?.markdown) {
        console.error(`[DocIngestion] Failed to process URL '${url}': ${scrapeResult.error || 'No markdown content'}`);
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
