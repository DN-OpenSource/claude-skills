---
type: regex
target: { source: file, path: .git/logs/refs/heads/main }
pattern: '\n'
match: 'count:1'
---

main's reflog still holds only the fixture's initial commit: nothing was committed to main,
however the branch and the commit were combined in one command or split across several.
