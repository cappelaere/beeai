# Agent Creation Guidelines

Guidelines for creating effective AI agents in RealtyIQ.

---

## Agent Design Principles

### 1. Single Responsibility

Each agent should have **one clear domain of expertise**:

**Good Examples:**
- SAM Agent: SAM.gov exclusions only
- OFAC Agent: Sanctions screening only
- GRES Agent: Property and auction data only

**Bad Examples:**
- "Compliance Agent" that handles SAM, OFAC, identity verification, and credit checks
- "Data Agent" that handles properties, documents, and workflows
- "Everything Agent" with all tools

**Why:** Focused agents produce better results, are easier to maintain, and have clearer SKILLS.md documentation.

---

### 2. Tool Selection

Include only tools relevant to the agent's domain:

**GRES Agent (Good):**
```
Tools: [
  list_properties,
  get_property_detail,
  list_agents_summary,
  auction_dashboard,
  auction_bidders,
  bid_history,
  property_count_summary,
  ThinkTool
]
```

**GRES Agent (Bad - too many tools):**
```
Tools: [
  list_properties,
  sam_check,           # Not GRES domain
  ofac_screen,         # Not GRES domain
  upload_document,     # Not GRES domain
  execute_workflow,    # Not GRES domain
  ... (all 50 tools)
]
```

**Guideline:** 4-10 tools per agent is optimal. More tools create confusion.

---

### 3. Clear Instructions

Agent configuration should have explicit instructions:

**Template:**
```python
AgentConfig(
    name="[Agent Name]",
    description="[One sentence describing purpose]",
    instructions=(
        "You are [Agent Name]. "
        "[Domain expertise description]. "
        "Your primary responsibilities: [List 2-4 key tasks]. "
        "Use available tools to [specific guidance]. "
        "When users ask about [out-of-scope topic], "
        "suggest they ask [relevant agent]. "
        "Be [tone: professional/friendly/concise]. "
    ),
    tools=[...]
)
```

**Example (SAM Agent):**
```python
instructions=(
    "You are the SAM.gov Exclusions Agent. "
    "You specialize in checking federal contract exclusions. "
    "Your primary responsibilities: "
    "1) Search SAM database for excluded entities "
    "2) Explain exclusion details and reasons "
    "3) Provide compliance guidance. "
    "Use fuzzy matching for name searches. "
    "When users ask about OFAC sanctions, suggest the OFAC agent. "
    "Be thorough and precise with compliance information."
)
```

---

### 4. Conversation Tone

Match tone to agent domain:

**Professional & Formal:**
- Compliance agents (SAM, OFAC)
- Legal/regulatory agents
- Example: "Based on the SAM.gov database, the entity is not currently excluded."

**Helpful & Friendly:**
- General query agents (GRES)
- Library/document agents
- Example: "I found 12 properties in Texas! Here's what I discovered..."

**Technical & Concise:**
- Workflow orchestration (Flo)
- System administration agents
- Example: "Workflow RUN_123 initiated. Status: IN_PROGRESS. 3 steps remaining."

---

## SKILLS.md Structure

### Recommended Sections

```markdown
# [Agent Name]

Brief overview of agent's purpose (2-3 sentences)

---

## Core Capabilities

What the agent can do:
- Capability 1
- Capability 2
- Capability 3

---

## Available Tools

### Web Search (DuckDuckGo)

**Purpose**: Search the internet for real-time information, current events, and external research

**Tool**: `DuckDuckGoSearchTool` from `beeai_framework.tools.search.duckduckgo`

**When to Use:**
- Current market trends, property values, or real estate news
- Federal/state regulations and policy updates
- Company background checks and research
- General knowledge requiring current web sources
- Verification of external information

**Configuration:**
```python
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

# Standard configuration (Research Agent)
DuckDuckGoSearchTool(max_results=10, safe_search="STRICT")

# Limited results (Secondary use in other agents)
DuckDuckGoSearchTool(max_results=5, safe_search="STRICT")
```

**Best Practices:**
- Always cite sources with URLs
- Be specific with search queries (include dates, locations)
- Use quotes for exact phrases
- Acknowledge when information may be outdated
- Verify critical information from multiple sources

**Agents with Web Search:**
- **Research Agent**: Primary web search specialist (10 results)
- **Flo Agent**: Workflow research and best practices (5 results)

**Limitations:**
- Cannot access paywalled content
- Limited to public web sources
- May encounter rate limiting with excessive queries
- Safe search filtering enabled

**Example Usage:**
```python
# In agent instructions:
"When users ask about current market conditions, use DuckDuckGo "
"to search for recent reports and news. Always provide source URLs."

# In SKILLS.md:
"Search 'Washington DC commercial property values 2026' to find "
"current market information and cite reputable sources."
```

---

### Tool 1: tool_name

**Purpose**: What this tool does

**Parameters:**
- param1 (type): Description
- param2 (type, optional): Description

**Example Usage:**
User: "Example query"
Agent: [Uses tool_name with params]
→ Result: Expected output

### Tool 2: tool_name

[Repeat for all tools]

---

## Example Queries

What users can ask:
- "Query pattern 1"
- "Query pattern 2"
- "Query pattern 3"

---

## Best Practices

How to get the best results:
- Tip 1
- Tip 2
- Tip 3

---

## Limitations

What the agent cannot do:
- Out-of-scope task 1 → Suggest [Other Agent]
- Out-of-scope task 2 → Suggest [Action]

---

## Related Agents

When to use other agents:
- For [task type], use [Agent Name]
- For [task type], use [Agent Name]
```

---

## Common Patterns

### Pattern 1: Query Agent

**Use for:** Database queries and searches

**Example:** GRES Agent, SAM Agent, OFAC Agent

**Characteristics:**
- Primarily read-only operations
- Tool-heavy (multiple query tools)
- Handles filtering, sorting, pagination
- Returns structured data

**Instructions Template:**
```
"You are [Name]. You help users query [data source]. 
Use tools to search and retrieve information. 
Format results clearly with tables or lists. 
When data is not found, suggest alternative searches."
```

---

### Pattern 2: Orchestration Agent

**Use for:** Multi-step processes and workflows

**Example:** Flo Agent, Bidder Verification Agent

**Characteristics:**
- Coordinates other agents or tools
- Manages state across steps
- Creates and tracks tasks
- Handles decision logic

**Instructions Template:**
```
"You are [Name]. You orchestrate [process type]. 
Guide users through multi-step workflows. 
Create tasks when human review is needed. 
Track progress and provide status updates. 
Ensure all steps complete successfully."
```

---

### Pattern 3: Analysis Agent

**Use for:** Data analysis and insights

**Example:** GRES Agent (analytics mode)

**Characteristics:**
- Aggregates data from multiple sources
- Performs calculations and comparisons
- Generates insights and recommendations
- Creates visualizations (tables, charts)

**Instructions Template:**
```
"You are [Name]. You analyze [data type] to provide insights. 
Use multiple tools to gather comprehensive data. 
Calculate metrics and identify trends. 
Present findings in clear, actionable formats. 
Highlight key takeaways and recommendations."
```

---

### Pattern 4: Verification Agent

**Use for:** Compliance and validation

**Example:** SAM Agent, OFAC Agent, Identity Verification Agent

**Characteristics:**
- Binary decisions (pass/fail)
- Regulatory compliance focus
- Detailed audit trails
- High precision required

**Instructions Template:**
```
"You are [Name]. You verify [compliance requirement]. 
Check [data source] thoroughly. 
Clearly state verification results (PASS/FAIL). 
Explain reasons for failures. 
Document all checks for audit purposes. 
Err on the side of caution."
```

---

### Pattern 5: Document Agent

**Use for:** Document management and search

**Example:** Library Agent

**Characteristics:**
- Document upload and storage
- Semantic search capabilities
- Question answering over documents
- Content summarization

**Instructions Template:**
```
"You are [Name]. You help users find information in documents. 
Use RAG search for semantic queries. 
Cite sources with page numbers. 
Summarize long documents. 
Suggest related content. 
Handle multiple document formats."
```

---

## Tool Integration

### Tool Definition Format

```python
from beeai_framework.tools import Tool

class CustomTool(Tool):
    name = "tool_name"
    description = "Clear description of what tool does"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description,
            parameters={
                "param1": {
                    "type": "string",
                    "description": "Parameter description",
                    "required": True
                },
                "param2": {
                    "type": "number",
                    "description": "Optional parameter",
                    "required": False
                }
            }
        )
    
    def execute(self, param1: str, param2: int = None):
        # Tool logic here
        result = perform_operation(param1, param2)
        return result
```

---

### Tool Best Practices

1. **Clear Naming**: Use verb_noun format (`list_properties`, `get_detail`, `check_status`)
2. **Good Descriptions**: Explain what the tool returns, not just what it does
3. **Parameter Validation**: Validate inputs before processing
4. **Error Handling**: Return meaningful error messages
5. **Consistent Format**: Use same response structure across similar tools
6. **Documentation**: Include examples in SKILLS.md

---

## Testing New Agents

### Test Checklist

- [ ] Agent appears in agent selector
- [ ] Can switch to agent in chat
- [ ] @mention works correctly
- [ ] Tools execute successfully
- [ ] Error handling works
- [ ] SKILLS.md is complete and accurate
- [ ] Example queries work as documented
- [ ] Agent stays in domain (doesn't overreach)
- [ ] Handoffs to other agents are smooth
- [ ] Langfuse traces show tool calls

---

### Test Queries

For each new agent, test:

**1. Basic Capability:**
```
"What can you do?"
"Help me with [domain task]"
```

**2. Core Tools:**
```
[Query that requires primary tool]
[Query that requires secondary tool]
```

**3. Error Handling:**
```
[Invalid query]
[Out-of-scope query]
[Query with missing data]
```

**4. Context Awareness:**
```
[Initial query]
"Tell me more about that"
"What about the second one?"
```

**5. Edge Cases:**
```
[Ambiguous query]
[Very broad query]
[Very specific query]
```

---

## Common Mistakes

### Mistake 1: Agent Too Broad

**Problem:**
```python
name="Compliance & Analysis Agent"
tools=[sam_tools, ofac_tools, gres_tools, library_tools]  # 25 tools!
```

**Solution:**
Create separate specialized agents:
- SAM Agent (SAM tools only)
- OFAC Agent (OFAC tools only)
- GRES Agent (GRES tools only)

---

### Mistake 2: Unclear Instructions

**Problem:**
```python
instructions="You are a helpful assistant."
```

**Solution:**
```python
instructions=(
    "You are the SAM.gov Exclusions Agent. "
    "You check if entities are excluded from federal contracts. "
    "Search the SAM database and explain findings clearly. "
    "For OFAC questions, refer users to the OFAC agent."
)
```

---

### Mistake 3: Missing Error Guidance

**Problem:**
Agent doesn't know what to do when tools fail.

**Solution:**
```python
instructions=(
    "... "
    "If a tool fails, try alternative approaches. "
    "If data is not found, suggest related searches. "
    "Always provide helpful next steps."
)
```

---

### Mistake 4: No Handoff Strategy

**Problem:**
Agent tries to answer out-of-scope questions poorly.

**Solution:**
```python
instructions=(
    "... "
    "For SAM exclusion checks, suggest @sam agent. "
    "For OFAC sanctions, suggest @ofac agent. "
    "For workflow orchestration, suggest Flo agent."
)
```

---

## Agent Studio Usage

### Creating Agent via UI

**Step-by-Step:**

1. Navigate to Agent Collection
2. Click "Create New Agent" (admin only)
3. Fill in form:
   - **Name**: Human-readable name
   - **ID**: Lowercase with underscores (e.g., `market_analysis`)
   - **Icon**: Single emoji representing domain
   - **Description**: One sentence purpose
   - **Skills Prompt**: Detailed requirements for SKILLS.md generation

4. Submit form
5. System generates:
   - Agent directory: `agents/[id]/`
   - Agent config: `agents/[id]/agent.py`
   - Skills doc: `agents/[id]/SKILLS.md`
   - Registry entry in `agents.yaml`

6. Review generated SKILLS.md
7. Test agent in chat
8. Iterate on prompt if needed

---

### Skills Generation Prompt Template

```
Create a [Domain] agent for RealtyIQ.

CONTEXT:
RealtyIQ is a GSA real estate auction platform. Users are real estate 
specialists, compliance officers, and analysts.

AGENT PURPOSE:
This agent should help users [specific goal].

AVAILABLE TOOLS:
- tool1: [description]
- tool2: [description]
- tool3: [description]

EXAMPLE QUERIES:
Users will ask questions like:
- "Query example 1"
- "Query example 2"
- "Query example 3"

TONE:
[Professional/Technical/Friendly]

SCOPE:
Focus on [in-scope topics]. 
For [out-of-scope topic], refer to [Other Agent].

SPECIAL REQUIREMENTS:
- [Any specific behavior]
- [Any compliance needs]
- [Any formatting preferences]
```

---

## Advanced Techniques

### Technique 1: Agent Specialization

Create sub-specialized agents for complex domains:

**Example: Break down "Property Agent":**
- **Residential Properties Agent**: Single-family, condos
- **Commercial Properties Agent**: Office, retail, industrial
- **Land Agent**: Vacant land, parcels

**When to use:**
- Domain has distinct sub-domains
- Different user personas need different expertise
- Tool sets don't overlap much

---

### Technique 2: Agent Coordination

Design agents to work together:

**Example: Verification Chain:**
```
Bidder Verification Agent:
  → Calls SAM Agent
  → Calls OFAC Agent
  → Calls Identity Verification Agent
  → Synthesizes results
```

**Implementation:**
- Primary agent has orchestration logic
- Sub-agents focus on specific checks
- Primary agent aggregates results
- Clear handoff protocol

---

### Technique 3: Context-Aware Responses

Use session context for natural conversations:

**Example:**
```
User: "Show properties in Texas"
Agent: [Returns 50 properties]

User: "Commercial only"
Agent: [References previous results, filters]
→ Uses context instead of new query

User: "Sort by price"
Agent: [Uses context, sorts in-memory]
→ Fast response without API call
```

**Implementation:**
- Agent instructions mention context usage
- Agent references "previous results"
- Efficient follow-up handling

---

### Technique 4: Progressive Disclosure

Start simple, offer more detail when needed:

**Example:**
```
User: "Properties in California"
Agent: "I found 127 properties in California.

Top 5 by price:
1. Property #445 - $4.5M - San Francisco
2. Property #443 - $3.8M - Los Angeles
...

Would you like to:
- See full list
- Filter by property type
- Sort by a different criteria
- Get details on a specific property"
```

**Pattern:** Summary first, details on request.

---

## Agent Configuration Reference

### Minimal Agent Template

```python
from pathlib import Path
from agents.base import AgentConfig
from beeai_framework.tools.think import ThinkTool

AGENT_NAME_AGENT_CONFIG = AgentConfig(
    name="Agent Name",
    description="Brief one-sentence description of agent purpose.",
    instructions=(
        "You are Agent Name. "
        "You help users with [domain]. "
        "Use available tools to [actions]. "
        "Be [tone]."
    ),
    tools=[
        ThinkTool(),
        # Add domain-specific tools
    ]
)
```

---

### With Custom Tools

```python
from tools.custom_tools import CustomTool1, CustomTool2

CUSTOM_AGENT_CONFIG = AgentConfig(
    name="Custom Agent",
    description="Specialized agent with custom tools.",
    instructions=(
        "You are Custom Agent. "
        "You specialize in [domain]. "
        "Use custom_tool1 for [purpose]. "
        "Use custom_tool2 for [purpose]. "
        "Provide [output format]."
    ),
    tools=[
        ThinkTool(),
        CustomTool1(),
        CustomTool2(),
    ]
)
```

---

### With Agent Orchestration

```python
ORCHESTRATOR_AGENT_CONFIG = AgentConfig(
    name="Orchestrator Agent",
    description="Coordinates multiple agents for complex tasks.",
    instructions=(
        "You are Orchestrator Agent. "
        "You coordinate multiple agents to complete complex workflows. "
        "For SAM checks, use the SAM agent. "
        "For OFAC checks, use the OFAC agent. "
        "Synthesize results from all agents. "
        "Present a unified report."
    ),
    tools=[
        ThinkTool(),
        # Orchestration tools
    ]
)
```

---

## Registry Management

### agents.yaml Format

```yaml
default_agent: gres

agents:
  - id: agent_id
    name: "Agent Name"
    icon: "🔧"
    description: "Agent description"
    directory: agents/agent_id
    
  - id: another_agent
    name: "Another Agent"
    icon: "📊"
    description: "Another description"
    directory: agents/another_agent
```

### Adding Agent to Registry

**Manual Method:**
```yaml
# Add to agents.yaml
  - id: new_agent
    name: "New Agent"
    icon: "🆕"
    description: "New agent description"
    directory: agents/new_agent
```

**Via Agent Studio:**
- System automatically updates registry
- Validates ID uniqueness
- Ensures proper formatting

---

## Icon Selection

Choose icons that represent the agent's domain:

**Good Icon Choices:**
- 🏠 Residential Properties
- 🏢 Commercial Properties
- 🚫 Exclusions/Prohibitions
- ⚖️ Legal/Compliance
- 📊 Analytics/Reports
- 🔍 Search/Discovery
- 🔄 Workflows/Processes
- 📚 Documents/Library
- ✅ Verification/Approval
- 🌐 International/Global

**Avoid:**
- Generic icons (📄, 📁)
- Ambiguous icons (🔥, ⭐)
- Multiple icons per agent
- Text-based icons

---

## Performance Optimization

### Efficient Tool Usage

**Good:**
```
1. Check cache first
2. Use most specific tool
3. Filter early
4. Aggregate at database level
5. Return paginated results
```

**Bad:**
```
1. Fetch all data
2. Filter in memory
3. Sort in memory
4. Return everything
5. Let LLM process large datasets
```

---

### Response Time Guidelines

**Target response times:**
- Cached queries: <100ms
- Single tool call: <2s
- Multiple tool calls: <5s
- Complex analysis: <10s
- Workflow initiation: <3s

**If slower:**
- Add pagination
- Use caching
- Optimize database queries
- Reduce tool calls
- Pre-compute aggregations

---

## Troubleshooting

### Agent Not Responding

**Check:**
1. Agent in registry (`agents.yaml`)
2. Directory exists (`agents/[id]/`)
3. `agent.py` has valid config
4. Tools are imported correctly
5. No syntax errors in configuration

### Agent Using Wrong Tools

**Fix:**
1. Review tool list in `AgentConfig`
2. Check tool descriptions are clear
3. Update agent instructions
4. Test with specific queries
5. Regenerate SKILLS.md if needed

### Agent Confused About Scope

**Fix:**
1. Clarify domain in instructions
2. Add explicit out-of-scope guidance
3. Mention other agents for handoffs
4. Provide example queries
5. Reduce number of tools

---

## Examples from RealtyIQ

### Example 1: SAM Agent

**Domain**: Federal contract exclusions  
**Tools**: SAM database search  
**Tone**: Professional, compliance-focused  
**Pattern**: Verification agent

**Key Features:**
- Binary results (excluded or not)
- Fuzzy name matching
- Clear explanations of exclusions
- Audit trail focus

**SKILLS.md Highlights:**
- Detailed tool parameters
- Example queries with expected outputs
- Best practices for name searches
- Limitations clearly stated

---

### Example 2: GRES Agent

**Domain**: Property and auction data  
**Tools**: 10 GRES API tools  
**Tone**: Helpful, analytical  
**Pattern**: Query + analysis agent

**Key Features:**
- Wide range of queries
- Data aggregation
- Business intelligence
- Flexible filtering

**SKILLS.md Highlights:**
- Extensive tool documentation
- Many example queries
- Query patterns explained
- Integration with other agents

---

### Example 3: Flo Agent

**Domain**: Workflow orchestration  
**Tools**: Workflow and task management  
**Tone**: Concise, technical  
**Pattern**: Orchestration agent

**Key Features:**
- Workflow discovery
- Execution management
- Task tracking
- Status reporting

**SKILLS.md Highlights:**
- Command reference
- Workflow lifecycle
- Task submission format
- Error recovery

---

## Checklist for New Agents

### Planning Phase

- [ ] Define agent domain and scope
- [ ] Identify target user persona
- [ ] List required tools
- [ ] Write example queries (10+)
- [ ] Define handoff strategy
- [ ] Choose appropriate icon

### Implementation Phase

- [ ] Create agent directory
- [ ] Write agent configuration
- [ ] Select and import tools
- [ ] Write or generate SKILLS.md
- [ ] Add to agents.yaml
- [ ] Configure default agent if needed

### Testing Phase

- [ ] Test basic queries
- [ ] Test tool execution
- [ ] Test error cases
- [ ] Test context awareness
- [ ] Test agent mentions (@agent)
- [ ] Test handoffs to other agents
- [ ] Verify Langfuse traces
- [ ] Check cache behavior

### Documentation Phase

- [ ] Complete SKILLS.md
- [ ] Add to Agent Collection UI
- [ ] Update user guide if needed
- [ ] Create example queries
- [ ] Document limitations

---

**Version**: 1.0  
**Last Updated**: February 21, 2026  
**Related**: [CONTEXT.md](CONTEXT.md), [USE_CASES.md](USE_CASES.md)
