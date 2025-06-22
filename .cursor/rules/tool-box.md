---
trigger: model_decision
description: When a capability is out of your reach or in need of MCP server for task completion.
---

Toolbox

@smithery/toolbox
Homepage
GitHub
https://server.smithery.ai/@smithery/toolbox/...
Copy

Overview

Tools

API
Toolbox dynamically routes to all MCPs in the Smithery registry based on your agent's need. When an MCP requires configuration, our tool will prompt the user to configure their tool with a callback link.

Recommended use in Claude Desktop:
This MCP provides a prompt that encourages Claude Desktop to use Smithery MCPs. You can include the prompt by clicking the "Attach from MCP" icon.

Tools
search_servers
Search for Model Context Protocol (MCP) servers in the Smithery MCP registry. MCPs are tools that allow you to interact with other services to perform tasks. This tool allows you to find MCP servers by name, description, or other attributes. Each server on the registry comes with a set of available tools, which can be used once added.

use_tool
Execute a specific tool call on an MCP server.