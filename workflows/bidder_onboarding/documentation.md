# Bidder Onboarding & Verification Workflow - Documentation

The workflow diagram is defined in **workflow.bpmn**. This document describes decision points and behavior.

## Key Decision Points

### Decision 1: Input Validation
- ✅ All required fields present?
- ✅ Terms & age accepted?
- ✅ Valid email format?

### Decision 2: Property Status
- ✅ Property exists?
- ✅ Property is active (status_id=1)?
- ✅ Property is approved?

### Decision 3: SAM Compliance
- ✅ Not found on exclusions list?
- ✅ No active exclusions?

### Decision 4: OFAC Compliance
- ✅ No exact matches?
- ✅ No high-similarity matches (>85% in strict mode)?
- ⚠️ Potential match (60-85%)? → Manual review

### Decision 5: Auto-Approval
- ✅ Property settings allow auto-approval?
- ✅ User type eligible for auto-approval?
- ✅ Bid limit configured?

## Output States

| Status | Meaning | Next Steps |
|--------|---------|------------|
| **APPROVED** ✅ | Bidder passed all checks and auto-approved | Can bid immediately with set limit |
| **PENDING** ⏳ | Bidder passed checks but awaiting manual approval | Admin must review and approve |
| **REVIEW REQUIRED** ⚠️ | Potential compliance issue flagged | Admin must investigate and decide |
| **DENIED** ❌ | Failed compliance check or validation | Cannot bid; notify bidder of reason |

## Success Metrics

- **Approval Time**: < 5 seconds (vs hours manually)
- **Consistency**: 100% rule application
- **Audit Trail**: Complete documentation of every decision
- **False Positive Rate**: Configurable (strict vs standard mode)

---

## Diagram Legend

- 🟢 Green: Successful/Approved paths
- 🔴 Red: Denied/Failed paths
- 🟡 Yellow: Review required paths
- 🔵 Blue: Pending/Awaiting paths
- ⬜ Gray: Process steps
- 💎 Diamond: Decision points

---

Generated for RealtyIQ BeeAI Workflows
