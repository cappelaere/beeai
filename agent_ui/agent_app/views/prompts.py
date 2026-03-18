"""
Prompts
7 functions
"""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


def prompts_view(request):

    from agent_app.models import PromptSuggestion

    prompts = PromptSuggestion.objects.all().order_by("-usage_count", "-last_used")[:100]

    return render(request, "prompts.html", {"prompts": prompts})


def examples_view(request):

    # Organize prompt examples by category

    examples = {
        "report_generation": {
            "title": "Report Generation",
            "icon": "📊",
            "description": "Generate detailed reports on properties, auctions, and bidding activity",
            "prompts": [
                "Generate a summary report of all active auctions with reserve prices above $500,000",
                "Create a report showing top 10 properties by number of bids",
                "Generate a monthly auction performance report for the last 3 months",
                "List all properties that sold above their reserve price this month",
                "Create a report of auction completion rates by property type",
            ],
        },
        "business_intelligence": {
            "title": "Business Intelligence",
            "icon": "📈",
            "description": "Analyze trends, performance metrics, and strategic insights",
            "prompts": [
                "What are the bidding trends for commercial properties over the last quarter?",
                "Analyze agent performance metrics and identify top performers",
                "Show me properties with the highest watcher-to-bidder conversion rates",
                "What is the average time from listing to sale for residential properties?",
                "Compare auction success rates between different property types",
            ],
        },
        "sam_gov": {
            "title": "SAM.gov Exclusions",
            "icon": "🚫",
            "description": "Query federal contract exclusions and entity status",
            "prompts": [
                "Check if John Smith is excluded from federal contracts",
                "Search for exclusions issued by TREAS-OFAC in the last year",
                "List all active exclusions for entities in California",
                "Show me statistics on exclusions by agency",
                "Get detailed information about exclusion record #12345",
            ],
        },
        "ofac_compliance": {
            "title": "OFAC Compliance",
            "icon": "🚨",
            "description": "Screen bidders against OFAC Specially Designated Nationals list",
            "prompts": [
                "Check if Mohammed Ahmed is eligible to bid",
                "Is ABC Corporation on the OFAC SDN list?",
                "Search for entities related to Cuba in the SDN database",
                "Screen bidder: John Smith for OFAC compliance",
                "How many entries are in the OFAC database?",
                "Find individuals designated as terrorists",
                "Check if Banco Nacional de Cuba is sanctioned",
                "Search for SDN entries in the narcotics trafficking program",
                "Get details for SDN entity ID 6365",
                "What are the most common OFAC sanctions programs?",
            ],
        },
        "bidder_verification": {
            "title": "Bidder Verification (Orchestration)",
            "icon": "✅",
            "description": "Comprehensive bidder screening - orchestrates both SAM.gov and OFAC checks",
            "prompts": [
                "Can John Smith bid on property #12345?",
                "Verify eligibility for ABC Corporation",
                "Is Jane Doe allowed to participate in auctions?",
                "Check if Mohammed Ahmed can bid",
                "Verify bidder: Smith Construction LLC",
                "Can Maria Garcia from Acme Holdings participate?",
                "Is XYZ Enterprises eligible to bid?",
                "Comprehensive screening for John Doe",
                "Check bidder eligibility: National Trading Company",
                "Verify both SAM.gov and OFAC status for Robert Johnson",
            ],
        },
        "identity_verification": {
            "title": "Identity Verification",
            "icon": "🔐",
            "description": "Verify bidder identity and eligibility (Future Agent)",
            "prompts": [
                "Verify the identity of bidder ID 789",
                "Check if bidder has completed KYC requirements",
                "Cross-reference bidder information with SAM.gov exclusions",
                "Generate identity verification report for bidder John Doe",
                "Check bidder eligibility for government property auctions",
            ],
        },
    }

    return render(request, "examples.html", {"examples": examples})


@require_GET
def prompt_suggestions_api(request):
    """Return prompt suggestions for autocomplete"""

    from agent_app.models import PromptSuggestion

    query = request.GET.get("q", "").strip()

    limit = int(request.GET.get("limit", 10))

    if not query:
        return JsonResponse({"suggestions": []})

    # Search prompts that contain the query string

    suggestions = PromptSuggestion.objects.filter(prompt__icontains=query).order_by(
        "-usage_count", "-last_used"
    )[:limit]

    results = []

    for s in suggestions:
        results.append(
            {
                "id": s.id,
                "prompt": s.prompt,
                "usage_count": s.usage_count,
                "is_predefined": s.is_predefined,
            }
        )

    return JsonResponse({"suggestions": results})


@require_GET
def prompts_list_api(request):
    """List prompts with pagination, search, and filtering"""

    from agent_app.models import PromptSuggestion

    # Parse query parameters

    page = int(request.GET.get("page", 1))

    page_size = int(request.GET.get("page_size", 20))

    search_query = request.GET.get("search", "").strip()

    filter_type = request.GET.get("filter", "all")  # all, predefined, user

    # Build queryset

    qs = PromptSuggestion.objects.all()

    # Apply filters

    if search_query:
        qs = qs.filter(prompt__icontains=search_query)

    if filter_type == "predefined":
        qs = qs.filter(is_predefined=True)

    elif filter_type == "user":
        qs = qs.filter(is_predefined=False)

    # Order by usage

    qs = qs.order_by("-usage_count", "-last_used")

    # Pagination

    total = qs.count()

    offset = (page - 1) * page_size

    prompts = qs[offset : offset + page_size]

    results = []

    for p in prompts:
        results.append(
            {
                "id": p.id,
                "prompt": p.prompt,
                "usage_count": p.usage_count,
                "is_predefined": p.is_predefined,
                "last_used": p.last_used.isoformat() if p.last_used else None,
            }
        )

    return JsonResponse(
        {
            "prompts": results,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_next": offset + page_size < total,
            },
        }
    )


@require_POST
@csrf_exempt
@require_POST
@csrf_exempt
def prompt_create_api(request):
    """Create a new prompt"""

    from agent_app.models import PromptSuggestion

    try:
        data = json.loads(request.body)

        prompt_text = data.get("prompt", "").strip()

    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not prompt_text:
        return JsonResponse({"error": "Prompt text required"}, status=400)

    # Check if prompt already exists

    if PromptSuggestion.objects.filter(prompt=prompt_text).exists():
        return JsonResponse({"error": "Prompt already exists"}, status=400)

    prompt_obj = PromptSuggestion.objects.create(prompt=prompt_text, is_predefined=False)

    return JsonResponse(
        {
            "success": True,
            "prompt": {
                "id": prompt_obj.id,
                "prompt": prompt_obj.prompt,
                "usage_count": prompt_obj.usage_count,
            },
        }
    )


@require_POST
@csrf_exempt
@require_POST
@csrf_exempt
def prompt_update_api(request, prompt_id):
    """Update an existing prompt"""

    from agent_app.models import PromptSuggestion

    prompt_obj = get_object_or_404(PromptSuggestion, pk=prompt_id)

    try:
        data = json.loads(request.body)

        new_text = data.get("prompt", "").strip()

    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not new_text:
        return JsonResponse({"error": "Prompt text required"}, status=400)

    prompt_obj.prompt = new_text

    prompt_obj.save()

    return JsonResponse(
        {"success": True, "prompt": {"id": prompt_obj.id, "prompt": prompt_obj.prompt}}
    )


@require_http_methods(["POST", "DELETE"])
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@csrf_exempt
def prompt_delete_api(request, prompt_id):
    """Delete a prompt"""

    from agent_app.models import PromptSuggestion

    prompt = get_object_or_404(PromptSuggestion, pk=prompt_id)

    prompt.delete()

    return JsonResponse({"success": True})
