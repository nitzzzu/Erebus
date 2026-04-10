---
name: skill-creator
description: Create new custom skills and save them to the user-skills directory so the agent can learn and use them in future sessions.
---

# Skill Creator

Use this skill to design and save new custom skills to the user-skills folder
(`~/.erebus/user-skills/`).  Skills saved here are separate from the built-in
skills and are loaded automatically every time the agent starts.

## When to Use

- User asks you to "create a new skill", "teach me how to do X", "save this workflow"
- A recurring pattern has been discovered that should be formalised as a skill
- User wants to extend the agent's capabilities with domain-specific knowledge

## How to Create a Skill

Use the API endpoint `POST /api/skills` with the following body:

```json
{
  "name": "my-skill",
  "description": "One-line description of what this skill does",
  "content": "Full SKILL.md body (markdown, workflow steps, examples)",
  "category": "optional-category"
}
```

Or use `ShellTools` / `FileTools` to write directly to:

```
~/.erebus/user-skills/<category>/<name>/SKILL.md
```

## SKILL.md Format

```markdown
---
name: skill-name
description: Short description
---

# Skill Title

## When to Use
...

## Steps / Instructions
...

## Output Format
...
```

## Important Notes

- User-created skills live in `~/.erebus/user-skills/` — **never** in the
  built-in `erebus/skills/builtins/` directory.
- The registry is refreshed automatically after saving via the API.
- Keep skill names lowercase with hyphens (e.g. `daily-standup`).
- Category is optional; use it to group related skills.
