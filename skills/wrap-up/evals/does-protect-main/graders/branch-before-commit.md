---
type: tool_order
before: { tool: Bash, input_match: '"command"\s*:\s*"[^\"]*git (switch -c|checkout -b) wip/' }
after: { tool: Bash, input_match: '"command"\s*:\s*"[^\"]*git commit' }
---
