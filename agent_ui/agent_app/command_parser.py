"""
Command Parser for slash commands and @Agent mentions.
Provides 508-compliant command parsing for accessibility.
"""

import re
import shlex


class Command:
    """Represents a parsed command."""

    def __init__(self, cmd_type: str, name: str, args: list[str], raw_text: str):
        """
        Initialize a command.

        Args:
            cmd_type: Type of command ('slash' or 'at_mention')
            name: Command name (e.g., 'help', 'agent', 'library')
            args: List of command arguments
            raw_text: Original command text
        """
        self.cmd_type = cmd_type
        self.name = name
        self.args = args
        self.raw_text = raw_text

    def __repr__(self):
        return f"Command(type={self.cmd_type}, name={self.name}, args={self.args})"


def parse_command(text: str) -> tuple[Command | None, str | None]:
    """
    Parse command from text input.

    Detects both slash commands (/command) and @Agent mentions.

    Args:
        text: Input text to parse

    Returns:
        Tuple of (Command object or None, remaining text or original text)

    Examples:
        >>> parse_command("/help")
        (Command(type=slash, name=help, args=[]), None)

        >>> parse_command("@library search for documents")
        (Command(type=at_mention, name=library, args=[]), "search for documents")

        >>> parse_command("regular message")
        (None, "regular message")
    """
    if not text or not text.strip():
        return None, text

    text = text.strip()

    # Check for @Agent mention first (higher priority)
    at_match = re.match(r"^@(\w+)\s*(.*)", text, re.IGNORECASE)
    if at_match:
        agent_name = at_match.group(1)
        remaining_text = at_match.group(2).strip()

        command = Command(cmd_type="at_mention", name=agent_name, args=[], raw_text=text)
        return command, remaining_text

    # Check for slash command
    if text.startswith("/"):
        # Remove leading slash
        command_text = text[1:].strip()

        if not command_text:
            # Just a slash, not a valid command
            return None, text

        # Parse command and arguments
        # Use shlex to handle quoted arguments
        try:
            parts = shlex.split(command_text)
        except ValueError:
            # If shlex fails (e.g., unclosed quote), fall back to simple split
            parts = command_text.split()

        if not parts:
            return None, text

        command_name = parts[0].lower()
        command_args = parts[1:] if len(parts) > 1 else []

        command = Command(cmd_type="slash", name=command_name, args=command_args, raw_text=text)
        return command, None

    # Not a command
    return None, text


def is_command(text: str) -> bool:
    """
    Check if text starts with a command indicator.

    Args:
        text: Input text to check

    Returns:
        True if text starts with / or @, False otherwise
    """
    if not text:
        return False

    text = text.strip()
    return text.startswith(("/", "@"))
