# User Guide

**How to use RealtyIQ - Documentation for end users**

This section contains all documentation for using RealtyIQ's features, commands, and workflows.

---

## Quick Start

### Essential Guides
- **[Commands (Quick Start)](COMMANDS.md)** - All slash commands and how to use them
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

---

## Workflows & Tasks

### [Workflow Management](workflow_management/README.md)
Learn how to execute workflows and manage tasks:
- **[Quick Reference](workflow_management/QUICK_REFERENCE.md)** - One-page command cheatsheet - START HERE
- **[Complete Guide](workflow_management/WORKFLOW_AND_TASK_GUIDE.md)** - Comprehensive workflow & task reference
- **[Test Suite](workflow_management/TEST_SUITE.md)** - Test documentation

**Quick Commands**:
```bash
/workflow list              # List available workflows
/workflow runs              # View your workflow runs
/task list                  # View your tasks
/task claim <task_id>       # Claim a task
/task submit <task_id> approve  # Submit task
```

---

## Accessibility Features

### Enabling Section 508 Mode

RealtyIQ includes accessibility features for users with disabilities:

**Enable/Disable**:
```bash
/settings 508 on         # Enable accessibility mode
/settings 508 off        # Disable accessibility mode
```

**What You Get**:
- Larger fonts and better contrast
- Text-to-Speech with audio controls
- Enhanced keyboard navigation
- Screen reader optimization

See **[Commands Reference](COMMANDS.md)** for all settings commands.

For technical implementation details, see [Developer Guide - Section 508](../developer-guide/section508/).

---

## Features

### [Using Features](features/)
Learn about specific features:
- **[RAG Tool](features/RAG_TOOL_IMPLEMENTATION.md)** - Semantic document search
- **[Session Context](features/SESSION_CONTEXT_IMPLEMENTATION.md)** - Conversation memory
- **[Context Settings](features/CONTEXT_SETTINGS.md)** - Configure message history
- **[Error Handling](features/ERROR_HANDLING_FIX.md)** - Error management

---

## Common Tasks

### Execute a Workflow
```bash
1. /workflow list                           # See available workflows
2. Switch to Flo agent
3. run workflow 1 for ABC Corp on property 12345
4. Wait for completion
5. /task list                               # See any tasks created
6. /task claim <task_id>                    # Claim task
7. /task submit <task_id> approve           # Submit decision
```

### Use Section 508 Mode
```bash
1. /settings 508 on                         # Enable accessibility mode
2. Enjoy larger text and better contrast
3. Use audio playback for responses
4. /settings 508 off                        # Disable when done
```

### Search Documents
```bash
1. Upload PDFs to Document Library
2. Ask questions about uploaded documents
3. Agent uses RAG tool for semantic search
4. Get accurate answers with sources
```

---

## Getting Help

### In the App
- Type `/help` for available commands
- Type `/context` to see current settings
- Type `/agents` to list available agents

### Documentation
- See **[Commands Reference](COMMANDS.md)** for all commands
- See **[Troubleshooting](TROUBLESHOOTING.md)** for common issues
- Check topic-specific guides in subdirectories above

---

**For Developers**: See [Developer Guide](../developer-guide/README.md) for technical documentation.

**Back to**: [Documentation Index](../README.md)
