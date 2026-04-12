---
name: brainstorming
description: Use BEFORE any creative work — creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements, and design before implementation.
metadata:
  version: "2.0.0"
  author: erebus
  tags: ["software-development", "planning", "design", "requirements"]
---

# Brainstorming: Ideas Into Designs

Turn rough ideas into fully formed designs and specs through collaborative dialogue.
Start by understanding the current project context, then ask questions one at a time.
Once you understand what's being built, present the design and get user approval.

<HARD-GATE>
Do NOT write any code, scaffold any project, or invoke any implementation skill
until you have presented a design and the user has explicitly approved it.
This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process — a todo list, a single-function utility,
a config change — all of them. "Simple" projects are where unexamined assumptions
cause the most wasted work. The design can be short (a few sentences), but you
MUST present it and get approval.

## Checklist

Complete each item in order:

1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time; understand purpose, constraints, success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections, get user approval after each section
5. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` and commit
6. **Spec self-review** — check for placeholders, contradictions, ambiguity
7. **User reviews written spec** — ask user to review before proceeding
8. **Transition** — invoke writing-plans skill to create implementation plan

## The Process

### Understanding the Idea

- Check project state first (files, docs, recent commits)
- Assess scope: if the request spans multiple independent subsystems, flag this immediately
  and help decompose into sub-projects before diving into details
- Ask questions **one at a time** — prefer multiple-choice when possible
- Focus on: purpose, constraints, success criteria

### Exploring Approaches

- Propose exactly 2-3 different approaches
- Include trade-offs for each (complexity, performance, maintainability)
- State your recommendation and why
- Keep options concrete — "use library X" not "use a library"

### Presenting the Design

- Once you understand what's being built, present the design
- Scale each section to its complexity: a few sentences if simple, up to 200 words if complex
- Ask after each section: "Does this look right so far?"
- Cover: architecture, components, data flow, error handling, testing
- Be ready to revise if something doesn't make sense

### Design for Isolation and Clarity

- Break the system into units with one clear purpose and well-defined interfaces
- For each unit answer: what does it do, how do you use it, what does it depend on?
- Smaller, well-bounded units are easier to test and reason about

### After the Design

**Write the spec:**
- Save validated design to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Commit the document

**Spec self-review:**
1. Placeholder scan — any "TBD", "TODO", incomplete sections? Fix them.
2. Internal consistency — do sections contradict each other?
3. Scope check — is this focused enough for a single implementation plan?
4. Ambiguity check — could any requirement be interpreted two ways? Pick one, make it explicit.

**User review gate:**
> "Spec written and committed to `<path>`. Please review it and let me know if
> you'd like any changes before I start the implementation plan."

Wait for approval. Only after approval: invoke the **writing-plans** skill.

## Key Principles

- **One question at a time** — don't overwhelm
- **YAGNI ruthlessly** — remove unnecessary features from all designs
- **Explore alternatives** — always propose 2-3 approaches before settling
- **Incremental validation** — present design sections, get approval, then continue

## What Comes Next

The terminal state is invoking **writing-plans**.
Do NOT invoke any implementation skill directly from brainstorming.
