---
name: webhook-subscriptions
description: Create webhook subscriptions for event-driven agent activation from GitHub, GitLab, Stripe, and CI/CD systems.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["devops", "webhooks", "events", "automation", "ci-cd"]
---

# Webhook Subscriptions

Use this skill to set up webhook-based event-driven automation.

## When to Use

- User wants to react to GitHub events (push, PR, issue)
- User needs webhook endpoints for external services
- User wants event-driven agent activation
- User needs to integrate with CI/CD pipelines

## Supported Sources

- **GitHub**: Push, PR, issues, releases, workflow runs
- **GitLab**: Push, merge requests, pipelines
- **Stripe**: Payment events, subscription changes
- **Generic**: Any service that sends HTTP POST webhooks

## Process

1. **Identify Event**: What event should trigger the agent?
2. **Create Endpoint**: Set up a webhook receiver URL
3. **Configure Source**: Register the webhook in the source service
4. **Test**: Send a test event to verify connectivity
5. **Handle**: Define what the agent should do when triggered

## Security

- Validate webhook signatures (HMAC)
- Use HTTPS endpoints only
- Implement rate limiting
- Log all incoming webhooks for auditing
