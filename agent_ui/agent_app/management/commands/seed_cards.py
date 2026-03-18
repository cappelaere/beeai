"""
Create example assistant cards. Run: python manage.py seed_cards
Idempotent: only creates cards that don't exist by name.
"""

from django.core.management.base import BaseCommand

from agent_app.models import AssistantCard

EXAMPLE_CARDS = [
    # GRES Agent Examples
    {
        "name": "List active properties",
        "description": "Get a list of properties currently available for auction.",
        "prompt": "List all active properties. Show property ID, address or title, and status.",
        "is_favorite": True,
        "agent_type": "gres",
    },
    {
        "name": "Auction dashboard summary",
        "description": "Overview of auction metrics and counts.",
        "prompt": "Give me a summary of the auction dashboard: total properties, bids, and key metrics.",
        "is_favorite": True,
        "agent_type": "gres",
    },
    {
        "name": "Property types breakdown",
        "description": "See available property types in the system.",
        "prompt": "What property types are available? List them with a short description of each.",
        "is_favorite": False,
        "agent_type": "gres",
    },
    {
        "name": "Site detail",
        "description": "Get details for the current or specified site.",
        "prompt": "Show me the site detail: name, description, and any relevant configuration.",
        "is_favorite": False,
        "agent_type": "gres",
    },
    {
        "name": "Recent bid activity",
        "description": "Check recent bidding activity across auctions.",
        "prompt": "Summarize recent bid activity. Which auctions have the most bids and what are the latest bid amounts?",
        "is_favorite": True,
        "agent_type": "gres",
    },
    # SAM.gov Agent Examples
    {
        "name": "Check entity exclusion",
        "description": "Check if a company or individual is excluded from federal contracts.",
        "prompt": "Check if ACME Corporation is excluded from federal contracts.",
        "is_favorite": True,
        "agent_type": "sam",
    },
    {
        "name": "SAM.gov statistics",
        "description": "Get overall statistics about the SAM.gov exclusions database.",
        "prompt": "Show me SAM.gov exclusion statistics including totals by classification and agency.",
        "is_favorite": True,
        "agent_type": "sam",
    },
    {
        "name": "Search by agency",
        "description": "Find all exclusions issued by a specific federal agency.",
        "prompt": "Search for all exclusions issued by TREAS-OFAC and show me the top 10 results.",
        "is_favorite": False,
        "agent_type": "sam",
    },
    {
        "name": "List excluding agencies",
        "description": "Show all federal agencies that have issued exclusions.",
        "prompt": "List all federal agencies that have issued exclusions, sorted by count.",
        "is_favorite": False,
        "agent_type": "sam",
    },
    {
        "name": "Exclusion details",
        "description": "Get complete details for a specific exclusion record.",
        "prompt": "Get detailed information for SAM number S4MR3R7D6 including all addresses and dates.",
        "is_favorite": False,
        "agent_type": "sam",
    },
]


class Command(BaseCommand):
    help = "Create example assistant cards if they don't exist."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for data in EXAMPLE_CARDS:
            card, was_created = AssistantCard.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "prompt": data["prompt"],
                    "is_favorite": data["is_favorite"],
                    "agent_type": data.get("agent_type", "gres"),
                },
            )
            if was_created:
                created += 1
            else:
                # Keep existing cards in sync with example data (so default favorites show on home)
                if (
                    card.description != data["description"]
                    or card.prompt != data["prompt"]
                    or card.is_favorite != data["is_favorite"]
                    or card.agent_type != data.get("agent_type", "gres")
                ):
                    card.description = data["description"]
                    card.prompt = data["prompt"]
                    card.is_favorite = data["is_favorite"]
                    card.agent_type = data.get("agent_type", "gres")
                    card.save(
                        update_fields=[
                            "description",
                            "prompt",
                            "is_favorite",
                            "agent_type",
                            "updated_at",
                        ]
                    )
                    updated += 1
        self.stdout.write(
            self.style.SUCCESS(f"Created {created}, updated {updated} example card(s).")
        )
        if created == 0 and updated == 0:
            self.stdout.write("All example cards already exist and are up to date.")
