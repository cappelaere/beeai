"""
Command Dispatcher - Registry and execution engine for commands.
"""

import logging
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest

from agent_app.command_parser import Command

logger = logging.getLogger(__name__)

# Type alias for command handler functions
CommandHandler = Callable[[HttpRequest, list[str], str], dict[str, Any]]


class CommandDispatcher:
    """
    Central registry and dispatcher for slash commands.
    """

    def __init__(self):
        """Initialize empty handler registry."""
        self.handlers: dict[str, CommandHandler] = {}

    def register(self, command_name: str, handler: CommandHandler):
        """
        Register a command handler.

        Args:
            command_name: Name of the command (e.g., 'help', 'agent')
            handler: Function to handle the command
        """
        self.handlers[command_name] = handler
        logger.debug(f"Registered command handler: {command_name}")

    def dispatch(self, command: Command, request: HttpRequest, session_id: int) -> dict[str, Any]:
        """
        Execute a command and return formatted response.

        Args:
            command: Parsed Command object
            request: Django HTTP request
            session_id: Current chat session ID

        Returns:
            Dictionary with:
                - content: Response text
                - metadata: Additional info (command name, etc.)
                - Optional: execute_card, card_prompt, card_agent for card execution
                - Optional: error: True if command failed
        """
        command_name = command.name.lower()

        if command_name not in self.handlers:
            return {
                "content": f"Unknown command: /{command_name}\n\nType /help to see available commands.",
                "metadata": {"error": True, "command": command_name},
            }

        try:
            # Get session key from request
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Execute handler
            handler = self.handlers[command_name]
            result = handler(request, command.args, session_key)

            # Ensure result has required fields
            if "content" not in result:
                result["content"] = ""
            if "metadata" not in result:
                result["metadata"] = {}

            # Add command name to metadata if not present
            if "command" not in result["metadata"]:
                result["metadata"]["command"] = command_name

            return result

        except Exception as e:
            logger.error(f"Error executing command /{command_name}: {e}", exc_info=True)
            return {
                "content": f"Error executing command: {str(e)}",
                "metadata": {"error": True, "command": command_name, "exception": str(e)},
            }

    def get_available_commands(self) -> list[str]:
        """
        Get list of registered command names.

        Returns:
            List of command names
        """
        return sorted(self.handlers.keys())


# Global dispatcher instance
dispatcher = CommandDispatcher()


def register_all_handlers():
    """
    Register all command handlers with the dispatcher.
    Called on module import to populate the registry.
    """
    try:
        from agent_app.commands.agent import handle_agent
        from agent_app.commands.cache import handle_cache
        from agent_app.commands.card import handle_card
        from agent_app.commands.context import handle_context
        from agent_app.commands.diagram import handle_diagram
        from agent_app.commands.document import handle_document
        from agent_app.commands.help import handle_help
        from agent_app.commands.logs import handle_logs
        from agent_app.commands.metrics import handle_metrics
        from agent_app.commands.model import handle_model
        from agent_app.commands.prompt import handle_prompt
        from agent_app.commands.schedule import handle_schedule
        from agent_app.commands.settings import handle_settings
        from agent_app.commands.task import handle_task
        from agent_app.commands.version import handle_version
        from agent_app.commands.workflow import handle_workflow

        # Register all handlers
        dispatcher.register("help", handle_help)
        dispatcher.register("schedule", handle_schedule)
        dispatcher.register("version", handle_version)
        dispatcher.register("agent", handle_agent)
        dispatcher.register("model", handle_model)
        dispatcher.register("card", handle_card)
        dispatcher.register("workflow", handle_workflow)
        dispatcher.register("context", handle_context)
        dispatcher.register("metrics", handle_metrics)
        dispatcher.register("settings", handle_settings)
        dispatcher.register("document", handle_document)
        dispatcher.register("prompt", handle_prompt)
        dispatcher.register("diagram", handle_diagram)
        dispatcher.register("logs", handle_logs)
        dispatcher.register("cache", handle_cache)
        dispatcher.register("task", handle_task)

        logger.info(f"Registered {len(dispatcher.handlers)} command handlers")

    except ImportError as e:
        logger.warning(f"Could not import some command handlers: {e}")


# Auto-register handlers on module import
register_all_handlers()
