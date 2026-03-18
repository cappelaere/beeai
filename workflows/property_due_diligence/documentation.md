# Property Due Diligence Workflow Diagram

This document contains the visual workflow diagram for the Property Due Diligence automation process.

## Workflow Overview

The Property Due Diligence Workflow automates comprehensive property research by orchestrating multiple agents to gather and synthesize information from various sources in parallel.

## Business Value

- **Faster Closings**: Accelerate due diligence from days to hours
- **Comprehensive Analysis**: Never miss critical information
- **Cost Savings**: Reduce manual research time by 80%
- **Better Decisions**: Synthesized insights from all available data

## Detailed Step Descriptions

### 1. Get Property Details
**Agent**: GRES Agent  
**Purpose**: Retrieve comprehensive property information including location, size, condition, zoning, and current status.  
**Output**: Property details object with all available information.

### 2. Parallel Research Tasks
Four research tasks execute simultaneously to maximize efficiency:

#### 2a. Find Comparable Sales
**Agent**: GRES Agent  
**Purpose**: Find 3-5 similar properties with recent sales data.  
**Criteria**: Similar location, size, condition, and type.  
**Output**: List of comparable properties with sale prices and dates.

#### 2b. Search Related Documents
**Agent**: Library Agent  
**Purpose**: Search document repository for relevant files.  
**Document Types**:
- Appraisals
- Tax Assessments
- Environmental Reports
- Title Documents
- Surveys

**Output**: List of found documents with metadata.

#### 2c. Check Compliance
**Agent**: SAM Agent  
**Purpose**: Screen sellers, brokers, and agents against federal exclusion lists.  
**Checks**: SAM.gov exclusions list (138,885+ records).  
**Output**: Compliance status for all parties.

#### 2d. Get Auction History
**Agent**: GRES Agent  
**Purpose**: Retrieve complete auction history for the property.  
**Information**: Previous listings, bid activity, outcomes, and notes.  
**Output**: Historical auction data.

### 3. Assess Risks
**Purpose**: Analyze all gathered information to identify risk factors.  
**Risk Factors Evaluated**:
- Compliance issues detected
- Limited documentation availability
- Previous unsuccessful auctions
- Lack of comparable sales data

**Risk Level Determination**:
- **HIGH**: 3+ risk factors identified
- **MEDIUM**: 1-2 risk factors identified
- **LOW**: No significant risk factors

### 4. Generate Report
**Purpose**: Synthesize all findings into a comprehensive due diligence report.  

**Report Sections**:
1. Property Details Summary
2. Comparable Sales Analysis
3. Documentation Review
4. Compliance Screening Results
5. Auction History
6. Risk Factors Identified
7. Recommendations

**Recommendations Based on Risk**:
- **High Risk**: Recommend thorough manual review, additional investigations
- **Medium Risk**: Proceed with caution, monitor closely, address specific concerns
- **Low Risk**: Proceed with standard auction process

## Agents Involved

| Agent | Role | Data Provided |
|-------|------|---------------|
| **GRES Agent** | Primary data source | Property details, comparable sales, auction history |
| **Library Agent** | Document search | Appraisals, assessments, reports, title docs |
| **SAM Agent** | Compliance screening | Federal exclusion list checks |

## Performance Characteristics

- **Parallel Execution**: 4 research tasks run simultaneously
- **Expected Duration**: 10-30 seconds (vs. hours manually)
- **Agents Used**: 2-3 agents orchestrated
- **API Calls**: ~5-8 calls total
- **Time Savings**: 80% reduction vs. manual process

## Error Handling

The workflow includes comprehensive error handling:
- Each parallel task can fail independently without stopping the workflow
- Missing data results in partial reports with recommendations to obtain it
- Agent unavailability is gracefully handled with appropriate messaging
- All errors are logged and included in the final report

## Output Format

```json
{
  "property_id": 12345,
  "risk_level": "medium",
  "risk_factors": [
    "Previous auction attempts were unsuccessful",
    "No comparable sales data available for valuation"
  ],
  "findings_summary": "# Property Due Diligence Report...",
  "recommendations": [
    "⚡ MEDIUM RISK: Proceed with caution...",
    "Conduct market analysis to establish reserve price"
  ],
  "checks_performed": [
    "property_details_retrieved",
    "comparable_sales_analyzed",
    "documents_searched",
    "compliance_verified",
    "auction_history_reviewed",
    "risk_assessment_completed",
    "report_generated"
  ],
  "property_details": {...},
  "comparable_sales": [...],
  "documents_found": [...],
  "compliance_checks": {...},
  "auction_history": [...]
}
```

## Integration Points

### Input Requirements
- **property_id** (required): Integer ID of property to research

### Output Usage
- Display report in web UI
- Email to stakeholders
- Attach to property record
- Support auction decision-making
- Archive for audit trail

### Triggered By
- Manual request from property management UI
- Automated trigger when property moves to "Pending Approval" status
- Scheduled re-verification before auction launch
- API call from external system

## Future Enhancements

1. **AI Synthesis**: Use LLM to generate natural language summary
2. **Predictive Scoring**: ML model to predict auction success probability
3. **Visual Reports**: Generate PDF with charts and visualizations
4. **Real-time Updates**: Subscribe to data changes and auto-refresh
5. **Comparison Tool**: Compare multiple properties side-by-side

---

**Related Files**:
- Implementation: `property_due_diligence_workflow.py`
- Examples: `EXAMPLES.md` (Section 2)
- Agent Skills: `agents/*/SKILLS.md`
