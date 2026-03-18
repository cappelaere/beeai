"""
/help command handler - Display available commands
"""


def handle_help(request, args, session_key):
    """
    Display list of available commands.

    Args:
        request: Django HTTP request
        args: Command arguments (unused)
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    commands = [
        "Available Commands:",
        "",
        "General:",
        "  /help - Show this help message",
        "  /version - Show application version",
        "",
        "Agent Management:",
        "  /agent - Show current active agent",
        "  /agent list - List all available agents",
        "  /agent <name> - Switch to specified agent",
        "  /agent tools - Show tools for current agent",
        "",
        "Model Selection:",
        "  /model - Show current active model",
        "  /model <name> - Switch to specified model",
        "",
        "Cards:",
        "  /card list - List all assistant cards",
        "  /card list [number] - Show details of specific card",
        "  /card <number> - Execute card by ID",
        "  /card create - Create new empty card",
        "  /card update <id> <field> <value> - Update card field",
        "  /card delete <number> - Delete card",
        "",
        "Workflows:",
        "  /workflow list - List all available workflows",
        "  /workflow <number> - Show workflow details",
        "  /workflow execute <number> - Execute workflow",
        "",
        "Schedules:",
        "  /schedule list - List your scheduled workflows",
        "  /schedule add <workflow> [name] at <datetime> | every <N> min - Create schedule",
        "  /schedule show <id> - Show schedule details",
        "  /schedule edit <id> - Edit in UI",
        "  /schedule delete <id> - Delete schedule",
        "",
        "Tasks:",
        "  /task - List my pending tasks",
        "  /task <task_id> - Show task details",
        "  /task claim <task_id> - Claim a task",
        "  /task submit <task_id> <approve|deny> - Submit task decision",
        "",
        "Session:",
        "  /context - Show current session message history",
        "  /context clear - Clear session context",
        "",
        "System:",
        "  /metrics - Show dashboard metrics",
        "  /logs - View system logs",
        "  /logs current [lines] - View current log file",
        "  /logs <filename> [lines] - View specific log file",
        "  /cache - Show cache statistics",
        "  /cache clear - Clear all cached responses",
        "  /settings - Show current user preferences",
        "  /settings agent <name> - Set default agent",
        "  /settings model <name> - Set default model",
        "  /settings 508 <on|off> - Toggle Section 508 accessibility mode",
        "  /settings context <number> - Set context message count (0-50, default: 0)",
        "",
        "Documents:",
        "  /document list [pattern] - List all documents",
        "  /document search <query> [top_k] - Search documents",
        "  /document info <filename> - Get document information",
        "  /document reindex - Rebuild search index",
        "  /document stats - Show library statistics",
        "",
        "Prompts:",
        "  /prompt list - List all saved prompts",
        "  /prompt save <name> <text> - Save a prompt for reuse",
        "  /prompt <name> - Execute a saved prompt",
        "  /prompt delete <name> - Delete a saved prompt",
        "",
        "Diagrams:",
        "  /diagram list - List all available diagrams",
        "  /diagram <name> - View a specific diagram",
        "",
        "@Agent Mentions:",
        "  @<agent> <message> - Route message to specific agent",
        "  Example: @library search for documents",
        "",
        "All commands support keyboard-only navigation for accessibility.",
    ]

    return {"content": "\n".join(commands), "metadata": {"command": "help", "type": "system"}}
