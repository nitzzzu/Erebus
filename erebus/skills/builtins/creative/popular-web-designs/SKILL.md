---
name: popular-web-designs
description: Reference library of 50+ real-world web design systems (Stripe, Linear, Vercel, Notion) with exact CSS values.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["creative", "design", "css", "web", "ui"]
---

# Popular Web Design Systems Reference

Use this skill when building web UIs that should match the quality of top SaaS products.

## When to Use

- User wants a website that looks like Stripe, Linear, Vercel, etc.
- User needs modern web design inspiration
- User asks for specific CSS values from popular sites
- User wants to replicate a particular design aesthetic

## Design Systems

### Stripe
- Font: `-apple-system, BlinkMacSystemFont, "Segoe UI"`, 15px body
- Colors: `#635bff` (primary purple), `#0a2540` (navy), `#425466` (text)
- Gradients: Mesh gradients with purple/blue/teal
- Border radius: 12px cards, 6px buttons

### Linear
- Font: `"Inter", -apple-system`, 14px base
- Colors: `#5e6ad2` (purple), `#171723` (bg), `#f7f8f8` (text)
- Dark-first design, minimal borders
- Animations: spring-based, 200ms duration

### Vercel
- Font: `"Inter", -apple-system`, 14px base
- Colors: `#000000` / `#ffffff` (stark contrast), `#0070f3` (link blue)
- Geist Mono for code blocks
- Minimal, high-contrast design

### Notion
- Font: `-apple-system`, 16px body
- Colors: Warm gray palette, `#2eaadc` (blue accent)
- Rounded corners: 3px default
- Block-based content layout

## Process

1. **Identify Style**: Which design system best matches the request?
2. **Extract Values**: Pull exact CSS variables and component specs
3. **Apply**: Use the design tokens in the implementation
4. **Adapt**: Modify to fit the user's specific needs
