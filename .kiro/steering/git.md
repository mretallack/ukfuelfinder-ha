# Git Workflow Guidelines

## Commit Policy

**NEVER commit automatically unless explicitly told to do so.**

When the user says:
- ✅ "commit" / "commit this" → Proceed with commit only
- ✅ "commit and push" / "push" / "push this" → Run tests, then commit and push
- ❌ Any other response → Do NOT commit

## Pre-Push Checklist

**Only run tests before pushing, not before committing.**

When user requests "commit and push" or "push", run the full GitHub Actions workflow locally:

### 1. Format Code
```bash
black custom_components tests
isort custom_components tests
```

### 2. Verify Formatting
```bash
black --check custom_components tests
isort --check-only custom_components tests
```

### 3. Run Tests
```bash
PYTHONPATH=. pytest tests/ -v -k "not integration"
```

### 4. Check All Pass
All three steps must pass before pushing:
- ✅ black check: no files to reformat
- ✅ isort check: imports correctly sorted
- ✅ pytest: all unit tests passing

## Workflow Examples

### Commit Only
```bash
# User says: "commit"
git add -A
git commit -m "message"
# STOP - do not push
```

### Commit and Push
```bash
# User says: "commit and push" or "push"
# 1. Run tests first
black custom_components tests
isort custom_components tests
black --check custom_components tests
isort --check-only custom_components tests
PYTHONPATH=. pytest tests/ -v -k "not integration"

# 2. If all pass, then commit and push
git add -A
git commit -m "message"
git push origin main
```

## Commit Message Format

Use clear, descriptive commit messages:
```
<type>: <short description>

- Bullet point details
- What changed
- Why it changed
```

Types: `Fix`, `Feature`, `Refactor`, `Docs`, `Test`, `Chore`

## Branch Strategy

- **main**: Production-ready code
- **dev**: Development branch (if exists)
- Always push to current branch unless specified otherwise

## Never Commit

- Secrets or API keys
- `.env` files (should be in `.gitignore`)
- Cache directories (`__pycache__`, `.pytest_cache`)
- IDE files (`.vscode`, `.idea`)
- Test artifacts

## Summary

1. Wait for explicit commit/push instruction
2. For "commit only" → just commit
3. For "commit and push" or "push" → run full workflow locally first
4. Only push if all checks pass
5. Use descriptive commit messages
