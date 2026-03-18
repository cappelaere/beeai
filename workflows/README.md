# BeeAI Dynamic Workflows for RealtyIQ

This directory contains BeeAI Framework workflow implementations that orchestrate multiple agents and tools to automate complex, multi-step processes in the GSA Real Estate Sales (GRES) application.

## What are BeeAI Workflows?

BeeAI Workflows provide a flexible and extensible component for managing and executing structured sequences of tasks. They enable:

- **Dynamic Execution**: Steps can direct the flow based on state or results
- **Validation**: Type-safe state management with Pydantic models
- **Modularity**: Steps can be standalone or invoke nested workflows
- **Observability**: Emit events during execution for tracking and error handling
- **Multi-Agent Orchestration**: Coordinate multiple specialized agents seamlessly

## Why Use Workflows?

### Current Challenge
RealtyIQ has 7 specialized agents (GRES, SAM, OFAC, Bidder Verification, IDV, Library, Section 508) with 39+ tools. Users must:
- Manually switch between agents
- Remember which agent has which capabilities
- Manually combine results from multiple sources
- Track multi-step processes themselves

### Workflow Solution
Workflows automate complex, multi-step processes by:
- **Orchestrating multiple agents** in a single unified process
- **Managing state** across steps with type safety
- **Implementing business logic** with conditional branching
- **Providing audit trails** with comprehensive event logging
- **Ensuring consistency** in critical business processes

## Documentation

### Quick Links
- **[How to start a new workflow](docs/DEVELOPER_GUIDE.md#how-to-start-a-new-workflow)** - Use **Workflow Studio** (admin UI, AI-generated BPMN + code) or create manually
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Complete development guide
- **[Workflow Examples](EXAMPLES.md)** - 7 detailed workflow examples
- **[Templates](templates/)** - Templates for manual workflow creation
- **[Implementation History](docs/IMPLEMENTATION_HISTORY.md)** - Historical details

### Individual Workflows
- **[Bidder Onboarding](bidder_onboarding/)** - Automated bidder verification (implemented)
- **[Property Due Diligence](property_due_diligence/)** - Property research automation (implemented)

---

## Architecture

### State Management
Each workflow defines a Pydantic model that:
- Holds data passed between steps
- Provides type validation and safety
- Persists throughout workflow execution

```python
from pydantic import BaseModel

class BidderOnboardingState(BaseModel):
    bidder_name: str
    property_id: int
    registration_data: dict
    sam_check_result: dict | None = None
    ofac_check_result: dict | None = None
    is_eligible: bool = False
    requires_manual_review: bool = False
```

### Step Functions
Steps are functions that:
- Take the current state as input
- Can modify the state
- Return the name of the next step or a reserved value

```python
async def check_sam_compliance(state: BidderOnboardingState):
    """Check SAM.gov exclusions"""
    result = await sam_agent.check_entity_status(state.bidder_name)
    state.sam_check_result = result
    return "check_ofac_compliance"  # Next step
```

### Flow Control
Each step returns:
- **Step name**: `"next_step_name"` - Go to specific step
- **`Workflow.NEXT`**: Proceed to next step in order
- **`Workflow.SELF`**: Repeat the current step (loops)
- **`Workflow.END`**: End workflow execution

### Multi-Agent Coordination
Workflows can call tools from any registered agent:

```python
# Call tools from different agents
sam_result = await sam_agent.check_entity_status(name)
ofac_result = await ofac_agent.check_bidder_eligibility(name)
property_info = await gres_agent.get_property_detail(property_id)

# Combine results with business logic
state.is_eligible = sam_result["passed"] and ofac_result["eligible"]
```

## Available Workflows

### Implemented Workflows

1. **[Bidder Onboarding Workflow](bidder_onboarding_workflow.py)** ✅
   - Automates complete bidder registration and verification
   - Orchestrates SAM, OFAC, and GRES agents
   - Implements compliance screening business rules
   - Handles auto-approval logic
   - Comprehensive audit trail

### Planned Workflows

See [EXAMPLES.md](EXAMPLES.md) for detailed examples of additional high-value workflows:

2. **Property Due Diligence Workflow** - Multi-agent property research
3. **Property Valuation & Market Analysis Workflow** - Parallel data analysis
4. **Conversational Research Assistant Workflow** - Stateful interactions with memory
5. **Auction Lifecycle State Machine Workflow** - Complete auction management
6. **Compliance Audit Trail Workflow** - Comprehensive compliance reporting
7. **Document Intelligence Extraction Workflow** - Automated document processing

## Usage

### Running a Workflow

```python
from workflows.bidder_onboarding_workflow import BidderOnboardingWorkflow

# Create workflow instance
workflow = BidderOnboardingWorkflow()

# Run with initial state
result = await workflow.run(
    bidder_name="John Smith",
    property_id=12345,
    registration_data={
        "email": "john@example.com",
        "phone": "555-1234",
        "user_type": "Investor"
    }
)

# Access results
print(f"Eligible: {result.state.is_eligible}")
print(f"Status: {result.state.approval_status}")
print(f"Requires Review: {result.state.requires_manual_review}")
```

### With Observability

```python
# Run with event monitoring
result = await workflow.run(
    bidder_name="John Smith",
    property_id=12345
).observe((emitter) => {
    emitter.on("start", (data) => console.log(f"Starting: {data.step}"))
    emitter.on("success", (data) => console.log(f"Completed: {data.step}"))
    emitter.on("error", (data) => console.log(f"Error in: {data.step}"))
})
```

### Integration with Django Views

```python
# In views.py
from workflows.bidder_onboarding_workflow import BidderOnboardingWorkflow

async def register_bidder(request):
    workflow = BidderOnboardingWorkflow()
    
    result = await workflow.run(
        bidder_name=request.POST['name'],
        property_id=request.POST['property_id'],
        registration_data=request.POST.dict()
    )
    
    if result.state.is_eligible:
        # Create bid registration record
        # Send approval notification
        return JsonResponse({"status": "approved"})
    else:
        # Handle rejection/review
        return JsonResponse({"status": "requires_review"})
```

## Workflow Design Patterns

### 1. Sequential Processing
Linear flow through steps in order:
```python
workflow.add_step("step1", step1_handler)
workflow.add_step("step2", step2_handler)
workflow.add_step("step3", step3_handler)
# Returns Workflow.NEXT for each step
```

### 2. Conditional Branching
Dynamic routing based on state:
```python
async def decision_step(state):
    if state.condition_met:
        return "success_path"
    else:
        return "alternative_path"
```

### 3. Loops and Retries
Repeat steps until condition is met:
```python
async def retry_step(state):
    if state.attempts < 3 and not state.success:
        state.attempts += 1
        return Workflow.SELF  # Retry this step
    return "next_step"
```

### 4. Parallel Processing
Execute multiple agents simultaneously:
```python
# Start multiple async tasks
sam_task = asyncio.create_task(sam_check())
ofac_task = asyncio.create_task(ofac_check())
property_task = asyncio.create_task(property_lookup())

# Wait for all to complete
await asyncio.gather(sam_task, ofac_task, property_task)
```

### 5. Nested Workflows
Workflows can invoke other workflows:
```python
compliance_workflow = ComplianceWorkflow()
workflow.add_step("run_compliance", compliance_workflow.as_step())
```

## Development Guidelines

### Creating a New Workflow

1. **Define State Model**
   ```python
   class MyWorkflowState(BaseModel):
       # Input fields (required)
       input_data: str
       
       # Working fields (optional, with defaults)
       intermediate_result: dict | None = None
       
       # Output fields (optional, with defaults)
       final_result: str | None = None
   ```

2. **Implement Step Functions**
   ```python
   async def my_step(state: MyWorkflowState) -> str:
       # Process data
       # Update state
       # Return next step name or Workflow.END
       return "next_step"
   ```

3. **Create Workflow Class**
   ```python
   class MyWorkflow:
       def __init__(self):
           self.workflow = Workflow(MyWorkflowState, name="MyWorkflow")
           self.workflow.add_step("step1", self.step1_handler)
           self.workflow.add_step("step2", self.step2_handler)
       
       async def run(self, **kwargs):
           return await self.workflow.run(MyWorkflowState(**kwargs))
   ```

4. **Add Tests**
   ```python
   async def test_my_workflow():
       workflow = MyWorkflow()
       result = await workflow.run(input_data="test")
       assert result.state.final_result is not None
   ```

### Best Practices

- **Type Safety**: Use Pydantic models for all state
- **Idempotency**: Steps should be idempotent where possible
- **Error Handling**: Use try/except in steps and emit error events
- **Observability**: Emit events at key points for monitoring
- **Documentation**: Include docstrings explaining step purpose
- **Testing**: Write unit tests for individual steps and integration tests for workflows
- **State Validation**: Validate state at each step to catch errors early

## Integration with Existing System

### Agent Registry Integration
```python
from agents.registry import get_agent_config

# Load agents dynamically
sam_agent = get_agent_config("sam")
ofac_agent = get_agent_config("ofac")
```

### Tool Calling
```python
# Import and call existing tools
from tools.list_properties import list_properties
from agents.sam.tools.check_entity_status import check_entity_status

# Use in workflow steps
properties = await list_properties(site_id=3)
sam_result = await check_entity_status(name="John Smith")
```

### Database Integration
```python
# Access Django models
from auction.models import BidRegistration, PropertySettings

# Create/update records from workflow
registration = BidRegistration.objects.create(
    property_id=state.property_id,
    user_id=state.user_id,
    is_approved=2 if state.is_eligible else 1
)
```

### Langfuse Observability
```python
# Workflows automatically integrate with existing Langfuse setup
# Events are emitted for each step execution
# Traces show complete workflow execution path
```

## File Structure

```
workflows/
├── README.md                          # This file
├── EXAMPLES.md                        # Detailed workflow examples
├── __init__.py                        # Package initialization
├── bidder_onboarding_workflow.py     # Implemented: Bidder onboarding
├── property_due_diligence.py         # Planned: Property research
├── property_valuation.py             # Planned: Market analysis
├── conversational_research.py        # Planned: Stateful chat
├── auction_lifecycle.py              # Planned: Auction state machine
├── compliance_audit.py               # Planned: Audit reporting
├── document_intelligence.py          # Planned: Document processing
└── tests/
    ├── test_bidder_onboarding.py
    └── ...
```

## Benefits

### For Users
- **Simplified Interface**: One command instead of multiple agent switches
- **Consistent Results**: Standardized business logic across all executions
- **Faster Processing**: Automated multi-step processes save time
- **Better Accuracy**: Reduced human error in complex processes

### For Developers
- **Reusable Components**: Modular steps can be shared across workflows
- **Type Safety**: Pydantic models catch errors at development time
- **Testability**: Individual steps and complete workflows are easily tested
- **Observability**: Built-in event system for monitoring and debugging

### For Business
- **Compliance**: Standardized processes ensure regulatory requirements are met
- **Audit Trail**: Complete execution history for every workflow run
- **Scalability**: Workflows can process thousands of requests consistently
- **Flexibility**: Easy to modify business logic as requirements change

## Resources

- **BeeAI Framework Documentation**: https://framework.beeai.dev/modules/workflows
- **BeeAI GitHub**: https://github.com/i-am-bee/beeai-framework
- **Python Examples**: https://github.com/i-am-bee/beeai-framework/tree/main/python/examples/workflows
- **RealtyIQ Documentation**: `/docs/README.md`
- **Agent Registry**: `/agents/README.md` (if exists)

## Support

For questions or issues with workflows:
1. Review existing workflow implementations in this directory
2. Check [EXAMPLES.md](EXAMPLES.md) for patterns
3. Consult BeeAI Framework documentation
4. Review agent SKILLS.md files for tool capabilities

---

**Ready to automate complex business processes with BeeAI Workflows!** 🚀
