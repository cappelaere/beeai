# Bidder Onboarding & Verification Workflow

## Overview

Automates the complete bidder registration and compliance verification process, including SAM.gov exclusions check and OFAC SDN list screening.

## Files

- **`USER_STORY.md`** - ⭐ Original user story with business value, acceptance criteria, and requirements
- **`workflow.py`** - Main workflow implementation (`BidderOnboardingWorkflow` class)
- **`metadata.yaml`** - Workflow configuration: name, icon, input schema, settings (YAML format)
- **`diagram.mmd`** - Main Mermaid diagram (single source of truth, plain text)
- **`documentation.md`** - Comprehensive documentation with Mermaid diagrams, use cases, and technical details
- **`__init__.py`** - Package initialization, loads YAML/diagram, exports workflow classes
- **`README.md`** - This file, quick reference guide

## Quick Start

### Import and Use

```python
from workflows.bidder_onboarding import BidderOnboardingWorkflow, BidderOnboardingState

# Create workflow instance
workflow = BidderOnboardingWorkflow()

# Execute workflow
result = await workflow.run(
    property_id=12345,
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    # ... other required fields
)
```

### Input Schema

See `documentation.md` for complete input field specifications.

Required fields:
- `property_id` (integer)
- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `terms_accepted` (boolean)
- `age_accepted` (boolean)

### Output States

- **APPROVED** ✅ - Bidder passed all checks and auto-approved
- **PENDING** ⏳ - Awaiting manual approval
- **REVIEW REQUIRED** ⚠️ - Potential compliance issue flagged
- **DENIED** ❌ - Failed compliance check

## Documentation

For detailed documentation, diagrams, and use cases, see [`documentation.md`](./documentation.md).

## Technical Details

- **Execution Time**: < 5 seconds
- **Category**: Compliance
- **Workflow Number**: #1
- **System Name**: `bidder_onboarding`

## Agents Used

- **SAM Agent**: Checks exclusions against SAM.gov database (138,885 records)
- **OFAC Agent**: Screens against OFAC SDN list (18,708 records)

## Testing

```bash
# Run workflow tests
pytest tests/test_bidder_onboarding_workflow.py

# Run standalone
python -m workflows.bidder_onboarding.workflow
```

## Related Documentation

- [Workflow Documentation Guide](../WORKFLOW_DOCUMENTATION_GUIDE.md)
- [Mermaid Syntax Guide](../MERMAID_SYNTAX_GUIDE.md)
- [Main Workflows README](../README.md)
