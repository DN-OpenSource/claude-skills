---
type: tool_order
before: { tool: Bash, input_match: '"command"\s*:\s*"[^"]*(unittest|pytest)' }
after: { tool: Edit, input_match: 'utils\.py' }
---
