# Research Agent Skills

**Agent**: Research Agent (🔍)  
**Purpose**: Web search specialist for real-time information and research  
**Primary Tool**: DuckDuckGo Search

---

## Core Capabilities

### 1. Web Search
Search the internet for current information on any topic using DuckDuckGo.

**Tool**: `DuckDuckGoSearchTool`
- Returns up to 10 search results
- Safe search enabled (STRICT mode)
- No API key required
- Public web content only

### 2. Strategic Thinking
Plan research approaches for complex queries.

**Tool**: `ThinkTool`
- Break down multi-part questions
- Plan search strategies
- Evaluate result quality

---

## Use Cases

### Real Estate Research

**Market Trends**
```
User: "What are the current real estate trends in Washington DC?"
Agent: Search "Washington DC real estate market trends 2026"
Result: Summarize findings with sources
```

**Property Valuations**
```
User: "What factors are affecting commercial property values?"
Agent: Search "commercial property value factors 2026"
Result: Provide insights from multiple sources
```

**Neighborhood Information**
```
User: "Tell me about the Capitol Hill neighborhood"
Agent: Search "Capitol Hill Washington DC neighborhood guide"
Result: Present comprehensive overview with URLs
```

### Compliance & Regulations

**Federal Regulations**
```
User: "What are the latest GSA real estate auction regulations?"
Agent: Search "GSA real estate auction regulations 2026"
Result: Cite official sources and recent updates
```

**State Requirements**
```
User: "What are Virginia real estate disclosure requirements?"
Agent: Search "Virginia real estate disclosure requirements 2026"
Result: Provide state-specific information
```

### Company Research

**Background Checks**
```
User: "What can you find about XYZ Corp?"
Agent: Search "XYZ Corp company information background"
Result: Company profile, news, public records
```

**Industry Information**
```
User: "Tell me about commercial real estate developers in Maryland"
Agent: Search "commercial real estate developers Maryland"
Result: List major players with details
```

### General Research

**News & Current Events**
```
User: "Any recent news about federal property sales?"
Agent: Search "federal property sales news 2026"
Result: Recent articles with dates and sources
```

**How-To Information**
```
User: "How does the GSA auction process work?"
Agent: Search "GSA auction process guide"
Result: Step-by-step information from official sources
```

---

## Search Best Practices

### Crafting Effective Queries

**Be Specific**
- ❌ "property values"
- ✅ "Washington DC commercial property values 2026"

**Use Quotes for Exact Phrases**
- ❌ GSA real estate
- ✅ "GSA real estate" auctions

**Add Time Context**
- ❌ "mortgage rates"
- ✅ "mortgage rates 2026" or "current mortgage rates"

**Include Location When Relevant**
- ❌ "building codes"
- ✅ "building codes Maryland 2026"

### Multiple Search Strategy

If first search doesn't yield good results:

1. **Rephrase**: Try different keywords
2. **Narrow**: Add more specific terms
3. **Broaden**: Remove overly specific terms
4. **Alternative Angle**: Search related topics

Example:
```
Query 1: "GSA property auction process"
Query 2: "how to bid on government real estate"
Query 3: "federal property disposal process"
```

### Source Evaluation

**Prioritize**:
- Official government websites (.gov)
- Established news organizations
- Industry associations
- Academic institutions

**Be Cautious**:
- Unknown blogs or personal sites
- Outdated information (>2 years old)
- Promotional or biased content

---

## Response Format

### Standard Response Structure

1. **Brief Answer**: Direct response to question
2. **Key Findings**: Summarize main points (3-5 bullets)
3. **Sources**: List URLs with descriptions
4. **Additional Context**: Caveats, dates, limitations

### Example Response

```markdown
## Market Trends in Washington DC

The Washington DC real estate market in 2026 shows continued growth 
in commercial properties with strong demand in federal contracting areas.

**Key Findings**:
- Commercial property values up 8% year-over-year
- Federal contracting zones seeing highest demand
- Residential market stabilizing after 2025 surge
- New GSA lease requirements affecting available properties

**Sources**:
1. Washington Business Journal - "DC Commercial Real Estate Report 2026"
   https://www.bizjournals.com/washington/news/2026/...
   
2. GSA Office - "Federal Property Lease Guidelines"
   https://www.gsa.gov/real-estate/leases/...
   
3. Urban Land Institute - "DC Market Analysis Q1 2026"
   https://uli.org/research/dc-market-q1-2026

**Note**: Data current as of February 2026. Market conditions 
are subject to change.
```

---

## Limitations

### What Research Agent CAN Do

✅ Search public web content  
✅ Find current news and information  
✅ Locate official government sources  
✅ Research company information  
✅ Find market trends and reports  
✅ Verify publicly available facts  

### What Research Agent CANNOT Do

❌ Access paywalled content  
❌ View private databases  
❌ Search internal RealtyIQ data (use GRES Agent)  
❌ Access confidential records  
❌ Guarantee accuracy of third-party sources  
❌ Provide legal or financial advice  

---

## Integration with Other Agents

### When to Use Research Agent vs. Other Agents

**Use Research Agent for**:
- Current web information
- External sources and validation
- General market research
- Company background checks

**Use GRES Agent for**:
- Internal auction data
- Property details in system
- Bid history and analytics
- Agent performance metrics

**Use Flo Agent for**:
- Workflow execution
- Internal process documentation
- Task management
- System operations

**Use Library Agent for**:
- Uploaded document search
- Internal knowledge base
- Document management
- RAG-based queries

### Collaborative Workflows

**Example 1: Property Due Diligence**
1. GRES Agent → Get internal property data
2. Research Agent → Find market comparables
3. Research Agent → Check area regulations
4. Library Agent → Search related documents

**Example 2: Bidder Verification**
1. Bidder Verification → Run compliance checks
2. Research Agent → Company background research
3. Research Agent → Industry reputation search
4. SAM/OFAC → Federal exclusion checks

---

## Advanced Features

### Search Result Ranking

DuckDuckGo ranks results by relevance. The agent:
- Reviews top 10 results
- Filters for quality and relevance
- Summarizes most pertinent information
- Cites multiple sources when available

### Privacy & Safety

**Safe Search**:
- STRICT mode enabled by default
- Filters inappropriate content
- Family-friendly results

**No Tracking**:
- DuckDuckGo doesn't track searches
- No personalized bubble
- Privacy-first search engine

### Rate Limiting

**Considerations**:
- Reasonable search frequency
- May encounter rate limits with excessive queries
- Designed for human-paced research

---

## Error Handling

### Common Issues

**No Results Found**
```
Action: Rephrase query with different keywords
Message: "I didn't find relevant results for that exact query. 
         Let me try a different search approach..."
```

**Limited Results**
```
Action: Broaden search or try related topics
Message: "Found limited information on this specific topic. 
         Here's what I found, plus some related information..."
```

**Outdated Information**
```
Action: Note dates and offer to search for updates
Message: "The most recent information I found is from [date]. 
         This may not reflect current conditions..."
```

---

## Tips for Users

### Getting Best Results

1. **Be Specific**: Include dates, locations, specific terms
2. **Ask Follow-Up**: Refine searches based on initial results
3. **Verify Important Info**: Ask for multiple sources
4. **Combine Searches**: Use with other agents for complete picture

### Example Interactions

**Good Query**:
"What are the current FHA loan limits for Washington DC in 2026?"

**Better Query**:
"Find the official FHA loan limits for Washington DC single-family homes, 
effective 2026, from government sources"

**Best Query**:
"I need to verify the 2026 FHA loan limits for DC. Please search for the 
official HUD announcement and any local news coverage explaining the changes."

---

## Maintenance & Updates

### Tool Configuration

Current settings:
- Max results: 10
- Safe search: STRICT
- Backend: DuckDuckGo

### Future Enhancements

Potential improvements:
- Result caching for common queries
- Search history and refinement
- Multi-source aggregation
- Specialized search filters

---

## Support & Troubleshooting

### Getting Help

If searches aren't returning good results:
1. Try rephrasing your question
2. Ask the agent to try alternative search terms
3. Be more specific with dates, locations, or context
4. Consider if information might be in internal systems (use different agent)

### Feedback

Help improve search capabilities:
- Report queries that don't return useful results
- Suggest search strategies that work well
- Identify topics that need specialized handling

---

**Last Updated**: February 2026  
**Agent Version**: 1.0.0  
**Tool Version**: ddgs 9.11.1
