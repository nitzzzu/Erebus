---
name: code-review
description: Pre-commit code review pipeline with static analysis, security scanning, and automated fix suggestions.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["software-development", "code-review", "quality", "security"]
---

# Code Review Pipeline

Use this skill for thorough code review before commits or merges.

## When to Use

- User wants a code review of their changes
- Before committing or pushing code
- User asks for feedback on code quality
- User wants security analysis of changes

## Review Checklist

### 1. Correctness
- Logic errors, off-by-one, null handling
- Edge cases and boundary conditions
- Error handling completeness

### 2. Security
- Input validation and sanitization
- Authentication and authorization
- Secrets exposure, injection vulnerabilities

### 3. Code Quality
- Naming conventions and readability
- DRY principle, code duplication
- Function length and complexity

### 4. Testing
- Test coverage for new/changed code
- Edge case testing
- Integration test needs

### 5. Performance
- Algorithm complexity
- Database query efficiency
- Memory usage patterns

### 6. Documentation
- Docstrings and comments
- API documentation updates
- README changes if needed

## Process

1. **Diff**: Get the code changes (git diff or provided code)
2. **Static Analysis**: Run linters and type checkers
3. **Security Scan**: Check for common vulnerabilities
4. **Review**: Apply the checklist systematically
5. **Report**: Provide findings with severity and fix suggestions
