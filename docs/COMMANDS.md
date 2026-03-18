# Command System

## Overview

The BeeAI RealtyIQ Agent supports text-based commands for full keyboard and screen-reader accessibility (508 compliance). All UI functionality can be accessed via text commands in the chat prompt, making the system fully accessible to users who rely on keyboard navigation or assistive technologies.

## Command Types

### Slash Commands (/)

Slash commands begin with `/` and provide system functionality:

```
/help
/agent list
/card create
```

### @Agent Mentions

@ mentions route a single message to a specific agent without changing your default:

```
@library search for documents about real estate
@sam check if entity XYZ is excluded
```

## Available Commands

### General Commands

#### `/help`
Display list of all available commands.

**Usage:**
```
/help
```

**Example Output:**
```
Available Commands:

General:
  /help - Show this help message
  /version - Show application version
...
```

#### `/version`
Display the application version.

**Usage:**
```
/version
```

**Example Output:**
```
BeeAI RealtyIQ Agent v1.0.0
```

---

### Agent Management

#### `/agent`
Show the currently active agent.

**Usage:**
```
/agent
```

**Example Output:**
```
Current agent: 🏢 GRES Agent
```

#### `/agent list`
List all available agents with descriptions.

**Usage:**
```
/agent list
```

**Example Output:**
```
Available agents:
(*) 🏢 gres - GSA Real Estate Sales (GRES) Auction assistant - DEFAULT agent
    🚫 sam - SAM.gov Exclusions Agent
    🔐 idv - Identity Verification
    📚 library - Document library management and semantic search assistant
```

Note: The `(*)` indicates the currently selected agent.

#### `/agent <name>`
Switch to a different agent.

**Usage:**
```
/agent library
/agent sam
/agent idv
```

**Example Output:**
```
Switched to: 📚 Library Agent
```

**Available Agents:**
- `gres` - GRES Real Estate Agent
- `sam` - SAM.gov Exclusions Agent
- `idv` - Identity Verification Agent
- `library` - Library/Document Agent

#### `/agent tools`
Show tools available for the current agent.

**Usage:**
```
/agent tools
```

**Example Output:**
```
Tools for library:
  - search_documents: Search indexed PDF documents using semantic similarity...
  - reindex_all_documents: Rebuild the FAISS index from all PDF documents...
  - list_documents: List all PDF documents in the library...
```

---

### Model Selection

#### `/model`
Show the currently active model.

**Usage:**
```
/model
```

**Example Output:**
```
Current model: claude-3-5-sonnet
```

#### `/model <name>`
Switch to a different model.

**Usage:**
```
/model claude-3-5-opus
/model claude-3-haiku
```

**Available Models:**
- `claude-3-5-sonnet` (default)
- `claude-3-5-opus`
- `claude-3-haiku`

---

### Card Management

#### `/card list`
List all assistant cards.

**Usage:**
```
/card list
```

**Example Output:**
```
Available cards:
⭐   #1 - Property Search (gres)
     #2 - Exclusion Check (sam)
⭐   #3 - Document Search (library)
```

Note: ⭐ indicates favorite cards.

#### `/card list <number>`
Show details of a specific card.

**Usage:**
```
/card list 1
```

**Example Output:**
```
Card #1: Property Search
Agent: gres
Description: Search for properties in Kansas
Favorite: Yes
Created: 2024-02-17 14:30
Prompt: List all properties in Kansas with auction type classic
```

#### `/card <number>`
Execute a card by its ID.

**Usage:**
```
/card 1
```

This will execute the card's prompt as if you typed it directly.

#### `/card create`
Create a new empty card.

**Usage:**
```
/card create
```

**Example Output:**
```
Created card #4

Use '/card update 4 <field> <value>' to configure:
  - name <value>
  - description <value>
  - prompt <value>
  - agent <gres|sam|idv|library>
  - favorite <true|false>
```

#### `/card update <id> <field> <value>`
Update a card field.

**Usage:**
```
/card update 4 name Property Analyzer
/card update 4 description Analyze properties in a specific state
/card update 4 prompt List properties in Kansas
/card update 4 agent gres
/card update 4 favorite true
```

**Updatable Fields:**
- `name` - Card name
- `description` - Card description
- `prompt` - Card prompt text
- `agent` - Associated agent (gres, sam, idv, library, all)
- `favorite` - Favorite status (true/false)

#### `/card delete <number>`
Delete a card by its ID.

**Usage:**
```
/card delete 4
```

**Example Output:**
```
Deleted card #4: Property Analyzer
```

---

### Session Context

#### `/context`
Show the current session's message history.

**Usage:**
```
/context
```

**Example Output:**
```
Session context (last 5 messages):

14:30 👤 List properties in Kansas
14:31 🤖 Here are the properties in Kansas...
14:32 👤 Show details for property 123
14:33 🤖 Property #123 details...
```

#### `/context clear`
Clear all messages from the current session.

**Usage:**
```
/context clear
```

**Example Output:**
```
Cleared 10 messages from session context.
```

**Warning:** This action cannot be undone.

---

### Document Management

#### `/document list [pattern]`
List all PDF documents in the library.

**Usage:**
```
/document list
/document list contract
```

**Example Output:**
```
📁 Document Library (12 documents)

  📄 GRES_User_Guide.pdf
     Size: 2.5MB | Modified: 2024-02-15
  📄 Contract_Template.pdf
     Size: 0.8MB | Modified: 2024-02-10
```

#### `/document search <query> [top_k]`
Search documents using semantic similarity.

**Usage:**
```
/document search bidding requirements
/document search auction process 3
```

**Example Output:**
```
🔍 Search Results for: 'bidding requirements'
Found 3 results from 12 documents

1. GRES_User_Guide.pdf (score: 0.92)
   Bidding requirements include registration, deposit, and verification...

2. Auction_Rules.pdf (score: 0.87)
   All bidders must meet the following requirements...
```

#### `/document info <filename>`
Get detailed information about a specific document.

**Usage:**
```
/document info GRES_User_Guide.pdf
```

**Example Output:**
```
📄 Document Information: GRES_User_Guide.pdf

Path: 2024/02/GRES_User_Guide.pdf
Size: 2.5MB (2,621,440 bytes)
Pages: 45
Created: 2024-02-15
Modified: 2024-02-15

Index Status: ✓ Indexed
Indexed Chunks: 89
```

#### `/document reindex`
Rebuild the search index from all PDF documents.

**Usage:**
```
/document reindex
```

**Example Output:**
```
🔄 Reindex Complete

Documents Found: 12
Documents Indexed: 12
Total Chunks Created: 456
```

#### `/document stats`
Show comprehensive library and index statistics.

**Usage:**
```
/document stats
```

**Example Output:**
```
📊 Library Statistics

Library:
  Total Documents: 12
  Total Size: 45.2MB
  Path: /media/documents

Search Index:
  Status: ✓ Exists
  Indexed Documents: 12
  Total Chunks: 456
  Index Size: 1.2MB
  Model: sentence-transformers/all-MiniLM-L6-v2

Coverage:
  Documents Not Indexed: 0
  Index Coverage: 100.0%
```

---

### Prompt Management

#### `/prompt list`
List all saved prompts for quick reuse.

**Usage:**
```
/prompt list
```

**Example Output:**
```
📝 Saved Prompts (3 total)

  • daily-report
    Generate a daily summary report of all activity...

  • search-contracts
    Search for all active contracts in the GRES system...

  • verify-identity
    Verify the identity of a user with the following...

Use '/prompt <name>' to execute a saved prompt
```

#### `/prompt save <name> <text>`
Save a prompt for future reuse.

**Usage:**
```
/prompt save daily-report Generate a daily summary report
/prompt save search-query Find all properties in Chicago
```

**Example Output:**
```
✓ Prompt 'daily-report' saved

Use '/prompt daily-report' to execute it
```

#### `/prompt <name>`
Execute a saved prompt.

**Usage:**
```
/prompt daily-report
/prompt search-query
```

**Notes:**
- The saved prompt will be executed as if you typed it
- Works with the currently selected agent
- Prompts are stored per-session

#### `/prompt delete <name>`
Delete a saved prompt.

**Usage:**
```
/prompt delete daily-report
```

**Example Output:**
```
✓ Prompt 'daily-report' deleted
```

---

### Diagrams

#### `/diagram list`
List all available system architecture diagrams.

**Usage:**
```
/diagram list
```

**Example Output:**
```
📊 Available Diagrams (1 total)

  • realtyIQ

Use '/diagram <name>' to view a diagram
```

#### `/diagram <name>`
View a specific system diagram in a new browser tab.

**Usage:**
```
/diagram realtyIQ
```

**Example Output:**
```
Opening diagram: realtyIQ
```

**Notes:**
- Opens the diagram in a new browser tab using the draw.io viewer
- Interactive diagram with zoom and navigation controls
- Diagrams are stored in the `/diagrams` folder as `.drawio` files

---

### System Information

#### `/metrics`
Display comprehensive dashboard metrics including service health status.

**Usage:**
```
/metrics
```

**Example Output:**
```
📊 Dashboard Metrics

═══ Service Health ═══
Overall Status: ✓ All Systems Operational
BidHom API: ✓ 10ms
Piper TTS: ✓ 15ms
Redis Cache: ✓ 5ms
PostgreSQL: ✓ 2ms

═══ Key Metrics ═══
Sessions: 5
Total Queries (User): 23
Total Tokens: 4,521
Documents Uploaded: 3 (2.45MB)

═══ Performance ═══
Total Messages: 46
User Messages: 23
Assistant Responses: 23
Average Response Time: 2.34s
Fastest Response: 0.85s
Slowest Response: 5.67s
Total Elapsed Time: 53.82s

═══ User Satisfaction ═══
Satisfaction Rate: 87.5%
Positive Feedback: 👍 14
Negative Feedback: 👎 2
Total Rated: 16
Unrated Responses: 7

═══ System Info ═══
Total Cards: 8
Favorite Cards: 3
Total Documents: 3
Document Storage: 2.45MB
```

**Service Status Indicators:**
- `✓` = Healthy (service operational)
- `✗` = Unhealthy (service down or error)
- `○` = Disabled (service not enabled)
- `?` = Unknown (status cannot be determined)

#### `/settings`
Show current user preferences.

**Usage:**
```
/settings
```

**Example Output:**
```
Current Settings:
  Agent: gres
  Model: claude-3-5-sonnet
  Section 508 Mode: disabled (from environment)

To update:
  /settings agent <value>
  /settings model <value>
  /settings 508 <on|off>
```

#### `/settings <setting> <value>`
Update a user preference.

**Usage:**
```
/settings agent library
/settings model claude-3-haiku
/settings 508 on
```

**Available Settings:**
- `agent` - Default agent
- `model` - Default model
- `508` - Section 508 accessibility mode (on/off)

**Section 508 Mode:**
When enabled, the UI applies enhanced accessibility features including:
- Larger text and increased line height
- Enhanced focus indicators
- Minimum touch target sizes (44x44px)
- Screen reader optimizations
- High contrast mode support

The default value is set via the `SECTION_508_MODE` environment variable. Users can override this with `/settings 508 <on|off>`.

---

## @Agent Mentions

Route a single message to a specific agent without changing your default agent preference.

### Syntax

```
@<agent> <message>
```

### Examples

```
@library search for documents about real estate
```

Routes "search for documents about real estate" to the Library agent.

```
@sam check if entity XYZ is excluded
```

Routes "check if entity XYZ is excluded" to the SAM.gov agent.

```
@idv verify user with drivers license ABC123
```

Routes verification request to the Identity Verification agent.

### Available Agents for @ Mentions

- `@gres` - GRES Real Estate Agent
- `@sam` - SAM.gov Exclusions Agent
- `@idv` - Identity Verification Agent
- `@library` - Library/Document Agent
- `@508` - Section 508 Accessibility Agent

### Behavior

- The mentioned agent processes **only that message**
- After processing, the system reverts to your default agent
- Your default agent preference is **not changed**
- Useful for one-off requests to specialized agents

---

## Accessibility Features

### 508 Compliance

All commands support:

✓ **Keyboard-only navigation** - No mouse required  
✓ **Screen reader support** - All responses are plain text  
✓ **WCAG 2.1 AA compliance** - Meets accessibility standards  
✓ **Focus management** - Prompt input maintains focus  
✓ **Clear error messages** - Descriptive errors for invalid commands  
✓ **In-context help** - `/help` provides guidance without leaving chat  

### Screen Reader Usage

Commands are announced as "Command response" with the command name for context. For example, `/help` is announced as "Command response: help".

### Keyboard Shortcuts

- **Type command** - Start with `/` to enter a command
- **Tab navigation** - Navigate through UI elements
- **Enter** - Submit command
- **Escape** - Clear input field (standard browser behavior)

---

## Examples and Use Cases

### Quick Agent Switching

Instead of clicking through UI menus:
```
/agent library
/agent tools
```

### Managing Cards via Keyboard

Create and configure a card entirely via commands:
```
/card create
/card update 5 name Document Finder
/card update 5 agent library
/card update 5 prompt search documents about contracts
/card update 5 favorite true
/card 5
```

### One-off Agent Queries

Ask Library agent a question without switching:
```
@library what documents do we have about real estate?
```

Your default agent remains unchanged for the next message.

### Session Management

Review and clean up your conversation:
```
/context
/context clear
```

### Checking System Status

```
/metrics
/version
/settings
```

---

## Error Handling

### Unknown Commands

```
/unknown
```

**Output:**
```
Unknown command: /unknown

Type /help to see available commands.
```

### Invalid Arguments

```
/agent invalidagent
```

**Output:**
```
Error: Unknown agent 'invalidagent'

Available agents: gres, sam, idv, library
```

### Invalid @Mentions

```
@invalidagent test
```

**Output:**
```
Error: Unknown agent @invalidagent

Available agents: gres, sam, idv, library
```

---

## Command History

All commands and their responses are stored in your chat history, just like regular messages. This allows you to:

- Review what commands you've run
- See the results of previous commands
- Export commands as part of session history
- Search through command results

---

## Best Practices

### For Screen Reader Users

1. Use `/help` to hear all available commands
2. Commands provide plain text responses that are fully readable
3. Use `/agent list` to hear all available agents
4. Use `/card list` to hear all your saved cards

### For Keyboard-Only Users

1. All functionality accessible via commands
2. No mouse clicks required
3. Tab through interface or use commands directly
4. Use `/agent` and `/card` commands for quick navigation

### For Power Users

1. Create frequently-used prompts as cards
2. Use @mentions for quick agent switching
3. Use `/context` to review conversation
4. Use `/settings` to set preferred defaults

---

## Technical Details

### Command Storage

- Commands are stored as `ChatMessage` objects with `role=user`
- Responses are stored with `role=assistant`
- Commands have `metadata.command` field indicating the command type
- All commands are fully auditable in the database

### Command Processing

1. User types command in chat input
2. Backend parses command using regex
3. Command dispatcher routes to appropriate handler
4. Handler executes and returns formatted response
5. Response stored in database and returned to user
6. Frontend displays response with command badge

### Performance

- Commands execute synchronously (no agent processing)
- Typical response time: < 100ms
- No LLM calls for command execution (except `/card <number>`)
- Minimal database queries per command

---

## Support

For issues or questions about commands:

1. Type `/help` for quick reference
2. Check this documentation
3. Contact support if commands aren't working as expected

---

## Version History

- **v1.0.0** (2024-02) - Initial command system release
  - Slash commands
  - @Agent mentions
  - Full 508 compliance
  - 8 command categories
  - Screen reader support
