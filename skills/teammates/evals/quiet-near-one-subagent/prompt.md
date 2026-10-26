---
description: teammates should not trigger on a request about the same topic
tags: [trigger, negative, near-miss]
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Spawn one subagent to list the TODO comments in this repo.
