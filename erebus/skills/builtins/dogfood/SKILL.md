---
name: dogfood
description: Systematic web application QA testing — five-phase exploratory workflow with evidence capture and structured reporting.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["testing", "qa", "browser", "dogfood", "bugs"]
---

# Dogfood — Systematic QA Testing

Use this skill for thorough exploratory testing of web applications.

## When to Use

- User wants QA testing of a web application
- User needs to find bugs before release
- User wants a structured test report
- User asks to "dogfood" or "test" their app

## Five Phases

### Phase 1: Plan
- Create output directory structure
- Define scope and test areas
- List key user flows to test

### Phase 2: Explore
- Navigate all pages and features
- Test user flows end-to-end
- Try edge cases and error states
- Test responsive design

### Phase 3: Collect Evidence
- Screenshot every issue found
- Record steps to reproduce
- Note expected vs. actual behavior
- Capture browser console errors

### Phase 4: Categorize
- De-duplicate similar issues
- Categorize by severity: Critical, Major, Minor, Cosmetic
- Group by feature area

### Phase 5: Report
- Generate structured bug report
- Include screenshots and reproduction steps
- Prioritize by business impact
- Suggest fixes where obvious

## Output Format

```markdown
# QA Report: [App Name]

## Summary
- Critical: X issues
- Major: Y issues  
- Minor: Z issues

## Issues

### [CRITICAL] Issue Title
**Page**: /path
**Steps**: 1. Go to... 2. Click... 3. Observe...
**Expected**: ...
**Actual**: ...
**Screenshot**: [link]
```
