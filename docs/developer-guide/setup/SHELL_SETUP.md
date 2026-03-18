# Shell Setup for Development

## Quick Start

### Manual Setup (Every Terminal)

```bash
cd /path/to/beeai
source dev-setup.sh
```

This will:
- ✅ Load nvm and check/install correct Node.js version
- ✅ Activate Python virtual environment
- ✅ Load environment variables from .env
- ✅ Check service status (Redis, Docker)
- ✅ Display quick commands and service URLs

### Automatic Setup (Recommended)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# RealtyIQ auto-setup
source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc
```

Then every new terminal will automatically:
- Run setup when entering project directory
- Load all necessary tools and variables
- Show status and available commands

## Files Created

### 1. `dev-setup.sh` - Main Setup Script

**Location**: `/path/to/beeai/dev-setup.sh`

**What it does**:
1. **Node.js Check**
   - Loads nvm
   - Checks current Node version against `.nvmrc`
   - Auto-installs if missing
   - Auto-switches to correct version

2. **Python Environment**
   - Finds virtual environment (venv, .venv, or env)
   - Activates it automatically
   - Shows Python version

3. **Environment Variables**
   - Loads all variables from `.env`
   - Shows key variables (without exposing secrets)
   - Counts total variables loaded

4. **Service Status**
   - Checks if Redis is running
   - Checks Docker services
   - Shows running containers

5. **Quick Reference**
   - Displays common commands
   - Shows service URLs
   - Links to documentation

**Usage**:
```bash
# In project directory
source dev-setup.sh

# Or with full path
source /path/to/beeai/dev-setup.sh
```

### 2. `.shellrc` - Auto-loader Configuration

**Location**: `/path/to/beeai/.shellrc`

**What it does**:
- Runs `dev-setup.sh` once per shell session
- Prevents duplicate loading
- Sets up useful aliases

**Aliases provided**:
```bash
beeai-dev       # make dev
beeai-docker    # make docker-up
beeai-redis     # make redis-start
beeai-test      # make test
beeai-logs      # make docker-logs
beeai-status    # docker ps (formatted)
```

**Setup**:
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'source /path/to/beeai/.shellrc' >> ~/.bashrc

# Or for zsh
echo 'source /path/to/beeai/.shellrc' >> ~/.zshrc
```

## Setup Examples

### Example 1: Manual Each Time

```bash
$ cd ~/projects/beeai
$ source dev-setup.sh

🚀 RealtyIQ Development Environment Setup
========================================

📦 Checking Node.js setup...
✓ nvm loaded
  Required Node version: v24.13.1
✓ Node.js v24.13.1 (correct version)
  npm version: 11.8.0

🐍 Checking Python environment...
✓ Virtual environment activated (venv)
  Python version: 3.10.12

⚙️  Loading environment variables...
✓ Environment variables loaded from .env (35 variables)
  Key variables set:
    • LLM_CHAT_MODEL_NAME
    • REDIS_ENABLED=true
    • LANGFUSE_ENABLED=true
    • API_URL

🔍 Checking services...
✓ Redis is running
✓ Docker is running (3 service(s))

========================================
✓ Development environment ready!

📝 Quick commands:
  make dev          - Start UI development server
  make docker-up    - Start all Docker services
  ...
```

### Example 2: Automatic (Recommended)

Add to `~/.zshrc`:
```bash
# RealtyIQ auto-setup
source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc
```

Then:
```bash
$ cd ~/projects/beeai
# Setup runs automatically!
🚀 RealtyIQ Development Environment Setup
...
✓ Development environment ready!

$ beeai-dev
# Alias for 'make dev'

$ beeai-status
# Shows Docker containers
```

## What Gets Checked

### Node.js Version

```bash
# If .nvmrc exists (it does)
- Reads required version: 24.13.1
- Checks current version
- Auto-switches if different
- Auto-installs if missing
```

**Behavior**:
- ✅ Correct version → Just confirms
- ⚠️ Different version → Switches automatically
- ❌ Not installed → Installs then switches

### Python Virtual Environment

```bash
# Searches for (in order)
1. venv/
2. .venv/
3. env/

# If found
- Activates automatically
- Shows Python version
- Ready for pip/python commands
```

### Environment Variables

```bash
# From .env file
- Loads all variables
- Exports them to environment
- Shows count and key variables
- Doesn't expose sensitive values
```

**Variables loaded**:
- `LLM_CHAT_MODEL_NAME`
- `REDIS_URL`, `REDIS_ENABLED`
- `LANGFUSE_ENABLED`, `LANGFUSE_*`
- `API_URL`, `AUTH_TOKEN`
- `DATABASE_URL`, `POSTGRES_*`
- And 30+ more...

### Service Status

**Redis**:
```bash
✓ Redis is running         # redis-cli ping succeeds
⚠ Redis not running        # Suggests: make redis-start
⚠ redis-cli not found      # Redis not installed locally
```

**Docker**:
```bash
✓ Docker is running (3 service(s))  # Shows count
⚠ Docker running but no services    # Suggests: make docker-up
⚠ Docker not running                # Docker daemon not started
```

## Customization

### Add Custom Checks

Edit `dev-setup.sh` and add to the "Check key services" section:

```bash
# Check your custom service
if systemctl is-active --quiet myservice; then
    echo -e "${GREEN}✓${NC} MyService is running"
else
    echo -e "${YELLOW}⚠${NC}  MyService not running"
fi
```

### Add Custom Aliases

Edit `.shellrc` and add:

```bash
# Your custom aliases
alias beeai-backup='make db-backup'
alias beeai-clean='make clean && make redis-flush'
```

### Change What's Displayed

Edit the "Summary and next steps" section in `dev-setup.sh`:

```bash
echo "📝 Your custom commands:"
echo "  custom-command    - Description"
```

## Troubleshooting

### "nvm: command not found"

**Problem**: Script can't find nvm

**Solution**: Install nvm first:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

Then reload shell or source `~/.bashrc`.

### "Virtual environment not found"

**Problem**: No venv/ directory

**Solution**: Create virtual environment:
```bash
python3 -m venv venv
source dev-setup.sh
```

### ".env file not found"

**Problem**: Missing .env file

**Solution**: Copy example and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
source dev-setup.sh
```

### Script doesn't run automatically

**Problem**: .shellrc not sourced

**Solution**: Add to shell config:
```bash
# For bash
echo 'source /path/to/beeai/.shellrc' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'source /path/to/beeai/.shellrc' >> ~/.zshrc
source ~/.zshrc
```

### Wrong Node version still

**Problem**: Node version doesn't switch

**Solution**: Run nvm commands manually:
```bash
nvm install 24.13.1
nvm use 24.13.1
nvm alias default 24
```

## Best Practices

### 1. Run Setup in Every New Terminal

```bash
# Either manually
source dev-setup.sh

# Or add to shell config for automatic loading
source /path/to/beeai/.shellrc
```

### 2. Check Status Before Development

The script shows you:
- ✅ What's working
- ⚠️ What needs attention
- 📝 Quick commands to fix issues

### 3. Use Provided Aliases

```bash
# Instead of
make dev

# Use
beeai-dev

# Instead of
docker ps --format '...'

# Use
beeai-status
```

### 4. Keep .env Updated

When adding new environment variables:
1. Add to `.env`
2. Run `source dev-setup.sh` to reload
3. Verify with `echo $VARIABLE_NAME`

## Integration with IDEs

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "terminal.integrated.env.osx": {
    "BEEAI_AUTO_SETUP": "true"
  },
  "terminal.integrated.shellArgs.osx": [
    "-l",
    "-c",
    "source ~/path/to/beeai/dev-setup.sh && exec bash"
  ]
}
```

### PyCharm

1. Go to Settings → Tools → Terminal
2. Set Shell path to: `/bin/bash`
3. Check "Start directory": Project root
4. Add to `.bashrc` or use Project Interpreter setup

## Advanced Usage

### Skip Checks

To skip specific checks, modify `dev-setup.sh`:

```bash
# Skip Docker check
# Comment out the Docker section
# if command -v docker >/dev/null 2>&1; then
#   ...
# fi
```

### Silent Mode

For minimal output:

```bash
# Add at top of dev-setup.sh
SILENT_MODE=true

# Wrap echo statements
if [ "$SILENT_MODE" != "true" ]; then
    echo "..."
fi
```

### Export Setup Function

Add to your `~/.bashrc`:

```bash
beeai() {
    cd /path/to/beeai && source dev-setup.sh
}
```

Then just run `beeai` from anywhere!

## Files Reference

```
beeai/
├── dev-setup.sh          # Main setup script ⭐
├── .shellrc              # Auto-loader config
├── .nvmrc                # Node version spec
├── .env                  # Environment variables
├── venv/                 # Python virtual environment
└── docs/
    └── SHELL_SETUP.md    # This file
```

## Summary

### Quick Commands

```bash
# Manual setup
source dev-setup.sh

# Auto setup (add to ~/.zshrc)
source /path/to/beeai/.shellrc

# Check status
beeai-status

# Start development
beeai-dev
```

### What You Get

- ✅ Automatic Node.js version management
- ✅ Python virtual environment activation
- ✅ Environment variables loaded
- ✅ Service status checks
- ✅ Quick command reference
- ✅ Useful aliases

---

**Status**: ✅ **READY**

Shell setup complete - run `source dev-setup.sh` to activate!
