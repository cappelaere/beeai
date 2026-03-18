# Shell Setup Summary

## ✅ Created Development Environment Script

A comprehensive shell script has been created to automate your development environment setup.

## Files Created

### 1. `dev-setup.sh` - Main Setup Script

**Location**: `/beeai/dev-setup.sh`

**What it does**:
- ✅ **Node.js Management** - Loads nvm, checks version against `.nvmrc`, auto-installs/switches if needed
- ✅ **Python Environment** - Finds and activates virtual environment (venv, .venv, or env)
- ✅ **Environment Variables** - Loads all variables from `.env` file
- ✅ **Service Status** - Checks Redis and Docker services
- ✅ **Quick Reference** - Shows common commands and service URLs

### 2. `.shellrc` - Auto-loader Configuration

**Location**: `/beeai/.shellrc`

**What it does**:
- Runs `dev-setup.sh` once per shell session
- Provides useful aliases:
  - `beeai-dev` → `make dev`
  - `beeai-docker` → `make docker-up`
  - `beeai-redis` → `make redis-start`
  - `beeai-test` → `make test`
  - `beeai-logs` → `make docker-logs`
  - `beeai-status` → `docker ps` (formatted)

### 3. `docs/SHELL_SETUP.md` - Documentation

Complete guide on using the shell setup scripts.

## Usage

### Option 1: Manual (Every Terminal)

```bash
cd /path/to/beeai
source dev-setup.sh
```

### Option 2: Automatic (Recommended)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc
```

Then every new terminal automatically sets up your environment!

## Example Output

```
🚀 RealtyIQ Development Environment Setup
========================================

📦 Checking Node.js setup...
✓ nvm loaded
  Required Node version: v24.13.1
✓ Node.js v24.13.1 (correct version)
  npm version: 11.8.0

🐍 Checking Python environment...
✓ Virtual environment activated (venv)
  Python version: 3.13.9

⚙️  Loading environment variables...
✓ Environment variables loaded from .env (47 variables)
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
  make redis-start  - Start Redis only
  make test         - Run all tests
  make help         - Show all available commands

🌐 Service URLs:
  UI:         http://localhost:8002
  API:        http://localhost:8000
  pgAdmin:    http://localhost:5555
  Redis:      localhost:6379
  PostgreSQL: localhost:8080

📚 Documentation: docs/README.md
```

## What Gets Checked

### ✅ Node.js Version
- Reads required version from `.nvmrc` (24.13.1)
- Checks if current version matches
- Auto-switches if different
- Auto-installs if missing

### ✅ Python Virtual Environment
- Searches for venv/, .venv/, or env/
- Activates automatically if found
- Shows Python version

### ✅ Environment Variables
- Loads all variables from `.env`
- Exports to environment
- Shows count and key variables
- Protects sensitive values

### ✅ Service Status
- **Redis**: Checks if running, suggests `make redis-start` if not
- **Docker**: Shows running containers, suggests `make docker-up` if none

## Quick Setup

### Step 1: Test the script

```bash
cd /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai
source dev-setup.sh
```

### Step 2: Make it automatic (optional)

```bash
# For bash
echo 'source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc' >> ~/.bashrc

# For zsh
echo 'source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc' >> ~/.zshrc
```

### Step 3: Open new terminal

Everything will be set up automatically!

## Benefits

### 🚀 Faster Setup
- No more manual environment configuration
- One command sets up everything
- Saves 2-3 minutes every time

### ✅ Consistency
- Always uses correct Node.js version
- Always loads environment variables
- Always activates Python environment

### 🔍 Visibility
- See what's running
- See what needs attention
- Quick command reference

### 🛠️ Convenience
- Useful aliases (beeai-*)
- Service status at a glance
- Quick access to common commands

## Troubleshooting

### Script doesn't find nvm

**Solution**: Install nvm first:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

### Virtual environment not found

**Solution**: Create one:
```bash
python3 -m venv venv
```

### .env not found

**Solution**: Copy from example:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Documentation

See **[docs/SHELL_SETUP.md](docs/SHELL_SETUP.md)** for:
- Complete usage guide
- Customization options
- Advanced features
- Troubleshooting

---

**Status**: ✅ **READY TO USE**

Run `source dev-setup.sh` to start!
