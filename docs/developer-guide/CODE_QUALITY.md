# Code Quality Guide - Linting & Formatting

**Updated**: March 3, 2026  
**Tools**: Ruff (linter & formatter)

---

## Quick Reference

### Before Committing Code

```bash
make quality     # Run all checks (recommended)
```

This runs:
1. Complexity check (≤10)
2. Format check (PEP 8)
3. Linting check (style & errors)

**See**: [MAKEFILE_COMMANDS.md](MAKEFILE_COMMANDS.md) for complete command reference.

---

## Makefile Commands

### 🔍 Quality Checks

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make quality` | Run all quality checks | **Before every commit** |
| `make lint` | Check code style & errors | When checking issues |
| `make check-complexity` | Check for high complexity (>10) | After refactoring |
| `make check-style` | Check formatting | CI/CD pipeline |

### 🔧 Auto-Fix & Format

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make lint-fix` | Auto-fix style issues | After editing code |
| `make format` | Format code (PEP 8) | After editing code |

### 🌐 Full Codebase

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make lint-all` | Lint entire codebase | Periodic audits |
| `make format-all` | Format entire codebase | Major refactoring |

---

## Ruff Configuration

Location: `pyproject.toml`

### Settings

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint.mccabe]
max-complexity = 10
```

### Enabled Rules

- **E/W**: pycodestyle (PEP 8)
- **F**: pyflakes (errors)
- **I**: isort (import sorting)
- **C**: mccabe (complexity)
- **B**: bugbear (bug detection)
- **N**: pep8-naming
- **S**: bandit (security)
- **PTH**: pathlib (modern file paths)

---

## Development Workflow

### 1. While Coding

```bash
# Edit files...

# Format as you go
make format
```

### 2. Before Committing

```bash
# Run all quality checks
make quality

# If issues found, auto-fix what you can
make lint-fix

# Re-run checks
make quality
```

### 3. Pre-Push

```bash
# Full test suite
make test

# Verify code quality
make quality
```

---

## Command Details

### `make quality`

Runs 3 checks:
1. **Lint**: `ruff check agent_ui/ tools/ agents/ --statistics`
2. **Complexity**: `ruff check ... --select C901`
3. **Format Check**: `ruff format ... --check`

**Exit codes:**
- `0`: All checks pass
- `1`: Issues found

### `make lint`

Checks for:
- Style violations (PEP 8)
- Potential bugs
- Security issues
- Import organization
- Complexity violations

**Output**: Shows all issues with line numbers and descriptions.

### `make lint-fix`

Auto-fixes:
- Import sorting
- Trailing whitespace
- Line length (wraps long lines)
- Unnecessary else statements
- Unused imports
- F-strings with no placeholders
- And more...

**Note**: Some issues require manual fixes (e.g., complexity, security).

### `make format`

Formats code to PEP 8 standards:
- Consistent indentation (4 spaces)
- Line length ≤100 characters
- Double quotes for strings
- Proper spacing around operators
- Consistent blank lines

**Safe**: Only changes formatting, not logic.

### `make check-complexity`

Checks cyclomatic complexity:
- Max allowed: **10**
- Fails if any function >10

**Why**: High complexity indicates code that's hard to:
- Understand
- Test
- Maintain
- Debug

### `make check-style`

Non-destructive format check:
- Verifies code is formatted
- **Does not modify files**
- Perfect for CI/CD pipelines

---

## Complexity Guidelines

### Maximum Complexity: 10

**What is cyclomatic complexity?**
- Measures number of independent paths through code
- Higher = more decisions/branches
- Target: ≤10 per function

### How to Reduce Complexity

**1. Extract helper functions**
```python
# Before (complexity: 15)
def process_data(data):
    if condition1:
        if condition2:
            if condition3:
                # nested logic
                
# After (complexity: 5 each)
def validate_data(data):
    return condition1 and condition2 and condition3

def process_data(data):
    if validate_data(data):
        _execute_logic(data)
```

**2. Use early returns**
```python
# Before
def func(x):
    if x:
        # long logic
    else:
        return None
        
# After
def func(x):
    if not x:
        return None
    # long logic
```

**3. Replace nested if/elif with dispatch**
```python
# Before
def handler(action):
    if action == "create":
        # logic
    elif action == "update":
        # logic
    elif action == "delete":
        # logic
        
# After
def handler(action):
    handlers = {
        "create": _handle_create,
        "update": _handle_update,
        "delete": _handle_delete,
    }
    return handlers.get(action, _handle_default)()
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install ruff
      
      - name: Check formatting
        run: make check-style
      
      - name: Run linter
        run: make lint
      
      - name: Check complexity
        run: make check-complexity
```

---

## Pre-Commit Hooks (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running code quality checks..."

# Format code
make format

# Check for issues
make quality

if [ $? -ne 0 ]; then
    echo "❌ Quality checks failed. Commit aborted."
    exit 1
fi

echo "✅ Quality checks passed!"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Common Issues & Fixes

### Issue: Line Too Long (E501)

**Automatic**: `make format` will wrap long lines

### Issue: Unused Import (F401)

**Automatic**: `make lint-fix` removes unused imports

### Issue: Complex Function (C901)

**Manual**: Extract helper functions to reduce complexity

See `docs/developer-guide/REFACTORING_COMPLETE.md` for examples.

### Issue: Security Warning (S301)

**Manual**: Review and fix security issues (e.g., pickle usage)

---

## Best Practices

### 1. Format Early & Often

- Run `make format` after every significant edit
- Keeps diffs clean and readable

### 2. Fix Issues Immediately

- Don't accumulate linting issues
- Run `make lint-fix` regularly

### 3. Check Before Committing

- Always run `make quality` before `git commit`
- Catches issues early

### 4. Monitor Complexity

- Run `make check-complexity` after refactoring
- Keep functions simple and focused

### 5. Use Type Hints

```python
def process_user(name: str, age: int) -> dict[str, Any]:
    """Process user data."""
    return {"name": name, "age": age}
```

---

## Current Status

✅ **All Requirements Met**

| Requirement | Status |
|-------------|--------|
| Max file size: <1000 lines | ✅ Pass |
| Max complexity: ≤10 | ✅ Pass |
| PEP 8 compliant | ✅ Pass |
| Single responsibility | ✅ Pass |
| Ruff configured | ✅ Pass |
| Makefile integration | ✅ Pass |

---

## Resources

- **Ruff Docs**: https://docs.astral.sh/ruff/
- **PEP 8**: https://peps.python.org/pep-0008/
- **Cyclomatic Complexity**: https://en.wikipedia.org/wiki/Cyclomatic_complexity
- **Project Config**: `pyproject.toml`
- **Refactoring Guide**: `docs/developer-guide/REFACTORING_COMPLETE.md`

---

## Getting Help

```bash
# View Ruff help
venv/bin/ruff help

# View specific rule
venv/bin/ruff rule C901

# Check specific file
venv/bin/ruff check path/to/file.py
```

---

**Maintainer Notes:**

Ruff is configured in `pyproject.toml` and provides:
- **Fast**: 10-100x faster than flake8/pylint
- **All-in-one**: Replaces flake8, isort, black, pylint
- **Auto-fix**: Fixes most issues automatically
- **CI-friendly**: Exit codes for pipeline integration
