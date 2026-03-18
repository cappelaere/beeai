"""
/card command handler - Manage assistant cards
"""


def _handle_card_list(args):
    """List all cards or show details of a specific card."""
    from agent_app.models import AssistantCard

    cards = AssistantCard.objects.all().order_by("-updated_at")

    if len(args) > 1:
        try:
            card_id = int(args[1])
            card = cards.get(id=card_id)
            return {
                "content": (
                    f"Card #{card.id}: {card.name}\n"
                    f"Agent: {card.agent_type}\n"
                    f"Description: {card.description}\n"
                    f"Favorite: {'Yes' if card.is_favorite else 'No'}\n"
                    f"Created: {card.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Prompt:\n{card.prompt}"
                ),
                "metadata": {"command": "card list detail", "card_id": card_id},
            }
        except (ValueError, AssistantCard.DoesNotExist):
            return {
                "content": f"Error: Card #{args[1]} not found",
                "metadata": {"error": True, "command": "card list"},
            }

    if not cards:
        return {
            "content": "No cards found. Use /card create to create one.",
            "metadata": {"command": "card list"},
        }

    lines = ["Available cards:"]
    for card in cards:
        fav = "⭐" if card.is_favorite else "  "
        lines.append(f"{fav} #{card.id:3d} - {card.name} ({card.agent_type})")

    return {
        "content": "\n".join(lines),
        "metadata": {"command": "card list", "count": cards.count()},
    }


def _handle_card_create():
    """Create a new card."""
    from agent_app.models import AssistantCard

    card = AssistantCard.objects.create(
        name="New Card", description="Created via command", prompt="", agent_type="gres"
    )
    return {
        "content": (
            f"Created card #{card.id}\n\n"
            f"Use '/card update {card.id} <field> <value>' to configure:\n"
            f"  - name <value>\n"
            f"  - description <value>\n"
            f"  - prompt <value>\n"
            f"  - agent <gres|sam|idv|library>\n"
            f"  - favorite <true|false>"
        ),
        "metadata": {"command": "card create", "card_id": card.id},
    }


def _handle_card_update(args):
    """Update a card field."""
    from agent_app.models import AssistantCard

    if len(args) < 4:
        return {
            "content": "Usage: /card update <id> <field> <value>",
            "metadata": {"error": True, "command": "card update"},
        }

    try:
        card_id = int(args[1])
        field = args[2].lower()
        value = " ".join(args[3:])

        card = AssistantCard.objects.get(id=card_id)

        if field == "name":
            card.name = value
        elif field == "description":
            card.description = value
        elif field == "prompt":
            card.prompt = value
        elif field == "agent":
            if value not in ["gres", "sam", "idv", "library", "all"]:
                return {
                    "content": f"Error: Invalid agent '{value}'. Available: gres, sam, idv, library, all",
                    "metadata": {"error": True},
                }
            card.agent_type = value
        elif field == "favorite":
            card.is_favorite = value.lower() in ["true", "yes", "1"]
        else:
            return {
                "content": f"Error: Unknown field '{field}'. Available: name, description, prompt, agent, favorite",
                "metadata": {"error": True},
            }

        card.save()

        return {
            "content": f"Updated card #{card_id}: {field} = {value}",
            "metadata": {"command": "card update", "card_id": card_id, "field": field},
        }

    except (ValueError, AssistantCard.DoesNotExist):
        return {"content": f"Error: Card #{args[1]} not found", "metadata": {"error": True}}


def _handle_card_delete(args):
    """Delete a card."""
    from agent_app.models import AssistantCard

    if len(args) < 2:
        return {"content": "Usage: /card delete <number>", "metadata": {"error": True}}

    try:
        card_id = int(args[1])
        card = AssistantCard.objects.get(id=card_id)
        card_name = card.name
        card.delete()

        return {
            "content": f"Deleted card #{card_id}: {card_name}",
            "metadata": {"command": "card delete", "card_id": card_id},
        }
    except (ValueError, AssistantCard.DoesNotExist):
        return {"content": f"Error: Card #{args[1]} not found", "metadata": {"error": True}}


def _handle_card_execute(args):
    """Execute a card by number."""
    from agent_app.models import AssistantCard

    try:
        card_id = int(args[0])
        card = AssistantCard.objects.get(id=card_id)

        return {
            "content": f"Executing card: {card.name}",
            "execute_card": True,
            "card_prompt": card.prompt,
            "card_agent": card.agent_type,
            "metadata": {"command": "card execute", "card_id": card_id},
        }
    except (ValueError, AssistantCard.DoesNotExist):
        return {
            "content": f"Error: Invalid card command or card not found: {args[0]}",
            "metadata": {"error": True},
        }


def handle_card(request, args, session_key):
    """
    Handle card-related commands.

    Commands:
        /card list - List all cards
        /card list <number> - Show card details
        /card <number> - Execute card
        /card create - Create new card
        /card update <id> <field> <value> - Update card
        /card delete <number> - Delete card

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    if not args:
        return {
            "content": "Usage: /card list|<number>|create|update|delete",
            "metadata": {"error": True, "command": "card"},
        }

    if args[0] == "list":
        return _handle_card_list(args)

    if args[0] == "create":
        return _handle_card_create()

    if args[0] == "update":
        return _handle_card_update(args)

    if args[0] == "delete":
        return _handle_card_delete(args)

    return _handle_card_execute(args)
