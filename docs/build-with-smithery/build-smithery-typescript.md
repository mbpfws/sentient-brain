Build MCP Servers

Copy page

Getting Started
Learn how to develop Model Context Protocol (MCP) servers using TypeScript with Smithery CLI.

​
Getting Started with TypeScript MCPs
The Smithery CLI provides tools for TypeScript developers to build, test, and deploy Model Context Protocol (MCP) servers.

​
Prerequisites
Node.js 18+
npm or yarn
A Smithery API key for development features
​
Quick Start
​
1. Install CLI

Copy

Ask AI
npm install -g @smithery/cli
​
2. Initialize Project

Copy

Ask AI
npm create smithery
​
3. Create Your Server
Create src/index.ts:


Copy

Ask AI
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

// Optional: Define configuration schema to require configuration at connection time
// export const configSchema = z.object({
//   debug: z.boolean().default(false).describe("Enable debug logging")
// });

export default function ({ config }: { config: z.infer<typeof configSchema> }) {
  const server = new McpServer({
    name: 'My MCP Server',
    version: '1.0.0'
  });

  // Add a tool
  server.tool(
    'hello',
    'Say hello to someone',
    {
      name: z.string().describe('Name to greet')
    },
    async ({ name }) => {
      return {
        content: [{ type: 'text', text: `Hello, ${name}!` }]
      };
    }
  );

  return server.server;
}

Show Configuration Schema

​
4. Configure Entry Point
Update your package.json to specify the entry point:


Copy

Ask AI
{
  "name": "mcp-server",
  "module": "./src/index.ts",
  "type": "module"
}
​
5. Start Development

Copy

Ask AI
npx @smithery/cli dev
This will:

Read your entry point from the module field in package.json
Start your server with hot-reload
Open the Smithery playground for you to test
​
6. Deploy
Add a smithery.yaml file to your project root:


Copy

Ask AI
runtime: typescript
Then deploy from Smithery’s UI.

​
Advanced: Build Configuration
For advanced use cases, you can customize the build process using a smithery.config.js file. This is useful for:

Marking packages as external (to avoid bundling issues)
Configuring minification, targets, and other build options
Adding custom esbuild plugins
​
Configuration File
Create smithery.config.js in your project root:


Copy

Ask AI
export default {
  esbuild: {
    // Mark problematic packages as external
    external: ["playwright-core", "puppeteer-core"],
    
    // Enable minification for production
    minify: true,
    
    // Set Node.js target version
    target: "node18"
  }
}
​
Common Use Cases
External Dependencies: If you encounter bundling issues with packages like Playwright or native modules:


Copy

Ask AI
export default {
  esbuild: {
    external: ["playwright-core", "sharp", "@grpc/grpc-js"]
  }
}
Configuration applies to both build and dev commands.