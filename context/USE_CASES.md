# RealtyIQ Use Cases Library

Detailed use cases and scenarios for RealtyIQ functionality.

---

## Property Research

### UC-101: Find Properties by Location

**Persona**: Real Estate Specialist  
**Goal**: Find properties in a specific state or city

**Conversation Flow:**
```
User: "Show me all properties in California"
GRES Agent: [Calls list_properties with state='CA']
→ Returns: 45 properties with summary information

User: "Which ones are commercial?"
GRES Agent: [Applies filter to previous results, uses context]
→ Returns: 12 commercial properties

User: "What's the average asking price?"
GRES Agent: [Calculates from results]
→ Returns: $2.3M average with breakdown
```

**Tools Used**: `list_properties`, session context

---

### UC-102: Property Detail Investigation

**Persona**: Analyst  
**Goal**: Deep dive into specific property

**Conversation Flow:**
```
User: "Tell me everything about property 12345"
GRES Agent: [Calls get_property_detail]
→ Returns: Full property details (location, size, condition, history)

User: "What's the auction status?"
GRES Agent: [Extracts auction info from property detail]
→ Returns: Auction dates, current bids, time remaining

User: "Show me all bids"
GRES Agent: [Calls bid_history with property_id=12345]
→ Returns: Chronological bid list with amounts and bidders
```

**Tools Used**: `get_property_detail`, `bid_history`

---

### UC-103: Property Type Analysis

**Persona**: Business Analyst  
**Goal**: Understand property portfolio composition

**Conversation Flow:**
```
User: "Give me a breakdown of properties by type"
GRES Agent: [Calls property_count_summary]
→ Returns: Counts by residential, commercial, land, industrial

User: "Which type has the highest average sale price?"
GRES Agent: [Analyzes historical data]
→ Returns: Commercial properties with $3.2M average

User: "Show me the top 5 commercial properties"
GRES Agent: [Calls list_properties with type filter and sorting]
→ Returns: Top 5 by price with details
```

**Tools Used**: `property_count_summary`, `list_properties`

---

## Auction Management

### UC-201: Monitor Active Auctions

**Persona**: Real Estate Specialist  
**Goal**: Track current auction activity

**Conversation Flow:**
```
User: "What auctions are ending this week?"
GRES Agent: [Calls auction_dashboard with date filter]
→ Returns: 8 auctions with end dates and current bid status

User: "Which one has the most bidders?"
GRES Agent: [Calls auction_bidders for each auction]
→ Returns: Property 99887 with 23 registered bidders

User: "Show me the bidding activity"
GRES Agent: [Calls auction_total_bids for property 99887]
→ Returns: 67 total bids, $450K current high bid
```

**Tools Used**: `auction_dashboard`, `auction_bidders`, `auction_total_bids`

---

### UC-202: Auction Performance Analysis

**Persona**: Administrator  
**Goal**: Evaluate auction effectiveness

**Conversation Flow:**
```
User: "Generate Q1 2026 auction performance report"
GRES Agent: [Multi-tool orchestration]
→ auction_dashboard (overall metrics)
→ property_count_summary (inventory)
→ Synthesizes executive summary

User: "What's the average time from listing to close?"
GRES Agent: [Analyzes historical data]
→ Returns: 45 days average with trend analysis

User: "Compare to Q4 2025"
GRES Agent: [Historical comparison]
→ Returns: 8% improvement, insights on what changed
```

**Tools Used**: `auction_dashboard`, `property_count_summary`, analytics

---

## Bidder Verification

### UC-301: Quick SAM Check

**Persona**: Compliance Officer  
**Goal**: Verify bidder is not excluded

**Conversation Flow:**
```
User: "@sam is ABC Construction Corp excluded?"
SAM Agent: [Searches SAM exclusions database]
→ Returns: No active exclusions found

User: "@sam check John Smith"
SAM Agent: [Fuzzy name search]
→ Returns: Found 3 matches, shows details for review

User: "@sam exclude party with CAGE code 1A2B3"
SAM Agent: [Precise CAGE code lookup]
→ Returns: Active exclusion from 2024-03-15, fraud conviction
```

**Tools Used**: SAM database search with fuzzy matching

---

### UC-302: OFAC Sanctions Screening

**Persona**: Compliance Officer  
**Goal**: Screen bidder against sanctions list

**Conversation Flow:**
```
User: "@ofac screen Vladimir Petrov, DOB 1975-08-22"
OFAC Agent: [Searches OFAC SDN list with fuzzy matching]
→ Returns: Possible match - 85% similarity, review required

User: "@ofac show me the details"
OFAC Agent: [Retrieves full SDN record]
→ Returns: Complete sanctions information, reason, date

User: "@ofac any matches for Russian entities?"
OFAC Agent: [Searches by country]
→ Returns: 1,234 Russian entities on SDN list
```

**Tools Used**: OFAC database with fuzzy name matching

---

### UC-303: Comprehensive Bidder Verification

**Persona**: Administrator  
**Goal**: Full eligibility check before contract award

**Conversation Flow:**
```
User: "Run full verification for XYZ Corporation"
User: [Switches to Flo agent]
Flo: "I'll help you run a workflow"

User: "Run bidder onboarding workflow for XYZ Corporation"
Flo: [Initiates bidder_onboarding workflow]
→ Step 1: SAM check - PASSED
→ Step 2: OFAC screen - FLAGGED (potential match)
→ Step 3: Creates human review task TASK_5678

User: "/task claim TASK_5678"
Flo: [Assigns task to user]
→ Shows flagged details for manual review

User: "/task submit TASK_5678 approve with notes: False positive, different person"
Flo: [Records decision, completes workflow]
→ Workflow completed: APPROVED
```

**Tools Used**: Workflow orchestration, SAM agent, OFAC agent, task system

---

## Document Management

### UC-401: Document Upload and Search

**Persona**: Real Estate Specialist  
**Goal**: Upload appraisal and ask questions

**Workflow:**
```
1. Navigate to Documents → Upload
2. Upload "property_appraisal_12345.pdf"
3. System indexes document with FAISS
4. Navigate to chat

User: "@library what is the appraised value in the document?"
Library Agent: [RAG search through document]
→ Returns: "$1.8M as of January 2026" with page reference

User: "@library were there any issues found?"
Library Agent: [Semantic search for problems/issues]
→ Returns: "Minor roof repairs needed ($15K estimated)"

User: "@library summarize the key findings"
Library Agent: [Comprehensive RAG query]
→ Returns: Bullet-point summary of appraisal report
```

**Tools Used**: RAG tool with FAISS vector search

---

### UC-402: Multi-Document Analysis

**Persona**: Analyst  
**Goal**: Compare information across multiple documents

**Conversation Flow:**
```
User: [Uploads 3 property inspection reports]

User: "@library which property has the best structural condition?"
Library Agent: [RAG search across all 3 documents]
→ Returns: Property B has highest ratings, details

User: "@library compare environmental findings"
Library Agent: [Semantic comparison]
→ Returns: Side-by-side comparison table

User: "@library any common issues?"
Library Agent: [Pattern analysis across documents]
→ Returns: HVAC systems need attention in all 3 properties
```

**Tools Used**: RAG tool, multi-document search

---

## Business Intelligence

### UC-501: Agent Performance Report

**Persona**: Administrator  
**Goal**: Evaluate real estate agent performance

**Conversation Flow:**
```
User: "Show me agent performance for Q1 2026"
GRES Agent: [Calls list_agents_summary with date range]
→ Returns: 15 agents with key metrics

User: "Who are the top 3 by sales volume?"
GRES Agent: [Sorts and filters results]
→ Returns: Top 3 agents with dollar volume and deal count

User: "Give me a detailed breakdown of the top agent"
GRES Agent: [Combines multiple tool calls]
→ Returns: Properties listed, sales closed, average price, commission
```

**Tools Used**: `list_agents_summary`, `list_properties`, aggregation

---

### UC-502: Market Trend Analysis

**Persona**: Business Analyst  
**Goal**: Identify market patterns and trends

**Conversation Flow:**
```
User: "What are the trends in commercial property sales?"
GRES Agent: [Analyzes historical data]
→ Returns: Increasing prices (+12% YoY), longer days on market

User: "Which states have the most activity?"
GRES Agent: [Calls property_count_summary by state]
→ Returns: CA (234), TX (189), FL (156)

User: "Create a state-by-state comparison chart"
GRES Agent: [Formats data for visualization]
→ Returns: Markdown table with all states, counts, trends
```

**Tools Used**: Historical analysis, `property_count_summary`, aggregation

---

## Workflow Execution

### UC-601: Workflow Discovery

**Persona**: User (any role)  
**Goal**: Find available workflows

**Conversation Flow:**
```
User: "/workflow list"
Flo Agent: [Lists all workflows]
→ Returns: 7 workflows with IDs and descriptions

User: "Tell me more about workflow 1"
Flo Agent: [Retrieves workflow details]
→ Returns: Bidder Onboarding - multi-step verification

User: "What steps does it include?"
Flo Agent: [Reads workflow metadata]
→ Returns: Step breakdown with agent assignments
```

**Tools Used**: `list_workflows`, workflow metadata

---

### UC-602: Workflow Execution with Parameters

**Persona**: Compliance Officer  
**Goal**: Run verification workflow for bidder

**Conversation Flow:**
```
User: [Switches to Flo agent]

User: "Run workflow 1 for ABC Corp with contact John Doe"
Flo Agent: [Initiates bidder_onboarding workflow]
→ Validates parameters
→ Creates workflow run with ID RUN_123
→ Starts execution

[Real-time updates via SSE:]
→ "Starting SAM.gov check..."
→ "SAM check complete: PASSED"
→ "Starting OFAC screening..."
→ "OFAC check complete: PASSED"
→ "Starting identity verification..."
→ "Creating task TASK_456 for manual review"

User: "/task claim TASK_456"
Flo Agent: [Assigns task]
→ Shows identity documents for review

User: "/task submit TASK_456 approve"
Flo Agent: [Completes workflow]
→ Workflow RUN_123 completed: APPROVED
```

**Tools Used**: `execute_workflow`, `get_workflow_status`, task system

---

### UC-603: Task Management

**Persona**: Reviewer  
**Goal**: Review and complete assigned tasks

**Conversation Flow:**
```
User: "/task list"
Flo Agent: [Lists user's tasks]
→ Returns: 3 pending tasks requiring attention

User: "/task claim TASK_789"
Flo Agent: [Assigns task to user]
→ Returns: Task details with review data

User: "What information do I need to approve this?"
Flo Agent: [Explains task context]
→ Returns: Decision criteria and available data

User: "/task submit TASK_789 reject with notes: Missing documentation"
Flo Agent: [Records decision, updates workflow]
→ Task completed, workflow step rejected
```

**Tools Used**: `list_tasks`, `claim_task`, `submit_task`

---

## System Administration

### UC-701: Agent Management

**Persona**: Administrator  
**Goal**: Configure system agents

**Workflow:**
```
1. Navigate to Agent Collection
2. Click three-dot menu on GRES Agent
3. Select "Set as Default"
4. Confirm action
→ GRES Agent is now default for new chats

Alternative: Edit agent
1. Click three-dot menu on Custom Agent
2. Select "Edit Agent"
3. Modify name and description
4. Save changes
→ Agent metadata updated in registry
```

**UI Features**: Admin actions menu, agent editing

---

### UC-702: Cache Management

**Persona**: Administrator  
**Goal**: Monitor and manage cache performance

**Workflow:**
```
User: Navigate to Settings page
[Cache Management section shows:]
- Status: Enabled ✅
- Database: redis://localhost:6379/0
- Hit Rate: 47.2%
- Hits: 1,234
- Misses: 1,378
- Saved: 52 API calls

User: Click "Clear All Cached Responses"
[Confirmation dialog]
User: Confirm
→ Cache cleared, hit rate resets
→ Next queries will be slower but fresh
```

**UI Features**: Cache stats display, clear cache button

---

### UC-703: Observability Monitoring

**Persona**: Developer  
**Goal**: Debug agent behavior

**Workflow:**
```
1. User runs query in chat
2. Navigate to Observability → Dashboard
3. Click on latest trace in Langfuse
4. View hierarchical trace:
   - User prompt
   - Agent execution
   - Tool calls (nested)
   - Response generation
5. Inspect tool inputs/outputs
6. Check latency and token usage
7. Identify performance bottlenecks
```

**Tools Used**: Langfuse dashboard, trace inspection

---

## Accessibility

### UC-801: Enable Section 508 Mode

**Persona**: User with visual impairment  
**Goal**: Use accessibility features

**Conversation Flow:**
```
User: "/settings 508 on"
System: [Enables Section 508 mode]
→ UI updated with larger fonts
→ Better color contrast applied
→ Audio controls appear on messages

User: "What are the properties in Florida?"
Agent: [Responds with text]
[Audio button appears on response]

User: [Clicks audio button]
[Piper TTS generates speech]
[Audio player plays response]

User: "/settings 508 off"
System: [Disables Section 508 mode]
→ UI returns to normal
→ Audio controls removed
```

**Features Used**: Section 508 toggle, TTS generation

---

### UC-802: Keyboard-Only Navigation

**Persona**: User relying on keyboard  
**Goal**: Navigate system without mouse

**Workflow:**
```
1. Tab to navigation sidebar
2. Arrow keys to select section
3. Enter to expand/collapse
4. Tab through links
5. Enter to navigate
6. Tab to chat input
7. Type query
8. Enter to submit
9. Tab to response
10. Arrow keys to scroll

All functionality accessible via keyboard.
```

**Features Used**: Full keyboard navigation, ARIA labels

---

## Advanced Scenarios

### UC-901: Multi-Agent Collaboration

**Persona**: Compliance Officer  
**Goal**: Comprehensive bidder check using multiple agents

**Conversation Flow:**
```
User: "I need to verify XYZ Corp before award"

User: "@sam check XYZ Corporation"
SAM Agent: No exclusions found ✓

User: "@ofac screen XYZ Corporation"  
OFAC Agent: No sanctions found ✓

User: "@library search for any previous issues with XYZ Corp"
Library Agent: Found 2 documents, no compliance issues ✓

User: "@gres how many times has XYZ Corp bid before?"
GRES Agent: 12 previous bids, 3 wins, good track record ✓

[User makes informed decision based on multi-agent insights]
```

**Tools Used**: Multiple agents in sequence

---

### UC-902: Workflow with Human Task

**Persona**: Workflow participant  
**Goal**: Complete multi-step process with approval

**Complete Flow:**
```
Step 1: Initiate Workflow
User: [To Flo] "Run property listing workflow for 789 Oak Street"
Flo: Workflow started - RUN_555

Step 2: Automated Checks (Agent-driven)
→ Property data validation
→ Title search
→ Environmental pre-screen
→ All automated steps complete

Step 3: Human Review Task Created
Flo: Created TASK_888 for final approval
[Task assigned to Administrator role]

Step 4: Task Claim
Admin: "/task claim TASK_888"
Flo: Task claimed, review data shown

Step 5: Decision
Admin: Reviews property details, checks, documentation
Admin: "/task submit TASK_888 approve"
Flo: Workflow completed - APPROVED

Step 6: Post-Actions
→ Property status updated to "Listed"
→ Notification sent
→ Audit trail recorded
```

**Tools Used**: Workflow system, task management, multi-agent coordination

---

### UC-903: Session Context for Complex Analysis

**Persona**: Analyst  
**Goal**: Progressive data exploration

**Conversation Flow:**
```
User: "Show me properties in Texas"
→ Agent returns 50 properties

User: "Filter to only commercial"
→ Agent uses context, filters to 18 properties

User: "Sort by price descending"
→ Agent uses context, reorders list

User: "Tell me about the top 3"
→ Agent uses context, retrieves details for top 3

User: "Which one has the best location?"
→ Agent uses context, compares locations of top 3

User: "Create a comparison table"
→ Agent uses full conversation context, generates table
```

**Features Used**: Session context (20 message memory), progressive refinement

---

## Error Scenarios

### UC-E01: Missing Data Graceful Handling

**Conversation:**
```
User: "Show me property 99999"
GRES Agent: [Calls get_property_detail]
→ API returns 404

Agent Response: "I couldn't find property 99999 in the system. 
Would you like me to:
- Search for properties with similar IDs?
- List recent properties?
- Try a different search?"
```

**Pattern**: Graceful error handling with helpful suggestions

---

### UC-E02: Ambiguous Query Clarification

**Conversation:**
```
User: "Show me John's properties"
GRES Agent: "I found multiple people named John:
1. John Smith (Agent ID: 123)
2. John Doe (Agent ID: 456)
3. John Williams (Agent ID: 789)

Which one would you like to see properties for?"

User: "The first one"
GRES Agent: [Uses context, retrieves for John Smith]
→ Returns: 12 properties listed by John Smith
```

**Pattern**: Clarification before proceeding

---

### UC-E03: Tool Failure Recovery

**Conversation:**
```
User: "List all properties"
GRES Agent: [Calls list_properties]
→ API timeout error

Agent Response: "I encountered a timeout while fetching the property list. 
Let me try with a smaller scope.

Could you specify:
- A state or region to search?
- A property type to filter by?
- A date range to narrow results?"
```

**Pattern**: Fallback strategy when tools fail

---

## Integration Scenarios

### UC-I01: External API Integration

**Example**: Weather data for property insights

**New Agent: Weather Analysis Agent**
```
Purpose: Integrate weather data for property decisions
Tools: weather_api, property_location_lookup
Use Case: "What's the climate risk for this coastal property?"
```

### UC-I02: Third-Party Verification

**Example**: Credit bureau integration

**New Workflow: Credit Check Workflow**
```
Steps:
1. Collect bidder consent
2. Call credit bureau API
3. Parse credit report
4. Create review task
5. Compliance officer approval
```

---

## Performance Patterns

### Caching Wins

**Best cache performance:**
- Repeated property lookups (90% hit rate)
- Common dashboard queries (75% hit rate)
- Status checks (85% hit rate)

**Poor cache performance:**
- Time-sensitive auction data
- Real-time bid updates
- User-specific queries

### Query Optimization

**Fast queries:**
- Direct ID lookups
- Indexed field searches
- Cached aggregations

**Slow queries:**
- Full table scans
- Complex joins
- Unindexed filters

**Optimization strategies:**
- Add pagination for large results
- Use filters early in query
- Cache aggregated summaries
- Index frequently searched fields

---

## Testing Scenarios

### Functional Tests

- Property CRUD operations
- Auction lifecycle
- Bidder verification workflow
- Document upload and search
- Cache hit/miss behavior
- Session management

### Integration Tests

- Multi-agent workflows
- Tool chaining
- Database transactions
- Redis caching
- Langfuse tracing

### E2E Tests

- User registration to bid
- Property listing to sale
- Document upload to search
- Workflow initiation to completion

---

**Version**: 1.0  
**Last Updated**: February 21, 2026  
**Related**: [CONTEXT.md](CONTEXT.md)
