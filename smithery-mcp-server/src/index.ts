import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { indexCodebase } from './services/code-indexing.service.js';
import { fileWatcherService } from './services/file-watcher.service.js';
import { Project } from './generated/prisma/index.js';
import { createGuide, findGuides, createImplementation, GuideCreateInput, ImplementationCreateInput } from './services/guides.service.js';
import { ingestWebDocument, IngestWebDocumentInput, ToolCallingContext } from './services/document-ingestion.service.js';

// Define configuration schema to require a Gemini API key
export const configSchema = z.object({
  GEMINI_API_KEY: z.string().describe("Google Gemini API Key")
});

export default function ({ config }: { config: z.infer<typeof configSchema> }) {
  // Set the API key for the Gemini client
  process.env.GEMINI_API_KEY = config.GEMINI_API_KEY;

  const server = new McpServer({
    name: 'Sentient Brain - MCP Server',
    version: '0.2.0-ts'
  });

  // Start the file watcher service on server initialization
  fileWatcherService.start().catch(console.error);

  // --- Code Indexing Tools ---

  server.tool(
    'index_codebase',
    'Scans and indexes a codebase directory for a given project.',
    {
      project_alias: z.string().describe('A unique alias for the project (e.g., `my-app`).'),
      root_path: z.string().describe('The absolute file path to the root of the codebase.')
    },
    async ({ project_alias, root_path }) => {
      // Run indexing in the background and then start watching the project
      indexCodebase(project_alias, root_path)
        .then((newProject: Project | null) => {
          if (newProject) {
            fileWatcherService.watchProject(newProject);
          }
        })
        .catch(console.error);

      return {
        content: [
          {
            type: 'text',
            text: `Indexing started for project '${project_alias}' at ${root_path}. Check server logs for progress.`
          }
        ]
      };
    }
  );





  // --- Guides & Implementation Memory Tools ---

  server.tool(
    'add_guide',
    'Adds a new architectural or implementation guide to the memory.',
    {
      project_alias: z.string().describe('The alias of the project this guide belongs to.'),
      title: z.string().describe('The title of the guide.'),
      description: z.string().describe('A detailed description of the guide/pattern.'),
    },
    async (input: GuideCreateInput) => {
      const guide = await createGuide(input);
      if (!guide) {
        return { content: [{ type: 'text', text: `Failed to create guide. Project '${input.project_alias}' not found.` }] };
      }
      return { content: [{ type: 'text', text: `Successfully created guide '${guide.title}' with ID ${guide.id}.` }] };
    }
  );

  server.tool(
    'find_guides',
    'Searches for relevant guides based on a query.',
    {
      project_alias: z.string().describe('The alias of the project to search within.'),
      query: z.string().describe('The search query to find relevant guides.'),
    },
    async ({ project_alias, query }) => {
      const guides = await findGuides(project_alias, query);
      return {
        content: [
          {
            type: 'application/json',
            content: JSON.stringify(guides, null, 2),
          },
        ],
      };
    }
  );

  server.tool(
    'add_implementation',
    'Adds a concrete code implementation example to a guide.',
    {
      guide_id: z.number().int().describe('The ID of the guide this implementation belongs to.'),
      title: z.string().describe('The title of the implementation example.'),
      code_snippet: z.string().describe('The code snippet demonstrating the implementation.'),
      description: z.string().optional().describe('An optional description for the code snippet.'),
    },
    async (input: ImplementationCreateInput) => {
      const implementation = await createImplementation(input);
      return { content: [{ type: 'text', text: `Successfully added implementation '${implementation.title}' to guide ${input.guide_id}.` }] };
    }
  );

  // --- Document Ingestion Tools ---

  server.tool(
    'ingest_web_document',
    'Ingests a document from a given URL, converts it to Markdown, and stores it.',
    {
      project_alias: z.string().describe('The alias of the project this document belongs to.'),
      url: z.string().url().describe('The URL of the web page to ingest.'),
    },
    async (input: IngestWebDocumentInput) => {
      const toolCallingCtx: ToolCallingContext = {
        callTool: server.callTool.bind(server) // Pass the server's callTool method
      };
      const document = await ingestWebDocument(toolCallingCtx, input);
      if (!document) {
        return { content: [{ type: 'text', text: `Failed to ingest document from URL '${input.url}'. Check server logs.` }] };
      }
      // Check if the document was newly created or if an existing one was returned
      // Prisma's default behavior for create doesn't easily distinguish this without an extra query or specific logic.
      // For now, we'll assume the console logs in the service are sufficient to indicate new vs. existing.
      // A more robust way might involve the service returning a flag.
      return { content: [{ type: 'text', text: `Processing complete for document from URL '${input.url}'. ID: ${document.id}, Title: '${document.title}'. Check server logs for ingestion details.` }] };
    }
  );

  return server.server;
}
