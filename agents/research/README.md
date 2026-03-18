# Research Agent (🔍)

**Web Search Specialist for Real-Time Information**

The Research Agent is a specialized assistant that enables RealtyIQ users to search the internet for current information, market trends, company background, regulations, and general research topics using DuckDuckGo search.

---

## Overview

**Agent ID**: `research`  
**Display Name**: Research  
**Icon**: 🔍  
**Primary Tool**: DuckDuckGo Search (no API key required)

### Key Features

- 🌐 **Web Search**: Search the internet for current information
- 🔒 **Privacy-First**: DuckDuckGo doesn't track searches
- ✅ **Safe Search**: Content filtering enabled by default
- 🎯 **Focused Results**: Up to 10 relevant results per query
- 📚 **Source Citation**: Always provides URLs and source information

---

## When to Use Research Agent

### Best For

- **Current Events**: Latest news and developments
- **Market Research**: Real estate trends, property values, market analysis
- **Regulations**: Federal and state regulations, GSA policies
- **Company Information**: Background checks, company profiles
- **General Knowledge**: Any question requiring external web sources
- **Verification**: Cross-checking information from public sources

### Not Suitable For

- Internal RealtyIQ data (use GRES Agent)
- Bidder compliance checks (use Bidder Verification Agent)
- Document search in uploaded files (use Library Agent)
- Workflow execution (use Flo Agent)
- Paywalled or restricted content

---

## How It Works

### Search Process

1. **User asks a question** requiring external information
2. **Agent analyzes** the query and formulates search terms
3. **DuckDuckGo search** retrieves up to 10 results
4. **Agent summarizes** findings and cites sources
5. **User can refine** search with follow-up questions

### Example Workflow

```
User: "What are current mortgage rates for VA loans?"

Agent: 
1. Uses DuckDuckGoSearchTool
2. Searches "VA loan mortgage rates 2026"
3. Reviews top results
4. Summarizes current rates
5. Provides source URLs
```

---

## Use Cases

### Real Estate Research

**Market Trends**
- Property value trends by region
- Market forecasts and analysis
- Investment opportunities
- Neighborhood demographics

**Property Information**
- Comparable sales research
- Area development plans
- Zoning information
- School district ratings

### Compliance & Regulations

**Federal Requirements**
- GSA auction regulations
- Federal property disposal rules
- HUD guidelines
- FHA/VA loan requirements

**State & Local**
- State real estate laws
- Local building codes
- Disclosure requirements
- Property tax information

### Business Intelligence

**Company Research**
- Company background and history
- News and press releases
- Industry reputation
- Financial information (public)

**Competitive Analysis**
- Market competitors
- Industry trends
- Best practices
- Emerging technologies

### General Research

**News & Updates**
- Real estate industry news
- Federal policy changes
- Market reports
- Economic indicators

**Educational Content**
- Process guides and how-tos
- Industry terminology
- Training resources
- Best practice articles

---

## Technical Details

### Tools Available

1. **DuckDuckGoSearchTool**
   - Max results: 10 per search
   - Safe search: STRICT mode
   - No API key required
   - Privacy-focused (no tracking)

2. **ThinkTool**
   - Plan complex research strategies
   - Break down multi-part questions
   - Evaluate result quality

### Configuration

```python
DuckDuckGoSearchTool(
    max_results=10,
    safe_search="STRICT"
)
```

### Network Requirements

- Requires outbound internet access
- Uses DuckDuckGo's public API
- No authentication needed
- Rate limits may apply with excessive queries

---

## Best Practices

### Crafting Effective Queries

**Do's**:
- Be specific with dates, locations, terms
- Use quotes for exact phrases
- Include context in your question
- Ask follow-up questions to refine results

**Don'ts**:
- Don't use overly broad queries
- Avoid asking for internal RealtyIQ data
- Don't expect access to paywalled content
- Don't rely on single sources for critical decisions

### Example Queries

**Good**: "What are the 2026 FHA loan limits for Washington DC?"  
**Better**: "Find official HUD announcement for 2026 FHA loan limits in DC metro area"

**Good**: "Recent federal real estate news"  
**Better**: "Latest GSA property disposal announcements from the past month"

### Interpreting Results

- Verify important information from multiple sources
- Check publication dates for currency
- Prioritize official government and industry sources
- Note when information may be outdated

---

## Integration with Other Agents

### Complementary Usage

**Research + GRES**:
- External market data + Internal property data
- Industry trends + Actual auction performance

**Research + Library**:
- Web sources + Internal documents
- Current news + Historical context

**Research + Flo**:
- Workflow best practices + Actual workflows
- Industry patterns + Internal processes

### Workflow Examples

**Due Diligence Workflow**:
1. GRES → Get property details
2. Research → Market comparables
3. Research → Area regulations
4. Library → Review related documents

**Compliance Workflow**:
1. Research → Latest regulations
2. Bidder Verification → Run checks
3. Research → Company background
4. Library → Policy documents

---

## Limitations & Considerations

### Content Limitations

**Can Access**:
- Public web pages
- News articles
- Government websites
- Public company information
- Academic resources

**Cannot Access**:
- Paywalled content
- Private databases
- Subscription services
- Internal networks
- Confidential records

### Accuracy Considerations

- Search results are from third-party sources
- Agent cannot guarantee accuracy of external content
- Always verify critical information
- Note publication dates
- Cross-reference important findings

### Rate Limiting

DuckDuckGo may rate-limit excessive searches. For best performance:
- Ask focused, specific questions
- Avoid rapid-fire repeated searches
- Allow agent to process and summarize results

---

## Security & Privacy

### Privacy Features

- **No Tracking**: DuckDuckGo doesn't track searches
- **No User Profiling**: Results aren't personalized/filtered by history
- **Safe Search**: Content filtering enabled
- **No Data Storage**: Search history not retained

### Safe Search

Safe Search is set to STRICT mode:
- Filters explicit content
- Family-friendly results
- Inappropriate content blocked
- Ensures workplace-appropriate results

---

## Performance

### Response Times

- **Search Execution**: 1-3 seconds typical
- **Result Processing**: 2-5 seconds
- **Total Response**: 5-10 seconds average

### Result Quality

- Returns top 10 most relevant results
- Ranked by DuckDuckGo's algorithm
- Filtered for safety and appropriateness
- Agent summarizes and contextualizes findings

---

## Troubleshooting

### Common Issues

**No Results Found**
- Try rephrasing the query
- Use different keywords
- Broaden the search scope

**Poor Quality Results**
- Be more specific with search terms
- Add context (dates, locations)
- Try alternative phrasing

**Outdated Information**
- Specify current year in search
- Look for "latest" or "current" in query
- Check publication dates in results

### Getting Help

If searches aren't working well:
1. Try different search terms
2. Ask agent to refine the search
3. Be more specific about what you're looking for
4. Consider if information is in internal systems

---

## Future Enhancements

### Potential Improvements

- Search result caching
- Multi-source aggregation
- Advanced filtering options
- Search history and refinement
- Specialized real estate search modes

---

## Documentation

- **[SKILLS.md](SKILLS.md)**: Detailed capabilities and examples
- **[Plan](/.cursor/plans/)**: Implementation plan and architecture
- **[Agent Guidelines](/context/AGENT_GUIDELINES.md)**: General agent best practices

---

## Support

For issues or questions:
- Review the SKILLS.md documentation
- Try rephrasing your search query
- Contact the development team
- Submit feedback through RealtyIQ interface

---

**Created**: February 2026  
**Version**: 1.0.0  
**Status**: Active  
**Maintained By**: RealtyIQ Development Team
