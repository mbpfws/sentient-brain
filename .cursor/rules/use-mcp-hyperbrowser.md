---
trigger: model_decision
description: It provides various tools to scrape, extract structured data, and crawl webpages
---

Tools
scrape_webpage - Extract formatted (markdown, screenshot etc) content from any webpage
crawl_webpages - Navigate through multiple linked pages and extract LLM-friendly formatted content
extract_structured_data - Convert messy HTML into structured JSON
search_with_bing - Query the web and get results with Bing search
browser_use_agent - Fast, lightweight browser automation with the Browser Use agent
openai_computer_use_agent - General-purpose automation using OpenAI’s CUA model
claude_computer_use_agent - Complex browser tasks using Claude computer use
create_profile - Creates a new persistent Hyperbrowser profile.
delete_profile - Deletes an existing persistent Hyperbrowser profile.
list_profiles - Lists existing persistent Hyperbrowser profiles.
Installing via Smithery
To install Hyperbrowser MCP Server for Claude Desktop automatically via Smithery:

npx -y @smithery/cli install @hyperbrowserai/mcp --client claude
