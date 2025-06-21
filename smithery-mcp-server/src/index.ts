import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { ingestWebDocument, IngestWebDocumentInput, ToolCallingContext, discoverDocumentStructure, DiscoverDocumentStructureInput } from './services/document-ingestion.service.js';
import { initializeSchema } from './lib/weaviate.service.js';

// Define configuration schema to require a Gemini API key
export const configSchema = z.object({
  GEMINI_API_KEY: z.string().describe("Google Gemini API Key")
});

export default function ({ config }: { config: z.infer<typeof configSchema> }) {
  // Set the API key for the Gemini client
  process.env.GEMINI_API_KEY = config.GEMINI_API_KEY;

  // Initialize Weaviate schema
  initializeSchema().then(() => {
    console.log('Weaviate schema initialization process completed.');
  }).catch(error => {
    console.error('Failed to initialize Weaviate schema:', error);
    // Depending on severity, you might want to prevent server startup or handle this error more gracefully.
  });

  const server = new McpServer({
    name: 'Sentient Brain - MCP Server',
    version: '0.2.0-ts'
  });



  // --- Document Ingestion Tools ---

  server.tool(
    'ingest_web_document',
  //   'Ingests a document from a given URL, converts it to Markdown, and stores it.',
  //   {
  //     project_alias: z.string().describe('The alias of the project this document belongs to.'),
  //     url: z.string().url().describe('The URL of the web page to ingest.'),
  //   },
  //   async (input: IngestWebDocumentInput) => {
  //     const toolCallingCtx: ToolCallingContext = {
  //       server: server // Pass the entire server instance
  //     };
  //     const result = await ingestWebDocument(toolCallingCtx, input);
  //     if (!result.success) {
  //       return { content: [{ type: 'text', text: `Failed to ingest document from URL '${input.url}'. Reason: ${result.message}` }] };
  //     }
  //     return { content: [{ type: 'text', text: `Successfully processed document from URL '${input.url}'. Source ID: ${result.documentSourceId}. Details: ${result.message}` }] };
  //   }
  );

  server.tool(
    'discover_document_structure',
  //   'Discovers all unique page URLs and titles under a base documentation URL for a project.',
  //   {
  //     project_alias: z.string().describe('The alias of the project for which to discover documents.'),
  //     base_url: z.string().url().describe('The base URL of the documentation site to scan (e.g., https://docs.example.com/).')
  //   },
  //   async (input: DiscoverDocumentStructureInput) => {
  //     const toolCallingCtx: ToolCallingContext = {
  //       server: server // Pass the entire server instance
  //     };
  //     const result = await discoverDocumentStructure(toolCallingCtx, input);
  //     if (!result.success) {
  //       return { content: [{ type: 'text', text: `Failed to discover document structure for '${input.base_url}': ${result.message}` }] };
  //     }
  //     return { content: [{ type: 'text', text: `Successfully initiated discovery for '${input.base_url}'. Found ${result.discovered_count} pages. Check server logs for details.` }] };
  //   }
  );

  return server.server;
}
