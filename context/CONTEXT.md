# RealtyIQ Application Context

**Purpose:** This document provides comprehensive context about RealtyIQ for use when creating new agents, workflows, and features.

---

## Application Overview

**RealtyIQ** is an AI-powered platform for GSA Real Estate Sales (GRES) auction management, reporting, and business intelligence. The system uses specialized AI agents to help real estate specialists, analysts, and administrators query auction data, verify bidders, manage workflows, and generate insights through natural language interactions.

### Core Intent

- **Primary Goal**: Provide intelligent assistance for federal real estate auction operations
- **Key Value**: Transform complex database queries and compliance checks into simple conversations
- **Target Users**: GSA real estate specialists, auction administrators, compliance officers, and analysts
- **Approach**: Multi-agent system with specialized expertise domains

---

## Domain & Business Context

### GSA Real Estate Sales (GRES) Auctions

RealtyIQ supports the federal government's real estate disposal program:

- **Properties**: Federal buildings, land, and facilities sold at public auctions
- **Auctions**: Online bidding platform managed by GSA
- **Bidders**: Individuals and entities who register and bid on properties
- **Agents**: Real estate agents who list and manage property sales
- **Compliance**: Federal regulations including SAM.gov exclusions and OFAC sanctions

### Business Intelligence Needs

- Property analytics and trends
- Auction performance metrics
- Bidder behavior analysis
- Agent performance tracking
- Compliance screening and verification
- Market insights and forecasting

---

## Key Features

### 1. Multi-Agent System

**8 Specialized Agents:**

1. **GRES Agent** (Default)
   - Property queries and auction data
   - Business intelligence reports
   - Dashboard metrics and analytics
   - Primary agent for real estate questions

2. **SAM.gov Exclusions Agent**
   - Federal contract exclusions database
   - Check if entities/individuals are excluded
   - Compliance verification

3. **OFAC Compliance Agent**
   - Office of Foreign Assets Control (OFAC) screening
   - Sanctions list (SDN - Specially Designated Nationals)
   - International compliance checks

4. **Bidder Verification Agent**
   - Orchestrates SAM + OFAC checks
   - Comprehensive eligibility screening
   - Multi-step verification workflow

5. **Identity Verification Agent**
   - User identity verification
   - Verification record management
   - KYC (Know Your Customer) processes

6. **Library Agent**
   - Document library management
   - Semantic search with RAG (FAISS)
   - PDF analysis and question answering

7. **Flo (Workflow Agent)**
   - Workflow discovery and management
   - Task assignment and tracking
   - Process orchestration
   - Workflow research (with web search)

8. **Research Agent** (Web Search) ⭐ NEW
   - Real-time internet search via DuckDuckGo
   - Market trends and property valuations
   - Company background checks
   - Regulations and compliance research
   - Current events and news

8. **Section 508 Agent**
   - Accessibility compliance assistant
   - Text-to-speech capabilities
   - WCAG 2.1 Level AA guidance

### 2. Workflow System

**Dynamic Workflows:** BeeAI Framework-based workflows for complex, multi-step processes

**Key Workflows:**
- **Bidder Onboarding** - Complete bidder verification including SAM, OFAC, and identity checks
- **Property Analysis** - Detailed property evaluation and reporting
- **Compliance Screening** - Automated verification workflows

**Workflow Features:**
- Human-in-the-loop task system
- Real-time progress tracking
- State management and persistence
- Role-based task assignment

### 3. Chat Interface

- **Natural Language Processing**: Ask questions in plain English
- **Session Management**: Multiple conversation threads
- **Session Context**: Agent remembers last 20 messages for follow-ups
- **Voice Input**: Web Speech API for dictation
- **Markdown Rendering**: Rich formatted responses
- **Code Highlighting**: Syntax highlighting for SQL, Python, etc.

### 4. Tool System

**16 API Tools for GRES Data:**
- `list_properties` - Search and filter properties
- `get_property_detail` - Detailed property information
- `list_agents_summary` - Real estate agent performance
- `auction_dashboard` - Auction metrics and KPIs
- `auction_bidders` - Bidder lists and statistics
- `bid_history` - Bidding patterns and history
- `property_count_summary` - Property counts by type/status
- And 9 more specialized tools

**Additional Tool Categories:**
- Workflow tools (execute, list, manage)
- Document tools (upload, search, RAG)
- Compliance tools (SAM, OFAC verification)
- System tools (think, search, analyze)

### 5. Document Library

- **Upload PDFs**: Store and manage auction documents
- **Semantic Search**: RAG-based document question answering
- **FAISS Vector Store**: Efficient similarity search
- **Metadata Management**: Track document ownership and dates

### 6. Observability & Monitoring

- **Langfuse Integration**: Complete trace visibility
- **Tool Tracking**: All tool calls logged with inputs/outputs
- **Prometheus Metrics**: Performance monitoring
- **Health Checks**: Service status for API, Redis, TTS
- **Logging**: Timestamped log files

### 7. Accessibility (Section 508)

- **Toggle Mode**: Enable/disable accessibility features
- **Enhanced UI**: Larger fonts, better contrast
- **Text-to-Speech**: On-prem Piper TTS with audio controls
- **Keyboard Navigation**: Full keyboard accessibility
- **WCAG 2.1 Level AA**: Compliant implementation

---

## Use Cases & Examples

### Use Case 1: Property Research

**Scenario:** Real estate specialist needs property information

**Example Conversation:**
```
User: "Show me all commercial properties in Texas over $1M"
GRES Agent: [Uses list_properties tool, returns filtered results]

User: "Tell me more about the first one"
GRES Agent: [Uses get_property_detail with context from previous message]

User: "What's the bidding history?"
GRES Agent: [Uses bid_history tool for that property]
```

### Use Case 2: Bidder Verification

**Scenario:** Administrator needs to verify a new bidder

**Example Workflow:**
```
User: "Run bidder verification for ABC Construction Corp"
Flo Agent: [Initiates bidder_onboarding workflow]
  → Step 1: SAM.gov exclusions check
  → Step 2: OFAC sanctions screening  
  → Step 3: Identity verification
  → Creates human review task if issues found
  
User: "/task claim TASK123"
User: "/task submit TASK123 approve"
```

### Use Case 3: Business Intelligence

**Scenario:** Analyst needs auction performance report

**Example Query:**
```
User: "Generate an executive summary of Q1 2026 auction performance"
GRES Agent: [Uses multiple tools]
  → auction_dashboard (overall metrics)
  → property_count_summary (inventory)
  → auction_total_bids (bidding activity)
  → Synthesizes comprehensive report
```

### Use Case 4: Compliance Screening

**Scenario:** Check if bidder is eligible

**Example Commands:**
```
User: "@sam check XYZ Corporation"
SAM Agent: [Queries SAM.gov exclusions database]

User: "@ofac screen John Smith, DOB 1980-05-15"
OFAC Agent: [Checks OFAC SDN list with fuzzy matching]

User: "@bidder_verification run full check for XYZ Corp"
Bidder Verification Agent: [Orchestrates both SAM + OFAC checks]
```

### Use Case 5: Document Search

**Scenario:** Find information in uploaded property documents

**Example Interaction:**
```
User: "Upload property_appraisal.pdf"
[Uploads via Documents section]

User: "@library what is the estimated market value?"
Library Agent: [Uses RAG tool to search document, returns relevant excerpt]

User: "@library what were the inspection findings?"
Library Agent: [Semantic search for inspection-related content]
```

### Use Case 6: Workflow Management

**Scenario:** Track and manage active workflows

**Example Commands:**
```
User: "/workflow list"
Flo: [Shows 7 available workflows]

User: "/workflow runs"
Flo: [Shows user's workflow runs with status]

User: "/task list"
Flo: [Shows pending tasks requiring attention]
```

---

## Technical Architecture

### Backend Stack

- **Framework**: Django 4.x + BeeAI Framework
- **Server**: Uvicorn (ASGI) for WebSocket support
- **Database**: 
  - PostgreSQL (GRES auction data)
  - SQLite (SAM exclusions - 139K records)
  - SQLite (OFAC SDN list - 18K records)
- **Cache**: Redis 7+ (dual database architecture)
- **LLM**: Anthropic Claude Sonnet 4.5
- **Search**: FAISS vector store for RAG

### Frontend Stack

- **UI Framework**: Bootstrap 5.3
- **JavaScript**: Vanilla JS (no frameworks)
- **Markdown**: Marked.js with syntax highlighting
- **Voice**: Web Speech API
- **Real-time**: Server-Sent Events (SSE) for workflows

### Integration Points

- **BidHom API**: Django REST API at `http://localhost:8000`
- **Piper TTS**: Text-to-speech service at `http://localhost:5000`
- **Langfuse**: Cloud observability at `https://us.cloud.langfuse.com`
- **Prometheus**: Metrics scraping on `/metrics/`
- **MCP Server**: Tool exposure via Model Context Protocol

---

## Data Model

### Core Entities

1. **Properties**
   - Federal real estate assets
   - Metadata: type, location, size, condition
   - Status: active, sold, withdrawn
   - Related auctions and bids

2. **Auctions**
   - Bidding events for properties
   - Timing: start date, end date, duration
   - Results: winning bid, total bids, participants
   - Types: online, sealed bid, open outcry

3. **Bidders**
   - Registered participants
   - Verification status (SAM, OFAC, identity)
   - Bid history and win rate
   - Compliance flags

4. **Agents** (Real Estate)
   - Licensed real estate professionals
   - Property listings and sales
   - Performance metrics
   - Commission tracking

5. **Bids**
   - Individual bid submissions
   - Timestamp, amount, bidder
   - Status: active, winning, outbid
   - History and patterns

6. **Documents**
   - Uploaded PDFs (appraisals, inspections, etc.)
   - FAISS vector embeddings for search
   - Metadata: owner, upload date, category

---

## Common Patterns

### Agent Creation Pattern

When creating new agents, consider:

**Domain Specialization:**
- What specific domain expertise is needed?
- What data sources will the agent access?
- What compliance or regulatory requirements apply?

**Tools & Capabilities:**
- Which API tools are most relevant?
- Does the agent need custom tools?
- Should it orchestrate other agents?

**User Interaction Style:**
- Technical vs. non-technical audience
- Report-focused vs. query-focused
- Proactive vs. reactive responses

**Example Use Cases:**
- Contract analysis for legal compliance
- Environmental assessment for property evaluation
- Financial analysis for investment decisions
- Market research for pricing strategy

### Workflow Creation Pattern

When designing workflows, consider:

**Process Steps:**
- What are the distinct stages?
- Which steps require human review?
- What are the decision points?

**Agent Orchestration:**
- Which agents participate in each step?
- How do agents hand off work?
- What data flows between steps?

**Task Management:**
- What tasks require human intervention?
- Who can claim and submit tasks?
- What are the approval criteria?

**Example Workflows:**
- Property listing approval process
- Multi-stage bidder verification
- Compliance audit workflow
- Document review and approval

---

## Feature Examples

### Favorite Cards (Quick Prompts)

Pre-configured prompts for common queries:
- "List active auctions in California"
- "Show top performing agents this quarter"
- "Generate property inventory summary"
- "Check bidder compliance status"

### Command System

Text-based commands for accessibility:
```bash
/workflow list              # List available workflows
/workflow runs              # View workflow runs
/task claim TASK123         # Claim a task
/task submit TASK123 approve # Submit task decision
/agent sam                  # Switch to SAM agent
@ofac screen John Smith     # One-time agent mention
/settings 508 on            # Enable accessibility mode
/context                    # Show session context settings
```

### Dashboard Metrics

Real-time KPIs:
- Active auctions count
- Total properties listed
- Pending tasks requiring review
- System health status
- Redis cache hit rate
- Recent workflow runs

---

## Integration Scenarios

### Scenario 1: New Data Source

**Adding a new compliance database:**

1. Create specialized agent (e.g., "EPA Compliance Agent")
2. Define tools for querying the database
3. Create SKILLS.md with domain expertise
4. Add to registry in `agents.yaml`
5. Optional: Create verification workflow

### Scenario 2: New Workflow Type

**Adding property inspection workflow:**

1. Define workflow in `workflows/property_inspection/`
2. Create `metadata.yaml` with workflow description
3. Implement steps in `workflow.py`
4. Define human tasks in task templates
5. Add workflow documentation

### Scenario 3: New Report Type

**Adding market analysis reports:**

1. Create tools for market data aggregation
2. Enhance GRES agent skills for market analysis
3. Add favorite cards for common reports
4. Create examples in prompt library
5. Document in user guide

---

## Best Practices

### When Creating Agents

1. **Clear Domain Focus**: Each agent should have well-defined expertise
2. **Tool Selection**: Include only relevant tools to reduce confusion
3. **Comprehensive Skills**: Document capabilities, limitations, and examples
4. **Error Handling**: Gracefully handle missing data and edge cases
5. **User Guidance**: Provide helpful suggestions when queries are ambiguous

### When Creating Workflows

1. **Clear Objectives**: Define what the workflow accomplishes
2. **Logical Steps**: Break complex processes into manageable stages
3. **Human Checkpoints**: Identify where human review is needed
4. **State Management**: Track workflow state and progress
5. **Error Recovery**: Handle failures and allow workflow restart

### When Designing Features

1. **Accessibility First**: Support keyboard navigation and screen readers
2. **Progressive Enhancement**: Basic functionality without JavaScript
3. **Mobile Responsive**: Work on tablets and phones
4. **Performance**: Use caching, pagination, and lazy loading
5. **Observability**: Add metrics and logging for monitoring

---

## Common Queries & Patterns

### Property Queries
- "List properties in [location]"
- "Show me [property type] over [price]"
- "What's the status of property [ID]?"
- "Properties by [agent name]"
- "Active auctions ending this week"

### Auction Analysis
- "How many bids on property [ID]?"
- "Who won the auction for [property]?"
- "Average winning bid for [property type]"
- "Auction participation trends"
- "Time-to-close analysis"

### Bidder Management
- "Verify bidder [name/entity]"
- "Check SAM exclusions for [entity]"
- "OFAC screening for [person]"
- "List all bidders on property [ID]"
- "Bidder win rate analysis"

### Reports & Analytics
- "Generate Q1 performance report"
- "Property inventory summary"
- "Agent performance dashboard"
- "Market trends by state"
- "Revenue forecasting"

### Compliance & Verification
- "Run full background check on [bidder]"
- "Verify contractor eligibility"
- "Check for sanctions"
- "Audit trail for property [ID]"
- "Compliance status report"

---

## Data Access Patterns

### Read-Only Operations

Most agents are **read-only** - they query data but don't modify it:
- Property searches and filters
- Auction statistics and metrics
- Historical bid analysis
- Compliance database lookups

### Write Operations

Limited to specific workflows and admin functions:
- Workflow execution and state updates
- Task creation and submission
- Document uploads
- User preferences and settings

### Caching Strategy

- **LLM Responses**: 1 hour TTL in Redis
- **Tool Results**: Not cached (always fresh data)
- **Static Content**: Browser caching with versioning
- **Session Data**: Django session store

---

## User Personas

### Real Estate Specialist

**Needs:**
- Quick property information
- Auction status and results
- Performance metrics
- Market insights

**Typical Workflows:**
- Property research
- Auction monitoring
- Report generation
- Trend analysis

### Compliance Officer

**Needs:**
- Bidder verification
- Exclusion checks
- Audit trails
- Compliance reports

**Typical Workflows:**
- Pre-auction bidder screening
- Post-award verification
- Periodic compliance audits
- Risk assessment

### Administrator

**Needs:**
- System monitoring
- User management
- Workflow oversight
- Data integrity

**Typical Workflows:**
- Task review and approval
- System health checks
- Configuration management
- Access control

### Analyst

**Needs:**
- Complex queries
- Data visualization
- Trend analysis
- Forecasting

**Typical Workflows:**
- Ad-hoc analysis
- Report generation
- Data exploration
- Statistical modeling

---

## Technical Capabilities

### Natural Language Understanding

The system can interpret:
- Direct questions ("What is property 12345?")
- Comparative queries ("Which properties have the most bids?")
- Analytical requests ("Analyze bidding patterns")
- Complex filters ("Active auctions in California over $500K")
- Follow-up questions ("Tell me more about the first one")
- Contextual references ("What about the second property?")

### Tool Orchestration

Agents can:
- Chain multiple tool calls
- Aggregate data from multiple sources
- Make decisions about which tools to use
- Handle tool errors gracefully
- Optimize tool call sequences

### Multi-Agent Coordination

The system supports:
- Agent-to-agent handoffs
- Parallel agent execution
- Sequential verification workflows
- Fallback agent strategies
- Consensus-based decisions

---

## Extensibility Points

### Adding New Agents

**Process:**
1. Define agent metadata in Agent Studio or manually
2. Specify domain expertise and capabilities
3. Select relevant tools from available pool
4. Generate or write SKILLS.md documentation
5. Test agent with representative queries
6. Add to agent selector in UI

**When to Create a New Agent:**
- New domain expertise needed (e.g., environmental compliance)
- New data source integration (e.g., third-party APIs)
- Specialized user persona (e.g., legal analyst)
- Complex orchestration logic (e.g., multi-step verification)

### Adding New Workflows

**Process:**
1. Create workflow directory in `workflows/`
2. Define metadata.yaml with description and parameters
3. Implement workflow.py with BeeAI Framework
4. Create task templates for human review
5. Add documentation and examples
6. Register workflow with Flo agent

**When to Create a Workflow:**
- Multi-step processes with clear stages
- Human-in-the-loop decision points
- Compliance or approval requirements
- Orchestration of multiple agents
- State-dependent logic flows

### Adding New Tools

**Process:**
1. Create tool function in `tools/` directory
2. Define tool schema (name, description, parameters)
3. Implement tool logic (API calls, calculations, etc.)
4. Add to relevant agent configurations
5. Document in agent SKILLS.md
6. Test with example queries

**When to Create a Tool:**
- New data source or API endpoint
- Complex calculation or analysis
- Specialized business logic
- External system integration
- Performance optimization (batch operations)

---

## Configuration & Environment

### Key Environment Variables

```bash
# LLM Configuration
LLM_CHAT_MODEL_NAME=anthropic:claude-sonnet-4-5
ANTHROPIC_API_KEY=sk-ant-...

# Redis Caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0      # UI cache
REDIS_LOCATION=redis://redis:6379/1     # API cache

# Observability
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
OBSERVABILITY_DASHBOARD=https://us.cloud.langfuse.com/...

# Section 508 Accessibility
SECTION_508_MODE=false                  # Default: disabled
PIPER_TTS_URL=http://localhost:5000     # TTS service

# Application
DEBUG=true
USER_ID=9                               # Default user for testing
```

---

## Security & Compliance

### Data Protection

- **No PII in prompts**: Agents warned not to request PII unless necessary
- **Exclusions data**: SAM and OFAC data is public but sensitive
- **User sessions**: Django session framework with CSRF protection
- **File uploads**: Validated file types and size limits

### Access Control

- **Role-based**: Admin vs. regular user roles
- **Session-based**: User ID tracked in session
- **Workflow permissions**: Task assignment by role
- **Document ownership**: Users can only see their uploads

### Compliance Features

- **Section 508**: Full accessibility compliance mode
- **Audit Trails**: All workflow steps logged
- **Data Retention**: Configurable TTL for cached data
- **Sanitization**: HTML escaping and input validation

---

## Performance Considerations

### Caching Strategy

- **LLM responses cached**: Identical prompts return instantly
- **Cache hit rate**: Typically 30-50% in production
- **Response time**: <100ms for cached queries
- **Cost savings**: Significant reduction in API calls

### Query Optimization

- **Indexed databases**: Fast lookups on key fields
- **Pagination**: Large result sets paginated
- **Lazy loading**: Documents loaded on demand
- **Connection pooling**: Database connection reuse

### Scalability

- **Stateless API**: Horizontal scaling possible
- **Async workflows**: Non-blocking execution
- **Background tasks**: Long-running jobs queued
- **Rate limiting**: API throttling (future)

---

## Testing & Quality

### Test Coverage

- **Backend**: 92 Django tests (all passing)
- **Frontend**: Jest unit tests
- **E2E**: Playwright browser tests
- **Workflows**: Command integration tests

### Quality Checks

- **Linting**: Code style enforcement
- **Type hints**: Python type annotations
- **Documentation**: Comprehensive guides
- **Examples**: Working code samples

---

## Future Directions

### Potential Agent Ideas

- **Environmental Compliance Agent**: EPA requirements and regulations
- **Legal Analysis Agent**: Contract review and legal compliance
- **Financial Analysis Agent**: ROI calculations and forecasting
- **Market Research Agent**: Competitive analysis and trends
- **Asset Management Agent**: Property maintenance and lifecycle
- **Risk Assessment Agent**: Risk scoring and mitigation

### Potential Workflow Ideas

- **Property Listing Workflow**: Multi-step property listing approval
- **Auction Setup Workflow**: Configure and launch new auctions
- **Post-Sale Workflow**: Closing and transfer processes
- **Compliance Audit Workflow**: Periodic regulatory reviews
- **Document Review Workflow**: Multi-reviewer document approval
- **Performance Review Workflow**: Agent performance evaluation

### Potential Feature Ideas

- **Collaborative Chat**: Multiple users in same session
- **Scheduled Reports**: Automated report generation and email
- **Advanced Analytics**: Predictive modeling and forecasting
- **Mobile App**: Native iOS/Android applications
- **API Authentication**: OAuth2 for external integrations
- **Webhook Integration**: Event-driven external notifications

---

## Context Usage Examples

### For Agent Creation

When creating a new agent, reference:
- **Domain**: What area of RealtyIQ does this agent cover?
- **Tools**: Which of the 16 tools should be available?
- **Use Cases**: What queries will users ask this agent?
- **Patterns**: Similar to which existing agent?

### For Workflow Design

When designing a workflow, reference:
- **Agents**: Which agents participate in which steps?
- **Data Flow**: What information passes between steps?
- **Tasks**: Where are human decision points?
- **Examples**: Similar to which existing workflow?

### For Feature Development

When adding features, reference:
- **Architecture**: How does it fit into Django app structure?
- **UI Patterns**: Bootstrap 5 components and styling
- **Observability**: Add Langfuse traces
- **Documentation**: Update relevant user/developer guides

---

**Document Version**: 1.0  
**Last Updated**: February 21, 2026  
**Maintained By**: RealtyIQ Development Team

---

**Related Documentation:**
- [Technical Specs](../docs/SPECS.md)
- [User Guide](../docs/user-guide/README.md)
- [Developer Guide](../docs/developer-guide/README.md)
- [Workflow Developer Guide](../workflows/docs/DEVELOPER_GUIDE.md)
