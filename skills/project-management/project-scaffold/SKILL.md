---
name: project-scaffold
description: Create a project directory structure from a tree specification.
category: project-management
---

# Project Scaffold

Skill for creating a project directory structure from a tree specification.

## When to Use
When you need to create a set of directories and files based on a hierarchical description, such as setting up a new software project from a defined layout.

## Steps
1. Review the specification: understand the directory tree and file contents.
2. Create base directory if it doesn't exist.
3. For each directory in the tree, ensure it exists (mkdir -p).
4. For each file, create it with the specified content. If content is not provided, create an empty file.
5. Optionally verify that created files match expectations.

## Tips
- Use `mkdir -p` to create parent directories as needed.
- Use `write_file` to create files with exact content.
- For tree specifications given in text, parse lines to extract paths.
- Always work within the intended project root to avoid stray files.

## Example
Given a specification like:
```
project/
├── src/
│   └── main.py
└── README.md
```
Create directories `project`, `project/src`, then create files `project/src/main.py` and `project/README.md` with appropriate content.

## Pitfalls
- Forgetting to create parent directories leading to missing paths.
- Overwriting existing files unintentionally; verify if needed.
- Misinterpreting the tree specification (e.g., confusing files with directories).

## References
- See `references/session-2026-10-17-autonomous-trading-controller.md` for the specific session that inspired this skill.