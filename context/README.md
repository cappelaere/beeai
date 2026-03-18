# RealtyIQ Context Documentation

This directory contains comprehensive context documentation about RealtyIQ, intended for use when creating new agents, workflows, and features.

---

## Purpose

These context documents provide:
- **Application overview** - What RealtyIQ is and does
- **Domain knowledge** - GSA real estate auction business context
- **Use cases** - Real-world examples and scenarios
- **Technical architecture** - How the system is built
- **Best practices** - Patterns and guidelines
- **Examples** - Concrete code and query examples

---

## Files

### [CONTEXT.md](CONTEXT.md)

**Primary context document** - Comprehensive overview covering:
- Application intent and goals
- Business domain and use cases
- Technical architecture and stack
- Feature descriptions and examples
- Agent and workflow patterns
- Best practices and guidelines

**Use this when:**
- Creating new agents
- Designing workflows
- Planning new features
- Onboarding developers
- Writing documentation

### [USE_CASES.md](USE_CASES.md)

**Detailed use case library** - Specific scenarios with examples:
- Property research and analysis
- Bidder verification and compliance
- Workflow execution and management
- Document search and retrieval
- Business intelligence and reporting
- System administration

**Use this when:**
- Testing new features
- Writing agent SKILLS.md
- Creating workflow examples
- Training users
- Generating demo scenarios

### [AGENT_GUIDELINES.md](AGENT_GUIDELINES.md)

**Agent creation guidelines** - How to build effective agents:
- Agent design principles
- Tool selection criteria
- SKILLS.md template and structure
- Conversation patterns and tone
- Testing and validation
- Common pitfalls to avoid

**Use this when:**
- Creating agents in Agent Studio
- Writing agent configurations
- Defining agent capabilities
- Troubleshooting agent behavior

### [WORKFLOW_GUIDELINES.md](WORKFLOW_GUIDELINES.md)

**Workflow design guidelines** - How to build effective workflows:
- Workflow architecture patterns
- Task design and human review
- Agent orchestration strategies
- State management best practices
- Error handling and recovery
- Performance optimization

**Use this when:**
- Creating workflows in Workflow Studio
- Designing complex processes
- Integrating multiple agents
- Adding human approval steps

---

## How to Use

### For AI Agent Creation

When using Agent Studio or manually creating agents:

1. **Read**: `CONTEXT.md` - Understand the application
2. **Review**: `AGENT_GUIDELINES.md` - Learn agent patterns
3. **Reference**: `USE_CASES.md` - Find relevant examples
4. **Generate**: Use context in your SKILLS.md generation prompt

**Example prompt for Agent Studio:**
```
Create a [Domain] agent for RealtyIQ.

Context: [Paste relevant sections from CONTEXT.md]

The agent should:
- [Specific capabilities]
- Use tools: [Relevant tools]
- Handle queries like: [Example queries]
```

### For Workflow Design

When creating new workflows:

1. **Read**: `CONTEXT.md` - Understand workflow system
2. **Review**: `WORKFLOW_GUIDELINES.md` - Learn workflow patterns
3. **Identify**: Which agents participate in each step
4. **Define**: Human task requirements
5. **Implement**: Using BeeAI Framework patterns

### For Feature Development

When adding new features:

1. **Review**: Technical architecture section
2. **Follow**: Established UI patterns (Bootstrap 5)
3. **Integrate**: Observability (Langfuse traces)
4. **Test**: Add to test suite
5. **Document**: Update user and developer guides

---

## Maintenance

### When to Update

Update context documentation when:
- New major features are added
- Architecture changes significantly
- New agents or workflows are created
- Business requirements evolve
- User feedback reveals gaps

### Update Checklist

- [ ] Update CONTEXT.md with new features
- [ ] Add examples to USE_CASES.md
- [ ] Update guidelines if patterns change
- [ ] Increment version numbers
- [ ] Update "Last Modified" dates
- [ ] Cross-reference new documentation

---

## Related Documentation

- [Technical Specs](../docs/SPECS.md) - Complete technical specifications
- [User Guide](../docs/user-guide/README.md) - How to use RealtyIQ
- [Developer Guide](../docs/developer-guide/README.md) - How to develop and extend
- [Workflow Developer Guide](../workflows/docs/DEVELOPER_GUIDE.md) - Workflow creation guide

---

**Version**: 1.0  
**Created**: February 21, 2026  
**Purpose**: Support agent and workflow creation with comprehensive context
