---
name: send-notification
description: Send notifications to users via configured apprise channels (Telegram, email, Slack, etc.)
---

# Send Notification

Use this skill to send push notifications, briefings, or alerts to the user
through any apprise-compatible channel configured in Erebus.

## When to Use

- User wants a morning/evening briefing delivered to Telegram or email
- A cron schedule completes a task and the result should be pushed to the user
- User asks to "notify me", "send me an alert", "ping me on Telegram", etc.
- Automated tasks need to report their outcome

## How to Use

Call `send_notification` from the built-in `notify` toolkit:

```
send_notification(message="Your briefing is ready!", title="Morning Briefing")
```

To target a specific channel by name:

```
send_notification(message="Deploy succeeded", channel="telegram")
```

## Channel Resolution

1. If `channel` is given → use that named channel
2. Otherwise → use the default channel (star icon in the Notifications UI)
3. If no default is set → broadcast to all enabled channels
4. As a last resort → use `EREBUS_APPRISE_DEFAULT_URL` if set

## Supported Apprise URL Examples

| Service   | URL Format                                      |
|-----------|-------------------------------------------------|
| Telegram  | `tgram://bottoken/chatid`                       |
| Email     | `mailto://user:pass@gmail.com`                  |
| Slack     | `slack://tokenA/tokenB/tokenC/channel`          |
| Discord   | `discord://webhook_id/webhook_token`            |
| Pushover  | `pover://user@apptoken`                         |

Full list: https://github.com/caronc/apprise/wiki

## Output Format

The tool returns a plain-text confirmation:

```
Notification sent successfully via: telegram
```

or an error message if delivery fails.
