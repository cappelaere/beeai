# Documentation Quick Reference

## 🚀 Getting Started
- [Main README](../README.md) - Project overview
- [Shell Setup](SHELL_SETUP.md) - Development environment automation
- [Node.js Setup](NODE_SETUP.md) - nvm and Node.js configuration
- [Quick Start Guide](#quick-start)

## 📖 Core Documentation
- [Technical Specifications](SPECS.md) - Complete system specs
- [Documentation Index](README.md) - Full documentation overview

## 🐳 Infrastructure
- [Docker Setup](DOCKER_SETUP.md) - Service management
- [Redis Architecture](REDIS_DATABASE_SEPARATION.md) - Cache database design
- [Redis Configuration](REDIS_CONFIG_FIX.md) - Troubleshooting guide

## ⚡ Features
- [LLM Caching](CACHE_IMPLEMENTATION.md) - Response caching system
- [Observability](OBSERVABILITY.md) - Langfuse integration
- [Observability Quick Start](OBSERVABILITY_QUICKSTART.md) - 5-minute setup

## 🧪 Testing
- [Testing Strategy](TESTING.md) - Overview
- [Test Summary](TEST_SUMMARY.md) - Implementation details
- [Tests Created](TESTS_CREATED.md) - Complete test documentation

## 📚 Reference
- [Business Intelligence](business-intelligence.md) - BI prompts
- [Tools](tools.md) - Available tools
- [App Structure](app.md) - Application architecture

## Quick Start

```bash
# Complete setup
make all

# Start development
make dev

# Start all services
make docker-up

# View help
make help
```

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| UI | 8002 | http://localhost:8002 |
| API | 8000 | http://localhost:8000 |
| Redis | 6379 | localhost:6379 |
| PostgreSQL | 8080 | localhost:8080 |
| pgAdmin | 5555 | http://localhost:5555 |

---

For complete documentation, see [README.md](README.md)
