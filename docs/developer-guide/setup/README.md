# Setup & Infrastructure Documentation

Documentation for development environment setup and infrastructure.

---

## Main Documentation

- **[SHELL_SETUP.md](SHELL_SETUP.md)** - Development environment automation
- **[SHELL_SETUP_SUMMARY.md](SHELL_SETUP_SUMMARY.md)** - Shell setup summary
- **[NODE_SETUP.md](NODE_SETUP.md)** - Node.js and nvm configuration
- **[NODE_VERSION_UPDATE.md](NODE_VERSION_UPDATE.md)** - Node version updates
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Docker service management
- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - General setup instructions

---

## Quick Start

```bash
# Automatic environment setup (recommended)
source dev-setup.sh

# Manual setup
make all        # Complete setup
make dev        # Start development server
make docker-up  # Start all services
```

### All Available Commands

See **[MAKEFILE_COMMANDS.md](../MAKEFILE_COMMANDS.md)** for complete list of setup, development, testing, and quality commands.

---

**Back to**: [Documentation Index](../README.md)
