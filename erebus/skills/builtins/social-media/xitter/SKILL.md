---
name: xitter
description: Interact with X (Twitter) via the official API — post, search, like, retweet, and manage bookmarks.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["social-media", "twitter", "x", "posting"]
required_environment_variables:
  - name: X_API_KEY
    prompt: "Enter your X (Twitter) API Key"
  - name: X_API_SECRET
    prompt: "Enter your X API Secret"
---

# X (Twitter) Integration

Use this skill to interact with X (formerly Twitter).

## When to Use

- User wants to post tweets
- User needs to search X for topics or users
- User wants to manage bookmarks or likes
- User wants to monitor mentions or hashtags

## Operations

### Post a Tweet
### Search Tweets
### Like/Retweet
### Read Timeline
### Manage Bookmarks

## Process

1. **Authenticate**: Verify X API credentials are configured
2. **Identify Action**: What does the user want to do on X?
3. **Execute**: Perform the API call
4. **Confirm**: Show the result (tweet URL, search results, etc.)

## Best Practices

- Respect rate limits (300 tweets/3hrs, 900 reads/15min)
- Keep tweets under 280 characters
- Use threads for longer content
- Always confirm before posting
