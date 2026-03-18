"""
/prompt command handler - Manage saved prompts
"""


def _get_saved_prompts(pref):
    """Load saved prompts from user preferences."""
    import json

    if not pref.saved_prompts:
        return {}

    try:
        return json.loads(pref.saved_prompts)
    except (json.JSONDecodeError, TypeError):
        return {}


def _handle_prompt_list(saved_prompts):
    """List all saved prompts."""
    if not saved_prompts:
        return {
            "content": "No saved prompts. Use '/prompt save <name> <text>' to save a prompt.",
            "metadata": {"command": "prompt list", "count": 0},
        }

    lines = [f"📝 Saved Prompts ({len(saved_prompts)} total)", ""]
    for name, text in saved_prompts.items():
        preview = text[:60] + "..." if len(text) > 60 else text
        lines.append(f"  • {name}")
        lines.append(f"    {preview}")
        lines.append("")

    lines.append("Use '/prompt <name>' to execute a saved prompt")

    return {
        "content": "\n".join(lines),
        "metadata": {"command": "prompt list", "count": len(saved_prompts)},
    }


def _handle_prompt_save(args, saved_prompts, pref):
    """Save a new prompt."""
    import json

    if len(args) < 3:
        return {"content": "Usage: /prompt save <name> <text>", "metadata": {"error": True}}

    prompt_name = args[1]
    prompt_text = " ".join(args[2:])

    if not prompt_text.strip():
        return {"content": "Error: Prompt text cannot be empty", "metadata": {"error": True}}

    saved_prompts[prompt_name] = prompt_text
    pref.saved_prompts = json.dumps(saved_prompts)
    pref.save()

    return {
        "content": (f"✓ Prompt '{prompt_name}' saved\n\nUse '/prompt {prompt_name}' to execute it"),
        "metadata": {"command": "prompt save", "name": prompt_name},
    }


def _handle_prompt_delete(args, saved_prompts, pref):
    """Delete a saved prompt."""
    import json

    if len(args) < 2:
        return {"content": "Usage: /prompt delete <name>", "metadata": {"error": True}}

    prompt_name = args[1]

    if prompt_name not in saved_prompts:
        return {"content": f"Error: Prompt '{prompt_name}' not found", "metadata": {"error": True}}

    del saved_prompts[prompt_name]
    pref.saved_prompts = json.dumps(saved_prompts)
    pref.save()

    return {
        "content": f"✓ Prompt '{prompt_name}' deleted",
        "metadata": {"command": "prompt delete", "name": prompt_name},
    }


def _handle_prompt_execute(prompt_name, saved_prompts):
    """Execute a saved prompt."""
    if prompt_name not in saved_prompts:
        return {
            "content": (
                f"Error: Prompt '{prompt_name}' not found\n\n"
                f"Available prompts:\n" + "\n".join(f"  • {name}" for name in saved_prompts)
                if saved_prompts
                else "No saved prompts available. Use '/prompt save <name> <text>' to create one."
            ),
            "metadata": {"error": True},
        }

    return {
        "content": f"Executing saved prompt: {prompt_name}",
        "metadata": {"command": "prompt execute", "name": prompt_name, "execute_prompt": True},
        "prompt_text": saved_prompts[prompt_name],
    }


def handle_prompt(request, args, session_key):
    """
    Handle prompt-related commands.

    Commands:
        /prompt list - List all saved prompts
        /prompt save <name> <text> - Save a prompt for reuse
        /prompt <name> - Execute a saved prompt
        /prompt delete <name> - Delete a saved prompt

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.models import UserPreference

    if not args:
        return {
            "content": (
                "Usage: /prompt <command>\n\n"
                "Commands:\n"
                "  list - List all saved prompts\n"
                "  save <name> <text> - Save a prompt for reuse\n"
                "  <name> - Execute a saved prompt\n"
                "  delete <name> - Delete a saved prompt"
            ),
            "metadata": {"error": True, "command": "prompt"},
        }

    subcommand = args[0].lower()
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    pref, created = UserPreference.objects.get_or_create(
        user_id=user_id,
        defaults={
            "session_key": session_key,
            "selected_agent": "gres",
            "selected_model": "anthropic:claude-sonnet-4",
        },
    )

    saved_prompts = _get_saved_prompts(pref)

    if subcommand == "list":
        return _handle_prompt_list(saved_prompts)

    if subcommand == "save":
        return _handle_prompt_save(args, saved_prompts, pref)

    if subcommand == "delete":
        return _handle_prompt_delete(args, saved_prompts, pref)

    return _handle_prompt_execute(subcommand, saved_prompts)
