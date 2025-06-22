---
trigger: model_decision
description: When asked with image generation or instead of using placeholder photos/images use prompting technique to call MCP Server https://server.smithery.ai/@falahgs/flux-imagegen-mcp-server/mcp?api_key=4e8105a9-20be-46b9-b8d4-8fc9265b924d
---

- First prepare prompt (describe clearly styles, dimension, file types, context, purposes, any lighting, concepts, camera angles etc, the objects, movement, subjecs in what context should be state clearly in the prompt) 
- Then generate using MCP tool https://server.smithery.ai/@falahgs/flux-imagegen-mcp-server/mcp?api_key=4e8105a9-20be-46b9-b8d4-8fc9265b924d -> using tool "generateImageUrl"
- After that, access the generated image through returned link
- Download the image, rename correctly as the document requested
- Save to instructed/requested directories (you may need to create directories at very beginning if they do not exist.
