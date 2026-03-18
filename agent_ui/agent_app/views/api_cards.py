"""
Api Cards
9 functions
"""

import json
import logging

from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from agent_app.models import AssistantCard

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


def cards_view(request):

    cards = AssistantCard.objects.all()

    return render(request, "cards.html", {"cards": cards})


def card_create_view(request):

    from .forms import AssistantCardForm

    if request.method == "POST":
        form = AssistantCardForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("cards")

    else:
        form = AssistantCardForm()

    return render(request, "card_form.html", {"form": form})


def card_edit_view(request, pk):

    from .forms import AssistantCardForm

    card = get_object_or_404(AssistantCard, pk=pk)

    if request.method == "POST":
        form = AssistantCardForm(request.POST, instance=card)

        if form.is_valid():
            form.save()

            return redirect("cards")

    else:
        form = AssistantCardForm(instance=card)

    return render(request, "card_form.html", {"form": form, "card": card})


@require_POST
@require_POST
def card_delete_view(request, pk):

    card = get_object_or_404(AssistantCard, pk=pk)

    card.delete()

    return redirect("cards")


@require_GET
@require_GET
def cards_list_api(request):
    """Return list of cards; ?favorites=1 for favorites only. Always includes prompt for home page."""

    qs = AssistantCard.objects.all().order_by("agent_type", "name")

    if request.GET.get("favorites") == "1":
        qs = qs.filter(is_favorite=True)

    cards = []

    for c in qs:
        row = {
            "id": c.id,
            "name": c.name,
            "description": c.description or "",
            "prompt": c.prompt,  # Always include prompt for home page cards
            "is_favorite": c.is_favorite,
            "agent_type": c.agent_type,
        }

        cards.append(row)

    return JsonResponse({"cards": cards})


@require_GET
def cards_by_agent_api(request, agent_type):
    """Return cards filtered by agent type"""

    qs = (
        AssistantCard.objects.filter(models.Q(agent_type=agent_type) | models.Q(agent_type="all"))
        .filter(is_favorite=True)
        .order_by("name")
    )

    cards = []
    for c in qs:
        cards.append(
            {
                "id": c.id,
                "name": c.name,
                "description": c.description or "",
                "prompt": c.prompt,
                "is_favorite": c.is_favorite,
                "agent_type": c.agent_type,
            }
        )

    return JsonResponse({"cards": cards})


@require_GET
@require_GET
def card_use_api(request, pk):

    card = get_object_or_404(AssistantCard, pk=pk)

    return JsonResponse(
        {
            "prompt": card.prompt,
            "name": card.name,
        }
    )


@require_http_methods(["POST", "PATCH"])
@csrf_exempt
@require_http_methods(["POST", "PATCH"])
@csrf_exempt
def card_patch_api(request, pk):

    card = get_object_or_404(AssistantCard, pk=pk)

    try:
        data = json.loads(request.body)

        updated = False

        if "name" in data:
            card.name = data["name"]

            updated = True

        if "description" in data:
            card.description = data["description"]

            updated = True

        if "prompt" in data:
            card.prompt = data["prompt"]

            updated = True

        if "is_favorite" in data:
            card.is_favorite = data["is_favorite"]

            updated = True

        if updated:
            card.save()

        return JsonResponse({"success": True})

    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@require_POST
@csrf_exempt
@require_POST
@csrf_exempt
def card_favorite_api(request, pk):

    card = get_object_or_404(AssistantCard, pk=pk)

    card.is_favorite = not card.is_favorite

    card.save()

    return JsonResponse({"success": True, "is_favorite": card.is_favorite})
