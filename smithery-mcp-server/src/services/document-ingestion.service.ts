import { PrismaClient, Document, Project } from '../generated/prisma';
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

// --- Scrape Strategy 1: Gemini URL Grounding (Free Tier) ---
async function scrapeWithGeminiUrl(
    url: string
): Promise<{ success: boolean; data?: { markdown: string; title?: string }; error?: string }> {
    try {
        console.log(`[DocIngestion] Attempt 1: Scraping with Gemini URL grounding for ${url}`);
        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

        const prompt = `Please act as a web scraper. Fetch the content from the provided URL and return the full, clean Markdown representation of the main content. Also, provide the document's primary title.\n\nURL: ${url}\n\nRespond in a JSON format with two keys: "title" and "markdownContent".`;

        const result = await model.generateContent(prompt);
        const responseText = result.response.text();

        // Attempt to parse the JSON from the response, which might be in a markdown block
        const jsonMatch = responseText.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch && jsonMatch[1]) {
            const parsed = JSON.parse(jsonMatch[1]);
            const markdown = parsed.markdownContent;
            const title = parsed.title;

            if (markdown && markdown.trim().length > 100) {
                console.log(`[DocIngestion] Gemini scrape successful for ${url}`);
                return { success: true, data: { markdown, title } };
            }
        }
        
        // Fallback if JSON is not found or content is trivial
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
): Promise<Document | null> {
    const { project_alias, url } = input;

    const project = await prisma.project.findUnique({ where: { alias: project_alias } });
    if (!project) {
        console.error(`[DocIngestion] Project with alias '${project_alias}' not found.`);
        return null;
    }

    console.log(`[DocIngestion] Starting ingestion for URL: ${url} for project ${project_alias}`);

    // --- Orchestration Logic ---
    let scrapeResult = await scrapeWithGeminiUrl(url);

    if (!scrapeResult.success) {
        console.log(`[DocIngestion] Gemini scrape failed. Falling back to Firecrawl.`);
        scrapeResult = await realFirecrawlScrape(ctx, url);
    }

    // TODO: Add 3rd and 4th fallback attempts here in the future.

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
