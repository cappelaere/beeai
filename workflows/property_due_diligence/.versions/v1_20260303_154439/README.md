# Property Due Diligence Workflow

## Overview

Automates comprehensive property research and risk assessment by executing multiple research tasks in parallel: comparable sales analysis, document search, compliance checks, and auction history review.

## Files

- **`USER_STORY.md`** - ⭐ Original user story with business value, acceptance criteria, and requirements
- **`workflow.py`** - Main workflow implementation (`PropertyDueDiligenceWorkflow` class)
- **`metadata.yaml`** - Workflow configuration: name, icon, input schema, settings (YAML format)
- **`diagram.mmd`** - Main Mermaid diagram (single source of truth, plain text)
- **`documentation.md`** - Comprehensive documentation with Mermaid diagrams, use cases, and technical details
- **`__init__.py`** - Package initialization, loads YAML/diagram, exports workflow classes
- **`README.md`** - This file, quick reference guide

## Quick Start

### Import and Use

```python
from workflows.property_due_diligence import PropertyDueDiligenceWorkflow, PropertyDueDiligenceState

# Create workflow instance
workflow = PropertyDueDiligenceWorkflow()

# Execute workflow
result = await workflow.run(property_id=12345)
```

### Input Schema

Required fields:
- `property_id` (integer) - Property ID to research and analyze

### Output States

- **READY FOR AUCTION** ✅ - Low risk, ready to proceed
- **PROCEED WITH CAUTION** ⚠️ - Medium risk, review recommended
- **FLAG FOR REVIEW** 🚩 - High risk, manual review required

### Research Components

1. **Comparable Sales** - Finds similar properties and analyzes pricing
2. **Document Search** - Searches for relevant property documents
3. **Compliance Check** - Verifies regulatory compliance
4. **Auction History** - Reviews past auction performance

## Documentation

For detailed documentation, diagrams, and use cases, see [`documentation.md`](./documentation.md).

## Technical Details

- **Execution Time**: 10-30 seconds
- **Category**: Property Analysis
- **Workflow Number**: #2
- **System Name**: `property_due_diligence`
- **Parallel Execution**: Yes (4 concurrent research tasks)

## Key Features

- ✅ **Parallel Processing** - Multiple research tasks run simultaneously
- ✅ **Comprehensive Analysis** - Aggregates data from multiple sources
- ✅ **Risk Assessment** - Automated risk level determination
- ✅ **Detailed Reporting** - Generates comprehensive due diligence report

## Agents Used

The workflow orchestrates multiple agents to gather property information:
- Document search agents
- Comparable sales analysis
- Compliance verification
- Historical data retrieval

## Testing

```bash
# Run workflow tests
pytest tests/test_property_due_diligence_workflow.py

# Run standalone
python -m workflows.property_due_diligence.workflow
```

## Performance

- Average execution: 15-20 seconds
- 4 tasks run in parallel
- Significant time savings vs. manual research (hours → seconds)

## Related Documentation

- [Workflow Documentation Guide](../WORKFLOW_DOCUMENTATION_GUIDE.md)
- [Mermaid Syntax Guide](../MERMAID_SYNTAX_GUIDE.md)
- [Main Workflows README](../README.md)
