---
type: tool_order
before: { tool: Read, input_match: 'git-conventions\.md' }
after: { tool: Bash, input_match: '"command"\s*:\s*"[^\"]*git commit' }
---
