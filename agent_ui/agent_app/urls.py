from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from django.urls import path

from . import views
from .analytics.views import analytics_location_api


def favicon_view(request):
    """Serve the favicon.png file."""
    # Try STATIC_ROOT first (production), then fall back to local static dir (development)
    if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
        favicon_path = (Path(settings.STATIC_ROOT) / "favicon.png").resolve()
    else:
        # Development - use the app's static directory
        favicon_path = (Path(__file__).resolve().parent / ".." / "static" / "favicon.png").resolve()

    if favicon_path.exists():
        return FileResponse(favicon_path.open("rb"), content_type="image/png")
    return HttpResponseNotFound()


urlpatterns = [
    # Favicon
    path("favicon.ico", favicon_view, name="favicon"),
    # Main pages
    path("", views.chat_view, name="chat"),
    path("chat/", views.chat_view, name="chat_page"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("analytics/dashboard/", views.analytics_dashboard_view, name="analytics_dashboard"),
    path("tools/", views.tools_view, name="tools"),
    path("agents/", views.agents_list, name="agents_list"),
    path("agents/studio/", views.agent_studio, name="agent_studio"),
    path("agents/<str:agent_id>/", views.agent_detail, name="agent_detail"),
    # API endpoints - Agents
    path("api/agents/create/", views.agent_create, name="agent_create"),
    path(
        "api/agents/<str:agent_id>/set-default/", views.agent_set_default, name="agent_set_default"
    ),
    path("api/agents/<str:agent_id>/update/", views.agent_update, name="agent_update"),
    path("api/agents/<str:agent_id>/remove/", views.agent_remove, name="agent_remove"),
    # API endpoints - Workflows
    path("api/workflows/create/", views.workflow_create, name="workflow_create"),
    path(
        "api/workflows/<str:workflow_id>/favorite/",
        views.workflow_favorite_api,
        name="workflow_favorite_api",
    ),
    path("api/workflows/<str:workflow_id>/save/", views.workflow_save, name="workflow_save"),
    path(
        "api/workflows/<str:workflow_id>/generate-user-story/",
        views.generate_workflow_user_story,
        name="workflow_generate_user_story",
    ),
    path(
        "api/workflows/<str:workflow_id>/versions/<int:version_number>/restore/",
        views.workflow_restore_version,
        name="workflow_restore_version",
    ),
    path(
        "api/workflows/<str:workflow_id>/versions/<int:version_number>/tag/",
        views.workflow_tag_version,
        name="workflow_tag_version",
    ),
    path(
        "api/workflows/<str:workflow_id>/versions/<int:version_number>/files/",
        views.workflow_version_files,
        name="workflow_version_files",
    ),
    path("api/analytics/location/", analytics_location_api, name="analytics_location_api"),
    path("prompts/", views.prompts_view, name="prompts"),
    path("examples/", views.examples_view, name="examples"),
    path("documents/", views.documents_view, name="documents"),
    path("documents/upload/", views.document_upload_view, name="document_upload"),
    path("documents/library/", views.document_library_view, name="document_library"),
    path("settings/", views.settings_view, name="settings"),
    path("diagrams/<str:diagram_name>/", views.diagram_view, name="diagram_view"),
    path("docs/<path:path>", views.docs_view, name="docs_view"),
    # Workflow pages
    path("workflows/", views.workflows_list, name="workflows_list"),
    path("workflows/schedules/", views.schedule_list, name="schedule_list"),
    path("workflows/schedules/new/", views.schedule_form, name="schedule_new"),
    path("workflows/schedules/<int:schedule_id>/edit/", views.schedule_form, name="schedule_edit"),
    path("workflows/studio/", views.workflow_studio, name="workflow_studio"),
    # Human Task pages (must come before generic workflow_id pattern)
    path("workflows/tasks/", views.task_list, name="task_list"),
    path("workflows/tasks/templates/", views.task_templates, name="task_templates"),
    path(
        "workflows/tasks/templates/<str:template_id>/preview/",
        views.task_template_preview,
        name="task_template_preview",
    ),
    path("workflows/tasks/<str:task_id>/", views.task_detail, name="task_detail"),
    path("workflows/tasks/<str:task_id>/claim/", views.task_claim, name="task_claim"),
    path("workflows/tasks/<str:task_id>/submit/", views.task_submit, name="task_submit"),
    path("workflows/tasks/<str:task_id>/cancel/", views.task_cancel, name="task_cancel"),
    path("workflows/tasks/<str:task_id>/delete/", views.task_delete, name="task_delete"),
    # Workflow runs (must come before generic workflow_id pattern)
    path("workflows/runs/", views.workflow_runs_list, name="workflow_runs_list"),
    path(
        "workflows/runs/bulk-delete/",
        views.workflow_runs_bulk_delete,
        name="workflow_runs_bulk_delete",
    ),
    path("workflows/runs/<str:run_id>/", views.workflow_run_detail, name="workflow_run_detail"),
    path(
        "workflows/runs/<str:run_id>/delete/", views.workflow_run_delete, name="workflow_run_delete"
    ),
    path(
        "workflows/runs/<str:run_id>/resume-bpmn/",
        views.workflow_run_resume_bpmn,
        name="workflow_run_resume_bpmn",
    ),
    # Generic workflow patterns (must come last to avoid matching specific routes)
    path("workflows/<str:workflow_id>/", views.workflow_detail, name="workflow_detail"),
    path("workflows/<str:workflow_id>/edit/", views.workflow_edit, name="workflow_edit"),
    path(
        "workflows/<str:workflow_id>/edit/diagram-frame/",
        views.workflow_diagram_editor_frame,
        name="workflow_diagram_editor_frame",
    ),
    path(
        "workflows/<str:workflow_id>/edit/diagram-xml/",
        views.workflow_diagram_xml,
        name="workflow_diagram_xml",
    ),
    path(
        "workflows/<str:workflow_id>/versions/", views.workflow_versions, name="workflow_versions"
    ),
    path(
        "workflows/<str:workflow_id>/versions/<int:version1>/compare/<int:version2>/",
        views.workflow_version_compare,
        name="workflow_version_compare",
    ),
    path("workflows/<str:workflow_id>/execute/", views.workflow_execute, name="workflow_execute"),
    path("workflows/<str:workflow_id>/export/", views.workflow_export, name="workflow_export"),
    path(
        "workflows/<str:workflow_id>/docs/",
        views.workflow_documentation,
        name="workflow_documentation",
    ),
    path(
        "workflows/<str:workflow_id>/user-story/",
        views.workflow_user_story,
        name="workflow_user_story",
    ),
    # Task API endpoints
    path("api/tasks/count/", views.task_count_api, name="task_count_api"),
    # API endpoints - Schedules
    path("api/workflows/schedules/", views.schedule_list_or_create_api, name="schedule_list_api"),
    path(
        "api/workflows/schedules/<int:schedule_id>/",
        views.schedule_detail_api,
        name="schedule_detail_api",
    ),
    path(
        "api/workflows/schedules/<int:schedule_id>/update/",
        views.schedule_update_api,
        name="schedule_update_api",
    ),
    path(
        "api/workflows/schedules/<int:schedule_id>/delete/",
        views.schedule_delete_api,
        name="schedule_delete_api",
    ),
    path(
        "api/workflows/schedules/<int:schedule_id>/run_now/",
        views.schedule_run_now_api,
        name="schedule_run_now_api",
    ),
    # API endpoints - Chat
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/chat/<int:session_id>/", views.chat_history_api, name="chat_history_api"),
    path(
        "api/agent-chart/<str:chart_id>/",
        views.serve_agent_chart,
        name="serve_agent_chart",
    ),
    path(
        "api/chat/<int:session_id>/export/",
        views.export_session_api,
        name="export_session_api_alias",
    ),
    # API endpoints - Cards
    path("api/cards/", views.cards_list_api, name="cards_list_api"),
    path(
        "api/cards/by-agent/<str:agent_type>/", views.cards_by_agent_api, name="cards_by_agent_api"
    ),
    path("api/cards/<int:pk>/use/", views.card_use_api, name="card_use_api"),
    path("api/cards/<int:pk>/patch/", views.card_patch_api, name="card_patch_api"),
    path(
        "api/card/<int:pk>/patch/", views.card_patch_api, name="card_patch_api_alt"
    ),  # Alternative URL for tests
    path("api/cards/<int:pk>/favorite/", views.card_favorite_api, name="card_favorite_api"),
    # Card view pages (for templates)
    path("cards/", views.cards_view, name="cards"),
    path("cards/create/", views.card_create_view, name="card_create"),
    path("cards/<int:pk>/edit/", views.card_edit_view, name="card_edit"),
    path("cards/<int:pk>/delete/", views.card_delete_view, name="card_delete"),
    # API endpoints - Sessions
    path("api/sessions/", views.chat_sessions_api, name="chat_sessions_api"),
    path("api/sessions/create/", views.create_session_api, name="create_session_api"),
    path(
        "api/sessions/<int:session_id>/rename/", views.rename_session_api, name="rename_session_api"
    ),
    path(
        "api/sessions/<int:session_id>/delete/", views.delete_session_api, name="delete_session_api"
    ),
    path(
        "api/sessions/<int:session_id>/messages/", views.chat_history_api, name="chat_history_api"
    ),
    path(
        "api/sessions/<int:session_id>/export/", views.export_session_api, name="export_session_api"
    ),
    # API endpoints - Notifications
    path("api/notifications/", views.notifications_list_api, name="notifications_list_api"),
    path(
        "api/notifications/read-all/",
        views.notification_mark_all_read_api,
        name="notification_mark_all_read_api",
    ),
    path(
        "api/notifications/<int:notification_id>/read/",
        views.notification_mark_read_api,
        name="notification_mark_read_api",
    ),
    # API endpoints - Documents
    path("api/documents/upload/", views.document_upload_api, name="document_upload_api"),
    path("api/documents/<int:pk>/delete/", views.document_delete_api, name="document_delete_api"),
    # API endpoints - Prompts
    path("api/prompts/", views.prompts_list_api, name="prompts_list_api"),
    path("api/prompts/create/", views.prompt_create_api, name="prompt_create_api"),
    path("api/prompts/<int:prompt_id>/update/", views.prompt_update_api, name="prompt_update_api"),
    path("api/prompts/<int:prompt_id>/delete/", views.prompt_delete_api, name="prompt_delete_api"),
    path("api/prompt-suggestions/", views.prompt_suggestions_api, name="prompt_suggestions_api"),
    # API endpoints - Message feedback
    path(
        "api/messages/<int:message_id>/feedback/",
        views.message_feedback_api,
        name="message_feedback_api",
    ),
    # API endpoints - Messages
    path("api/messages/<int:message_id>/audio/", views.message_audio_api, name="message_audio_api"),
    # API endpoints - Cache
    path("api/cache/stats/", views.cache_stats_api, name="cache_stats_api"),
    path("api/cache/clear/", views.cache_clear_api, name="cache_clear_api"),
    # API endpoints - Accessibility
    path("api/section508/", views.section_508_api, name="section_508_api"),
    path("api/context-settings/", views.context_settings_api, name="context_settings_api"),
    path("api/logs/", views.logs_api, name="logs_api"),
    path("api/logs/<str:log_name>/", views.log_view, name="log_view"),
    path("logs/", views.logs_view, name="logs_view"),
    path("metrics/bi/", views.prometheus_metrics_bi, name="prometheus_metrics_bi"),
    path("metrics/", views.prometheus_metrics, name="prometheus_metrics"),
    path("prometheus/", views.prometheus_view, name="prometheus_view"),
]
