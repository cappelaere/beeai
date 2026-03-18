# Web Search Implementation

**Feature**: DuckDuckGo Web Search Integration  
**Implementation Date**: February 2026  
**Status**: Active

---

## Overview

RealtyIQ now includes web search capability using BeeAI Framework's built-in `DuckDuckGoSearchTool`. This enables agents to search the internet for real-time information, current events, market trends, and external research without requiring API keys.

### Key Benefits

- **No API Key Required**: DuckDuckGo provides free search access
- **Privacy-First**: No user tracking or search history
- **Safe Search**: Content filtering enabled by default
- **Simple Integration**: Built into BeeAI Framework
- **Flexible Configuration**: Configurable result limits and safety settings

---

## Architecture

### Component Overview

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       v
┌─────────────────────────────────┐
│  Agent (Research/Flo)           │
│  - Analyzes query               │
│  - Formulates search terms      │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  DuckDuckGoSearchTool           │
│  - max_results: 5-10            │
│  - safe_search: STRICT          │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  ddgs Package                   │
│  - DDGS client                  │
│  - HTTP requests                │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  DuckDuckGo API                 │
│  - Public search API            │
│  - Returns results              │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  Search Results                 │
│  - Title, description, URL      │
│  - Up to 10 results             │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────────────────┐
│  Agent Response                 │
│  - Summarizes findings          │
│  - Cites sources                │
│  - Provides URLs                │
└─────────────────────────────────┘
```

---

## Implementation Details

### 1. Package Installation

Added to `requirements.txt`:

```txt
# Web Search
ddgs>=9.11.0  # DuckDuckGo search (no API key required)
```

Installation:
```bash
make install
```

### 2. Research Agent Creation

Created new specialized agent at `agents/research/`:

**Structure:**
```
agents/research/
├── __init__.py          # Agent export
├── agent.py             # Agent configuration
├── SKILLS.md            # Detailed capabilities (600+ lines)
└── README.md            # Agent documentation (300+ lines)
```

**Configuration** (`agent.py`):
```python
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.think import ThinkTool
from agents.base import AgentConfig

RESEARCH_AGENT_CONFIG = AgentConfig(
    name="Research Agent",
    description="Web search specialist for real-time information and research",
    instructions="[Detailed instructions for web search usage]",
    tools=[
        ThinkTool(),
        DuckDuckGoSearchTool(max_results=10, safe_search="STRICT")
    ],
    icon="🔍",
)
```

### 3. Agent Registry

Added to `agents.yaml`:
```yaml
research:
  name: Research Agent
  display_name: Research
  icon: 🔍
  description: Web search specialist for real-time information and research
  skills_file: agents/research/SKILLS.md
  config_module: agents.research.agent
  config_name: RESEARCH_AGENT_CONFIG
  default: false
```

### 4. Flo Agent Enhancement

Added web search to Flo Agent for workflow research (`agents/flo/agent.py`):

```python
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

tools=[
    ThinkTool(),
    DuckDuckGoSearchTool(max_results=5, safe_search="STRICT"),  # Fewer results
    # ... workflow tools ...
]
```

**Rationale**: Enables Flo to research workflow best practices and patterns.

---

## Configuration Options

### DuckDuckGoSearchTool Parameters

```python
DuckDuckGoSearchTool(
    max_results: int = 10,        # Number of results (1-10 recommended)
    safe_search: str = "STRICT",  # STRICT, MODERATE, or OFF
    options: dict | None = None   # Additional options
)
```

### Safe Search Levels

- **STRICT** (Recommended): Filters explicit content, family-friendly
- **MODERATE**: Filters extreme content only
- **OFF**: No filtering (not recommended for production)

### Result Limits by Agent

- **Research Agent**: 10 results (primary search agent)
- **Flo Agent**: 5 results (secondary use for workflow research)

---

## Usage Patterns

### Search Query Optimization

**Best Practices:**
```python
# Good: Specific with context
"Washington DC commercial property values 2026"

# Better: Includes location and timeframe
"GSA property auction regulations 2026 Washington DC"

# Best: Quoted phrases with specific details
'"FHA loan limits" 2026 "Washington DC" single-family'
```

**Query Formulation in Instructions:**
```python
instructions=(
    "When users ask about market conditions:\n"
    "1. Identify key terms (location, property type, timeframe)\n"
    "2. Construct specific search query\n"
    "3. Use quotes for exact phrases\n"
    "4. Include current year for recent information\n"
    "5. Review top 5-10 results\n"
    "6. Summarize findings with source URLs"
)
```

### Response Format

Agents should structure search results:

```markdown
## [Topic]

[Brief answer/summary]

**Key Findings:**
- Finding 1
- Finding 2
- Finding 3

**Sources:**
1. [Source Title] - [URL]
   Description or key excerpt
   
2. [Source Title] - [URL]
   Description or key excerpt

**Note:** Information current as of [date]. [Any caveats]
```

---

## Testing

### Test Coverage

Created `agent_ui/agent_app/tests/test_research_agent.py` with 14 tests:

**Test Categories:**
1. **Tool Tests** (4 tests):
   - Import verification
   - Instantiation
   - Configuration options
   - Input schema validation

2. **Agent Tests** (4 tests):
   - Agent import
   - Configuration validation
   - Tool inclusion (DuckDuckGo + Think)
   - Instructions verification

3. **Integration Tests** (3 tests):
   - Flo agent integration
   - Configuration verification
   - Tool count validation

4. **Registry Tests** (3 tests):
   - Registry entry validation
   - Configuration correctness
   - Agent loadability

**Running Tests:**
```bash
# Specific test file
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_research_agent

# All tests
make test-backend
```

**Results**: All 14 tests passing ✅

---

## Security Considerations

### Content Safety

- **Safe Search**: STRICT mode enabled by default
- **Content Filtering**: Inappropriate content blocked
- **Workplace Appropriate**: Results suitable for professional environment

### Privacy

- **No Tracking**: DuckDuckGo doesn't track searches
- **No User Profiling**: Results not personalized by history
- **No Data Retention**: Search history not stored
- **Anonymous Queries**: No user identification sent

### Rate Limiting

**Considerations:**
- DuckDuckGo may rate-limit excessive requests
- Recommend reasonable query frequency
- Use caching for common queries (future enhancement)
- Monitor usage patterns

**Mitigation:**
```python
# Configure lower max_results for secondary agents
DuckDuckGoSearchTool(max_results=5)  # Instead of 10

# Add delay between rapid searches (if needed)
# Implement in agent logic, not tool configuration
```

---

## Performance

### Response Times

**Typical Performance:**
- Search execution: 1-3 seconds
- Result processing: 1-2 seconds
- Agent summarization: 2-5 seconds
- **Total response time**: 5-10 seconds average

**Factors:**
- Network latency to DuckDuckGo API
- Number of results requested
- Agent processing complexity

### Optimization Strategies

**Current:**
- Limit results (5-10 instead of 50+)
- Safe search filtering reduces processing
- Single search per query when possible

**Future Enhancements:**
- Cache common searches
- Pre-fetch trending topics
- Batch related queries

---

## Limitations

### What Web Search CAN Do

✅ Public web content  
✅ Current news and events  
✅ Market trends and reports  
✅ Company information (public)  
✅ Government websites (.gov)  
✅ Academic resources  
✅ General knowledge  

### What Web Search CANNOT Do

❌ Paywalled content  
❌ Private databases  
❌ Subscription services  
❌ Internal RealtyIQ data (use GRES Agent)  
❌ Real-time stock/financial data (delayed)  
❌ Personal information (privacy protected)  
❌ Content behind authentication  

---

## Troubleshooting

### Common Issues

**No Results Found**
```
Cause: Query too specific or niche topic
Solution: Broaden search terms, try alternative phrasing
```

**Poor Quality Results**
```
Cause: Vague query terms
Solution: Add context (dates, locations, specifics)
```

**Rate Limiting**
```
Cause: Too many rapid searches
Solution: Reduce query frequency, implement delays
```

**Outdated Information**
```
Cause: Search doesn't prioritize recent content
Solution: Include year in query ("2026"), use "latest" or "current"
```

### Debugging

**Check Tool Availability:**
```python
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
tool = DuckDuckGoSearchTool()
print(tool.name)  # Should print "DuckDuckGo"
```

**Verify Agent Configuration:**
```bash
cd agent_ui && ../venv/bin/python manage.py shell
>>> from agents.registry import get_agent_config
>>> config = get_agent_config('research')
>>> print(config.tools)
```

**Test Direct Search:**
```python
# In Django shell
from beeai_framework.tools.search.duckduckgo import (
    DuckDuckGoSearchTool,
    DuckDuckGoSearchToolInput
)
import asyncio

tool = DuckDuckGoSearchTool(max_results=3)
input_data = DuckDuckGoSearchToolInput(query="test query")

# Run search
result = asyncio.run(tool.run(input_data))
print(result)
```

---

## Future Enhancements

### Potential Improvements

**Search Result Caching:**
- Cache common queries
- Reduce API calls
- Faster response times
- TTL-based expiration

**Multi-Source Aggregation:**
- Combine DuckDuckGo with other sources
- Cross-reference information
- Improved accuracy

**Advanced Filtering:**
- Date range filtering
- Domain-specific searches
- Result type filtering (news, articles, etc.)

**Search History:**
- Track previous searches
- Suggest refinements
- Learn from user patterns

**Specialized Search Modes:**
- Real estate-specific searches
- Regulation-focused searches
- Company research mode
- News aggregation mode

---

## Documentation References

### Implementation Files

- `agents/research/` - Research Agent implementation
- `agents/flo/agent.py` - Flo Agent enhancement
- `requirements.txt` - Package dependencies
- `agents.yaml` - Agent registry
- `agent_ui/agent_app/tests/test_research_agent.py` - Test suite

### Documentation

- `agents/research/SKILLS.md` - Detailed capabilities
- `agents/research/README.md` - Agent overview
- `context/AGENT_GUIDELINES.md` - Web search guidelines
- `docs/developer-guide/MAKEFILE_COMMANDS.md` - Installation commands

### External References

- [BeeAI Framework Tools](https://framework.beeai.dev/modules/tools)
- [DuckDuckGo Search API](https://duckduckgo.com/api)
- [ddgs Package](https://pypi.org/project/ddgs/)

---

## Maintenance

### Regular Checks

**Monthly:**
- Verify ddgs package updates
- Test search functionality
- Review result quality
- Check rate limiting status

**Quarterly:**
- Review search patterns
- Update SKILLS.md examples
- Assess performance metrics
- Evaluate user feedback

**Annually:**
- Major version updates
- Architecture review
- Security audit
- Feature enhancements

### Update Procedure

**Package Updates:**
```bash
# Check for updates
venv/bin/pip list --outdated | grep ddgs

# Update package
venv/bin/pip install --upgrade ddgs

# Update requirements.txt
# Update version number in requirements.txt

# Test
make test-backend
```

**Configuration Updates:**
```python
# Update agent configuration if needed
# Test changes
# Update documentation
# Deploy
```

---

## Support

### Getting Help

**Issues:**
- Check SKILLS.md for usage guidance
- Review test suite for examples
- Consult BeeAI Framework documentation
- Contact development team

**Feedback:**
- Report search quality issues
- Suggest query improvements
- Request feature enhancements
- Share best practices

---

**Implementation Date**: February 2026  
**Version**: 1.0.0  
**Status**: Active  
**Last Updated**: February 2026
