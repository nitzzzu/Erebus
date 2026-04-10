---
name: linear
description: Manage Linear issues, projects, and cycles via GraphQL API using curl with no dependencies.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "linear", "issues", "project-management"]
required_environment_variables:
  - name: LINEAR_API_KEY
    prompt: "Enter your Linear API key"
---

# Linear Issue Manager

Use this skill to manage Linear issues, projects, and cycles.

## When to Use

- User wants to create, update, or close Linear issues
- User needs to list issues by project, team, or assignee
- User wants to manage Linear cycles or projects
- User needs to search issues

## API Usage

All requests use GraphQL via curl:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 10) { nodes { id title state { name } } } }"}'
```

## Common Operations

### List Issues
### Create Issue
### Update Issue State
### List Projects
### Search Issues

## Process

1. **Identify Operation**: What does the user need to do in Linear?
2. **Build Query**: Construct the GraphQL query or mutation
3. **Execute**: Run via curl with authorization
4. **Parse**: Extract relevant data from JSON response
5. **Present**: Format results as a table or list
