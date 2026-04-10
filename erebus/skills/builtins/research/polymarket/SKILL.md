---
name: polymarket
description: Query Polymarket prediction market data via public REST APIs for market odds and event forecasts.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["research", "predictions", "markets", "data"]
---

# Polymarket — Prediction Market Data

Use this skill to query prediction market data from Polymarket.

## When to Use

- User asks about prediction market odds
- User wants to know probability estimates for future events
- User needs market data on political, economic, or cultural events
- User asks "what are the odds of X happening"

## API Endpoints

### Search Markets
```bash
curl -s "https://gamma-api.polymarket.com/markets?_limit=10&active=true&closed=false&_q={query}"
```

### Get Market Details
```bash
curl -s "https://gamma-api.polymarket.com/markets/{market_id}"
```

### Get Event Markets
```bash
curl -s "https://gamma-api.polymarket.com/events?_limit=10&_q={query}"
```

## Process

1. **Search**: Query Polymarket for relevant markets
2. **Parse**: Extract market question, current odds, volume, and end date
3. **Present**: Show probabilities as percentages with context
4. **Caveat**: Always note that prediction markets reflect crowd sentiment, not certainty

## Output Format

| Market | Yes | No | Volume | End Date |
|--------|-----|-----|--------|----------|
| Will X happen? | 65% | 35% | $2.1M | 2025-12-31 |
