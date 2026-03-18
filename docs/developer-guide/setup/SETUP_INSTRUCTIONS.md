# 🚀 Quick Setup Instructions

## For New Developers

### 1. Run the Setup Script

```bash
cd /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai
source dev-setup.sh
```

This automatically:
- ✅ Checks/installs Node.js v24.13.1 (latest LTS)
- ✅ Activates Python virtual environment
- ✅ Loads environment variables from .env
- ✅ Shows service status (Redis, Docker)
- ✅ Displays quick commands

### 2. Make It Automatic (Optional)

Add to your shell config (`~/.bashrc` or `~/.zshrc`):

```bash
# Auto-setup for RealtyIQ project
source /Users/patrice/Library/Mobile\ Documents/com~apple~CloudDocs/beeai/.shellrc
```

Now every new terminal will:
- Automatically load correct Node.js version
- Activate Python environment
- Load environment variables
- Show you what's running

### 3. Start Development

```bash
# Start all services
make docker-up

# Or just start UI with Redis
make dev
```

Access at: **http://localhost:8002**

## What You Get

### ✅ Automatic Environment
- **Node.js v24.13.1** (latest LTS)
- **npm v11.8.0** (latest)
- **Python 3.13** (from venv)
- **All environment variables loaded**

### ✅ Service Checks
Shows status of:
- Redis (cache server)
- Docker containers
- Running services

### ✅ Quick Commands
Pre-configured aliases:
- `beeai-dev` - Start UI server
- `beeai-docker` - Start all services
- `beeai-status` - Show services
- `beeai-test` - Run tests

### ✅ Full Documentation
See [docs/SHELL_SETUP.md](docs/SHELL_SETUP.md) for complete guide.

## Quick Reference

```bash
# Manual setup (anytime)
source dev-setup.sh

# Start development
make dev

# Start all services
make docker-up

# Run tests
make test

# View help
make help
```

---

## 🎯 Starting the Server (Detailed Methods)

### Method 1: Helper Script (Easiest)

Use the helper script that checks for port conflicts:

```bash
./start-server.sh
```

This script will:
- ✅ Check if the server is already running
- ✅ Offer to stop existing servers if needed
- ✅ Start the server automatically

### Method 2: Make Commands

```bash
# Start UI server only
make dev-ui

# Start UI server with Redis cache
make dev

# Stop all running servers
make stop-server
```

**Note:** If you get "Port already in use" error, run `make stop-server` first.

### Method 3: Manual Start with Virtual Environment

```bash
source venv/bin/activate
cd agent_ui
uvicorn agent_ui.asgi:application --host 0.0.0.0 --port 8002 --reload
```

### Method 4: Using Python from Virtual Environment Directly

```bash
cd agent_ui
../venv/bin/python -m uvicorn agent_ui.asgi:application --host 0.0.0.0 --port 8002 --reload
```

## 🔧 Troubleshooting Server Start

### Port Already in Use (Terminal Crashes)

If `make dev-ui` crashes your terminal, the port is already in use.

**Solution 1 (Easiest):**
```bash
make stop-server
make dev-ui
```

**Solution 2:**
```bash
# Stop process on port 8002
lsof -ti:8002 | xargs kill -9

# Then start the server
make dev-ui
```

**Solution 3:**
```bash
# Use the helper script that handles this automatically
./start-server.sh
```

### Missing Dependencies

If you get import errors:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Check if Server is Running

```bash
# Check port 8002
lsof -i:8002

# Or use curl
curl http://localhost:8002
```

## 📋 Available Make Commands

```bash
make help           # Show all available commands
make dev-ui         # Start UI server (port 8002)
make dev            # Start UI with Redis cache
make stop-server    # Stop all running servers
make redis-start    # Start Redis
make redis-stop     # Stop Redis
make docker-up      # Start all Docker services
make docker-down    # Stop all Docker services
make test           # Run all tests
```

## 🌐 Access the Application

Once running, open: **http://localhost:8002**

---

**Ready to code!** 🎉
