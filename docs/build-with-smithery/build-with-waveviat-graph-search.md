

This plan is oriented around **Weaviate** as the core data layer and is designed for deployment on **Smithery**, with specific integration points for IDEs like **Cursor** and **Windsurf**. It also incorporates the technical stack required for the hackathon, including **Vultr**, **Groq**, and **Llama 3**.

Here is the production-ready build plan for your Sentient Brain MCP Server.

***

# Production Build Plan: Sentient Brain MCP Server

This document outlines a phased, production-ready development plan for the Sentient Brain MCP Server. The architecture is designed to be robust, scalable, and compliant with the deployment requirements of Smithery.ai, Vultr, and the specified hackathon technologies.

## Phase 1: Foundational Architecture & Environment Setup

This phase establishes the core technical decisions, the full technology stack, and the initial development environment.

### 1.1. Core Architectural Decision: A Weaviate-Centric Approach

While a dual-database system (Graph + Vector) is powerful, a more streamlined and modern approach is to leverage a single, advanced vector database that can handle the core requirements. For this project, we will build a **Weaviate-centric architecture**.

*   **Why Weaviate?** Weaviate is an open-source vector database that stores data as "objects" which can be linked together using **cross-references**. This feature allows us to create a knowledge graph *within* Weaviate, modeling the hierarchical and relational nature of documentation without the operational overhead of managing a separate graph database.[1, 2, 3]
*   **Key Advantages:**
    *   **Simplified Stack:** Manages one database system instead of two, reducing complexity and cost.[4]
    *   **Unified Search:** Weaviate excels at **hybrid search**, combining vector (semantic) search with traditional keyword (BM25) filtering in a single, efficient query.[5, 6, 7] This is critical for accurately querying technical documentation, which contains both conceptual language and specific keywords (like function names or error codes).
    *   **AI-Native:** It is designed for AI-first applications, with features like generative search (RAG) and integrations with modern LLM frameworks.[8, 9]

### 1.2. Full Technology Stack

| Component | Technology | Rationale & Integration |
| :--- | :--- | :--- |
| **Server Language** | **TypeScript** | Aligns with your existing project files (`index.ts`, `tsconfig.json`) and the robust `@modelcontextprotocol/sdk` for building MCP servers.[10, 10, 10] |
| **Vector & Graph DB** | **Weaviate** | Serves as the single source of truth for both vectorized content and relational metadata via its cross-referencing capabilities.[5, 2, 11] |
| **Primary LLM (Synthesis)** | **Google Gemini 1.5 Flash** | Used for complex, high-quality tasks like entity/relationship extraction and deep content synthesis, leveraging its large context window.[12, 13, 14] |
| **Secondary LLM (Speed)** | **Llama 3 via Groq API** | Fulfills the hackathon requirement. Used for high-speed, low-latency tasks like initial intent recognition from user prompts or generating quick summaries.[15, 16, 17] |
| **Agent Orchestration** | **LangGraph** | Its stateful, graph-based model is ideal for managing the complex, cyclical workflows you described, especially the client-server feedback loops.[18, 19] |
| **Deployment Platform** | **Smithery & Vultr** | The server will be packaged as a Docker container, registered on Vultr Container Registry, and deployed to Vultr Kubernetes Engine (VKE), while being managed and exposed via the Smithery platform.[20, 21, 22, 23, 24] |

### 1.3. Environment Setup & Configuration

1.  **Project Initialization:** Your existing TypeScript project structure is a solid starting point. Ensure `package.json` specifies `"type": "module"` and the entry point is `"module": "./src/index.ts"`.[10, 10]
2.  **Install Dependencies:**
    ```bash
    npm install @modelcontextprotocol/sdk zod weaviate-ts-client @google/generai groq-sdk chokidar
    npm install -D @smithery/cli @types/node typescript tsx prisma
    ```
3.  **API Keys & Environment:** Create a `.env` file in the project root to store your API keys.[10, 10]
    ```
    #.env
    GEMINI_API_KEY="your-google-gemini-api-key"
    GROQ_API_KEY="your-groq-api-key"
    WEAVIATE_URL="http://localhost:8080" # Or your cloud endpoint
    WEAVIATE_API_KEY="your-weaviate-api-key" # If using Weaviate Cloud Service
    ```
4.  **Local Weaviate Instance:** For local development, use Docker Compose to run Weaviate with a text vectorization module (e.g., `text2vec-openai` or a HuggingFace model).
5.  **Smithery CLI:** Install and configure the Smithery CLI for local development and testing: `npm install -g @smithery/cli`.[10]

## Phase 2: Data Modeling & Ingestion Pipeline

This phase focuses on structuring your data within Weaviate and building the automated pipeline to populate it.

### 2.1. Weaviate Schema & Data Modeling

Instead of a separate relational database, we will model all data within Weaviate collections. We'll use **Zod** (the TypeScript equivalent of Pydantic) to define and validate our data structures before they are sent to Weaviate.[25]

**Weaviate Collections:**

1.  **`Project` Collection:**
    *   **Properties:** `alias` (string), `rootPath` (string), `description` (text).
    *   **Purpose:** Stores metadata about each indexed project.

2.  **`Document` Collection:**
    *   **Properties:** `sourceUrl` (string), `title` (text), `contentHash` (string), `markdownContent` (text).
    *   **Cross-Reference:** `fromProject` (points to `Project` collection).
    *   **Purpose:** Stores the full, scraped content of a documentation page or a local file.

3.  **`Chunk` Collection:**
    *   **Properties:** `chunkText` (text), `order` (number), `chunkType` (e.g., "code", "prose", "heading").
    *   **Vectorization:** The `chunkText` property will be vectorized.
    *   **Cross-Reference:** `fromDocument` (points to `Document` collection).
    *   **Purpose:** This is the core collection for semantic search. Each object represents a semantically coherent piece of a larger document.

This structure allows us to perform powerful queries. For example, we can find relevant `Chunk`s via vector search, then traverse the `fromDocument` cross-reference to retrieve the full context of the original document.[2, 3]

### 2.2. Advanced Chunking Strategy

A naive chunking strategy will fail for technical documentation. We will implement a multi-stage, content-aware chunking pipeline.

*   **For Technical Documentation (HTML/Markdown):**
    1.  **Structural Splitting:** Use a library like `langchain/textsplitters`'s `HTMLHeaderTextSplitter` to first split the document by headers (`<h1>`, `<h2>`, etc.). This preserves the document's logical structure.[26, 27]
    2.  **Recursive Splitting:** For each structural section, use a `RecursiveCharacterTextSplitter` to break it down further into smaller, coherent chunks based on paragraphs and sentences.[28, 27, 29]

*   **For Source Code:**
    1.  **Syntax-Aware Chunking (cAST):** The most effective method is **Chunking via Abstract Syntax Trees (cAST)**. This involves parsing the code into an AST and then splitting the tree into chunks that correspond to logical units like functions, classes, or methods. This ensures that code blocks are never broken apart arbitrarily.[30] Libraries are available in various languages to generate ASTs.
    2.  **Textification:** Before embedding code chunks, convert them into a more natural language-like description. For example, `def getUser(id: int):` becomes "a function named 'getUser' that accepts an integer parameter 'id'". This helps general-purpose embedding models understand the code's semantic purpose.[31]

### 2.3. The Automated Ingestion Workflow

This workflow will be implemented as the `ingest_web_document` tool in your MCP server, mirroring the logic in your `document-ingestion.service.ts` file.[10]

1.  **Discovery:** Use a multi-pronged approach to discover all pages in a documentation site, as outlined in your `discoverDocumentStructure` tool. This includes using tools like Firecrawl or Gemini's Google Search grounding.[10]
2.  **Scraping:** Use **Playwright** to reliably scrape content from modern, JavaScript-heavy websites. It's crucial to implement **ethical scraping practices**: respect `robots.txt`, set a descriptive `User-Agent`, throttle requests, and implement a retry/backoff mechanism for transient errors.[32, 33, 34, 35]
3.  **Chunking:** Apply the advanced chunking strategy from section 2.2 to the scraped content.
4.  **LLM-Powered Enrichment (Gemini 1.5 Flash):** For each chunk, use Gemini to:
    *   **Extract Entities:** Identify key technical concepts, function names, library names, etc.
    *   **Extract Relationships:** Identify how these entities relate (e.g., `functionA` USES `libraryB`).
5.  **Populate Weaviate:**
    *   Create a `Document` object for the scraped page.
    *   For each chunk, create a `Chunk` object in Weaviate. The vector embedding will be generated automatically by Weaviate's configured module.
    *   Create cross-references to link each `Chunk` to its parent `Document`.
    *   (Advanced) Use the extracted entities and relationships to create additional cross-references between `Chunk` objects, building a richer knowledge graph.

## Phase 3: Agentic Logic & Retrieval Pipeline

This phase defines the "brain" of the server, handling incoming queries and orchestrating the response generation.

### 3.1. Agent Orchestration with LangGraph

The server's core logic will be a state machine built with LangGraph. This is essential for managing the multi-step, potentially cyclical nature of agent interactions (e.g., retrieval -> synthesis -> client feedback -> re-retrieval).[18, 19]

**Key States in the Graph:**
*   `AWAITING_QUERY`
*   `RETRIEVING_CONTEXT`
*   `SYNTHESIZING_ANSWER`
*   `AWAITING_FEEDBACK`
*   `INITIATING_RE_INGESTION`

### 3.2. Hybrid Retrieval from Weaviate

The retrieval tool will leverage Weaviate's full search capabilities:

1.  **Intent Recognition (Groq/Llama 3):** When a user prompt arrives, a quick call to the low-latency Groq API can classify the user's intent (e.g., "code generation," "conceptual question," "specific lookup").[36, 37] This helps tailor the retrieval strategy.
2.  **Hybrid Search:** Execute a hybrid search query in Weaviate. This combines:
    *   **Vector Search:** To find semantically similar chunks based on the query's meaning.
    *   **Keyword (BM25) Search:** To find exact matches for function names, variable names, or error codes.
    *   The `alpha` parameter in Weaviate's hybrid search allows you to balance the weight between these two search types.[6, 7]
3.  **Contextual Expansion:** After retrieving the top N chunks, use Weaviate's GraphQL API to traverse the `fromDocument` cross-references and fetch the full parent documents. This provides the LLM with the rich context it needs to generate a high-quality response.[38, 39]

### 3.3. The Client-Server Feedback Loop

This is a critical feature for a self-improving system.

1.  **Client-Side Trigger:** The IDE agent (e.g., in Cursor) determines that the server's response was insufficient or led to an error.
2.  **Structured Feedback:** The client agent calls a dedicated `process_feedback` tool on the MCP server, providing the original query, the flawed response, and a description of the knowledge gap.
3.  **Server-Side Action (LangGraph):** The LangGraph orchestrator receives this feedback and transitions to a `RE_INGESTION` state. It triggers a targeted re-scrape of the relevant documentation URL, updates the `Document` and `Chunk` objects in Weaviate, and then re-runs the original query to provide an updated answer.[40, 41]

## Phase 4: Smithery Server & IDE Integration

This phase focuses on exposing the server's capabilities through the Model Context Protocol (MCP) and integrating it with target IDEs.

### 4.1. MCP Server Implementation (`index.ts`)

Structure your main server file to define the tools that agents can call. This aligns with your existing `index.ts` file.[10]

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
//... import your service functions

export const configSchema = z.object({
  GEMINI_API_KEY: z.string().describe("Google Gemini API Key"),
  GROQ_API_KEY: z.string().describe("Groq API Key"),
  WEAVIATE_URL: z.string().url().describe("URL for Weaviate instance"),
  //... other configs
});

export default function ({ config }: { config: z.infer<typeof configSchema> }) {
  // Initialize clients (Weaviate, Gemini, Groq) with config
  
  const server = new McpServer({
    name: 'Sentient Brain',
    version: '1.0.0-weaviate'
  });

  // Define the core tool for querying the knowledge base
  server.tool(
    'query_knowledge_base',
    'Searches the indexed documentation and codebase to answer a technical question.',
    { query: z.string().describe('The user\'s question or coding task.') },
    async ({ query }) => {
      // This is where you trigger your LangGraph retrieval pipeline
      const response = await runRetrievalPipeline(query); 
      return { content: };
    }
  );

  // Define the tool for the feedback loop
  server.tool(
    'process_feedback',
    'Reports a knowledge gap to the server for self-correction.',
    { /*... schema for feedback object... */ },
    async (feedback) => {
      // Trigger the feedback workflow in LangGraph
      const result = await processKnowledgeGap(feedback);
      return { content: [{ type: 'text', text: result.message }] };
    }
  );
  
  //... other tools like discover_document_structure, ingest_web_document
  
  return server.server;
}
```

### 4.2. Smithery Configuration (`smithery.yaml`)

Create a `smithery.yaml` file in your project root to define how Smithery should run and deploy your server.[10, 10, 10]

```yaml
runtime: typescript
startCommand:
  type: stdio
  configSchema:
    # Reference the exported configSchema from your index.ts
    # Smithery CLI will handle this automatically if exported correctly.
  commandFunction: |
    (config) => ({
      command: 'npx',
      args: ['tsx', './src/index.ts'],
      env: {
        GEMINI_API_KEY: config.GEMINI_API_KEY,
        GROQ_API_KEY: config.GROQ_API_KEY,
        WEAVIATE_URL: config.WEAVIATE_URL,
        WEAVIATE_API_KEY: config.WEAVIATE_API_KEY
      }
    })
# Add build configuration for deployment
build:
  dockerBuildPath: "."
  dockerfilePath: "Dockerfile"
```

### 4.3. IDE Integration (Cursor & Windsurf)

To make your server available within Cursor and Windsurf, users will configure it in their IDE settings. Your documentation should provide these snippets.

*   **For Cursor (`.cursor/config.json`):**
    ```json
    {
      "mcpServers": {
        "sentient-brain": {
          "url": "https://your-smithery-deployment-url.smithery.ai",
          "config": {
            "GEMINI_API_KEY": "...",
            "GROQ_API_KEY": "..."
          }
        }
      }
    }
    ```
*   **For Windsurf:** Windsurf's agent, Cascade, can be enhanced by connecting to MCP servers. Users can add your server through the UI or configuration files, allowing Cascade to use the `@` mention to reference your server's tools.[42, 43, 44, 45]

## Phase 5: Hackathon Deployment & Optional Tech

This phase focuses on meeting the specific deployment and technology requirements of the hackathon.

### 5.1. Vultr Deployment Plan

1.  **Containerize the Application:** Create a `Dockerfile` for your TypeScript MCP server.
    ```dockerfile
    # Use an official Node.js runtime as a parent image
    FROM node:20-slim

    WORKDIR /usr/src/app

    # Install dependencies
    COPY package*.json./
    RUN npm install --production

    # Bundle app source
    COPY..

    # Your app binds to port 8080
    EXPOSE 8080
    CMD [ "npx", "tsx", "./src/index.ts" ]
    ```
2.  **Use Vultr Container Registry:**
    *   Build your Docker image: `docker build -t my-mcp-server:latest.`.[24]
    *   Tag the image for the Vultr registry: `docker tag my-mcp-server:latest <your-vcr-url>/my-mcp-server:latest`.[46]
    *   Log in and push the image to your Vultr Container Registry.[23, 46]
3.  **Deploy on Vultr Kubernetes Engine (VKE):**
    *   Create a VKE cluster in the Vultr dashboard.[21, 47]
    *   Create a Kubernetes deployment YAML file that pulls your image from the Vultr Container Registry and exposes it.

### 5.2. Hackathon Tech Integration: Coral Protocol

To showcase an advanced multi-agent system, we will use **Coral Protocol** as the communication layer between the client-side IDE agent and the server-side MCP agent.

*   **Architecture:** Instead of direct HTTP calls, agents communicate through a shared **Coral Thread**.
*   **Workflow:**
    1.  The client-side agent (in Cursor/Windsurf) is "Coralized" and registers with a Coral Server.[48]
    2.  When the user makes a request, the client agent sends a structured message to a specific thread, mentioning the `@SentientBrain` agent.[49]
    3.  Your MCP server also runs as a Coralized agent, listening for mentions in that thread.
    4.  Upon receiving a mention, it triggers its internal LangGraph pipeline and posts the synthesized result back to the thread.
*   **Benefit:** This demonstrates a sophisticated, decentralized, and scalable multi-agent architecture, a key judging criterion for the hackathon.[50, 51]

## Phase 6: Resilience & Maintenance

A production-ready system must be robust and maintainable.

*   **Resilience Patterns:** Implement resilience for all external network calls (Weaviate, LLM APIs, web scraping).
    *   **Retry:** For transient errors like network timeouts, retry the request 2-3 times with exponential backoff.
    *   **Circuit Breaker:** If a service (like an external documentation site) is consistently failing, temporarily stop sending requests to it to avoid cascading failures.
    *   **Fallback:** If scraping a primary URL fails, have a fallback strategy, such as performing a web search for the content or notifying the user that the source is unavailable.[52]
*   **Testing:**
    *   **Unit Tests:** Test individual functions (e.g., chunking logic, data transformation).
    *   **Integration Tests:** Test the full retrieval pipeline from query to synthesized response.
    *   **E2E Tests:** Use the Smithery playground or a test client to simulate an IDE agent calling the deployed MCP server.
*   **Monitoring:**
    *   **Logging:** Implement structured logging to track request flows, tool calls, errors, and performance metrics (e.g., query latency, token usage).
    *   **Health Checks:** Create a simple HTTP endpoint (e.g., `/health`) that checks the status of database connections and external API availability.