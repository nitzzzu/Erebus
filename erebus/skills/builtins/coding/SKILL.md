---
name: coding
description: Read, write, edit files and execute shell commands to help with coding tasks.
license: MIT
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["coding", "files", "shell", "development"]
---

# Coding Skill

Use this skill when the user needs help with coding tasks involving file operations or command execution.

## When to Use

- User wants to read, create, or edit files
- User needs to run shell commands or scripts
- User asks for help debugging or building a project
- User wants to explore a codebase

## Core Tools

- `read_file` / `save_file` — read and write files
- `list_files` / `search_files` — browse the filesystem
- `run_shell_command` — execute shell commands (bash, python, etc.)
- `replace_file_chunk` — make targeted edits to existing files

## Process

1. **Understand the Task**: Clarify what needs to be done
2. **Explore**: Read existing files to understand context before making changes
3. **Plan**: Think through changes before executing
4. **Execute**: Make minimal, targeted changes
5. **Verify**: Run tests or commands to verify the changes work

## Best Practices

- Always read a file before editing it
- Make small, incremental changes
- Run `ls` or `find` to explore directory structure
- Use `run_shell_command` to run tests after making changes
- Prefer editing existing files over creating new ones when fixing bugs
- Keep backups in mind — don't delete files without asking

## Safety

- Never delete files without explicit user confirmation
- Be cautious with commands that have side effects (rm, chmod, network calls)
- Avoid running untrusted code
