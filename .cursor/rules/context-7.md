---
trigger: model_decision
description: when working with external, third party dependencies
---

# Context7

@upstash/context7-mcp

[Homepage](https://github.com/upstash/context7#readme)[GitHub](https://github.com/upstash/context7-mcp)

`https://server.smithery.ai/@upstash/context7-mcp/...`

Copy

[Overview](https://smithery.ai/server/@upstash/context7-mcp)[Tools](https://smithery.ai/server/@upstash/context7-mcp/tools)[API](https://smithery.ai/server/@upstash/context7-mcp/api)

Fetch up-to-date, version-specific documentation and code examples directly into your prompts. Enhance your coding experience by eliminating outdated information and hallucinated APIs. Simply add `use context7` to your questions for accurate and relevant answers.

## Tools

[

### resolve-library-id

Resolves a package/product name to a Context7-compatible library ID and returns a list of matching libraries. You MUST call this function before 'get-library-docs' to obtain a valid Context7-compatible library ID. Selection Process: 1. Analyze the query to understand what library/package the user is looking for 2. Return the most relevant match based on: - Name similarity to the query (exact matches prioritized) - Description relevance to the query's intent - Documentation coverage (prioritize libraries with higher Code Snippet counts) - Trust score (consider libraries with scores of 7-10 more authoritative) Response Format: - Return the selected library ID in a clearly marked section - Provide a brief explanation for why this library was chosen - If multiple good matches exist, acknowledge this but proceed with the most relevant one - If no good matches exist, clearly state this and suggest query refinements For ambiguous queries, request clarification before proceeding with a best-guess match.



](https://smithery.ai/server/%40upstash%2Fcontext7-mcp/tools)[

### get-library-docs

Fetches up-to-date documentation for a library. You must call 'resolve-library-id' first to obtain the exact Context7-compatible library ID required to use this tool.



](https://smithery.ai/server/%40upstash%2Fcontext7-mcp/tools)