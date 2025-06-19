import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { indexCodebase } from './services/code-indexing.service.js';
import { fileWatcherService } from './services/file-watcher.service.js';
import { Project } from './generated/prisma/index.js';
import { createGuide, findGuides, createImplementation, GuideCreateInput, ImplementationCreateInput } from './services/guides.service.js';

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

  return server.server;
}
