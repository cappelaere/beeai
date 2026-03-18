"""
Documents
5 functions
"""

import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


def documents_view(request):
    """Legacy view - redirects to document library"""

    return redirect("document_library")


def document_upload_view(request):
    """View for uploading new documents"""

    return render(request, "documents/upload.html")


def document_library_view(request):
    """View for browsing and managing uploaded documents"""

    from agent_app.models import Document

    documents = Document.objects.all().order_by("-uploaded_at")

    return render(request, "documents/library.html", {"documents": documents})


@require_POST
@csrf_exempt
def document_upload_api(request):
    """Handle document upload"""

    from agent_app.models import Document

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)

    uploaded_file = request.FILES["file"]

    name = request.POST.get("name", uploaded_file.name)

    description = request.POST.get("description", "")

    # Create document

    doc = Document.objects.create(
        name=name,
        description=description,
        file=uploaded_file,
        file_type=uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else "",
        file_size=uploaded_file.size,
    )

    # Auto-index the uploaded document

    indexed_chunks = 0

    try:
        import sys
        from pathlib import Path

        # Add tools to path

        Path(__file__).parent.parent.parent / "tools"

        # Add agents directory to path

        agents_path = Path(__file__).parent.parent.parent / "agents"

        if str(agents_path) not in sys.path:
            sys.path.insert(0, str(agents_path))

        from agents.library.tools.document_utils import index_document

        # Index the document (async in background would be better for production)

        pdf_path = Path(doc.file.path)

        if pdf_path.suffix.lower() == ".pdf":
            indexed_chunks = index_document(pdf_path)

    except Exception as e:
        # Don't fail the upload if indexing fails

        print(f"Warning: Failed to index document: {e}")

    return JsonResponse(
        {
            "success": True,
            "document": {
                "id": doc.id,
                "name": doc.name,
                "description": doc.description,
                "file_type": doc.file_type,
                "file_size": doc.get_file_size_display(),
                "uploaded_at": doc.uploaded_at.isoformat(),
            },
            "indexed_chunks": indexed_chunks,
        }
    )


@require_http_methods(["POST", "DELETE"])
@csrf_exempt
def document_delete_api(request, pk):
    """Delete a document"""

    from agent_app.models import Document

    doc = get_object_or_404(Document, pk=pk)

    # Delete the file from storage

    if doc.file:
        doc.file.delete(save=False)

    doc.delete()

    return JsonResponse({"success": True})
