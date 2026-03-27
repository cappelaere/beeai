"""
Views package for agent_app.

This __init__.py provides backward compatibility by importing all view functions
from their respective modules, allowing code like:
    from agent_app.views import chat_view
to continue working after splitting views into separate modules.
"""

# Chat views
# Admin views
from .admin import (
    dashboard_view,
    diagram_view,
    docs_view,
    log_view,
    logs_api,
    logs_view,
    prometheus_metrics,
    prometheus_metrics_bi,
    prometheus_view,
    settings_view,
    tools_view,
)

# Agent views
from .agents import (
    agent_detail,
    agent_studio,
    agents_list,
)

# API: Agents
from .api_agents import (
    agent_create,
    agent_remove,
    agent_set_default,
    agent_update,
)

# API: Cards
from .api_cards import (
    card_create_view,
    card_delete_view,
    card_edit_view,
    card_favorite_api,
    card_patch_api,
    card_use_api,
    cards_by_agent_api,
    cards_list_api,
    cards_view,
)

# API: Chat
from .api_chat import (
    chat_api,
    chat_history_api,
    serve_agent_chart,
)

# API: Notifications
from .api_notifications import (
    notification_mark_all_read_api,
    notification_mark_read_api,
    notifications_list_api,
)

# API: Schedules
from .api_schedules import (
    schedule_create_api,
    schedule_delete_api,
    schedule_detail_api,
    schedule_list_api,
    schedule_list_or_create_api,
    schedule_run_now_api,
    schedule_update_api,
)

# API: Sessions
from .api_sessions import (
    chat_sessions_api,
    create_session_api,
    delete_session_api,
    export_session_api,
    rename_session_api,
)

# API: System
from .api_system import (
    cache_clear_api,
    cache_stats_api,
    context_settings_api,
    section_508_api,
)

# API: Workflows
from .api_workflows import (
    generate_workflow_user_story,
    workflow_create,
    workflow_favorite_api,
    workflow_restore_version,
    workflow_save,
    workflow_tag_version,
    workflow_version_files,
)
from .chat import (
    chat_view,
)

# Document views
from .documents import (
    document_delete_api,
    document_library_view,
    document_upload_api,
    document_upload_view,
    documents_view,
)

# Message views
from .messages import (
    message_audio_api,
    message_feedback_api,
)

# Prompt views
from .prompts import (
    examples_view,
    prompt_create_api,
    prompt_delete_api,
    prompt_suggestions_api,
    prompt_update_api,
    prompts_list_api,
    prompts_view,
)

# Task views
from .tasks import (
    task_cancel,
    task_claim,
    task_count_api,
    task_delete,
    task_detail,
    task_list,
    task_submit,
    task_template_preview,
    task_templates,
)

# Workflow views
from .workflows import (
    schedule_form,
    schedule_list,
    workflow_detail,
    workflow_diagram_editor_frame,
    workflow_diagram_xml,
    workflow_documentation,
    workflow_edit,
    workflow_execute,
    workflow_export,
    workflow_run_delete,
    workflow_run_detail,
    workflow_run_resume_bpmn,
    workflow_runs_bulk_delete,
    workflow_runs_list,
    workflow_studio,
    workflow_user_story,
    workflow_version_compare,
    workflow_versions,
    workflows_list,
)

__all__ = [
    # Chat
    "chat_view",
    # Agents
    "agents_list",
    "agent_studio",
    "agent_detail",
    # Messages
    "message_feedback_api",
    "message_audio_api",
    # Workflows
    "workflows_list",
    "schedule_list",
    "schedule_form",
    "workflow_detail",
    "workflow_diagram_editor_frame",
    "workflow_diagram_xml",
    "workflow_edit",
    "workflow_execute",
    "workflow_export",
    "workflow_documentation",
    "workflow_user_story",
    "workflow_versions",
    "workflow_version_compare",
    "workflow_runs_list",
    "workflow_run_detail",
    "workflow_run_delete",
    "workflow_run_resume_bpmn",
    "workflow_runs_bulk_delete",
    "workflow_studio",
    # Tasks
    "task_list",
    "task_detail",
    "task_claim",
    "task_submit",
    "task_cancel",
    "task_delete",
    "task_count_api",
    "task_template_preview",
    "task_templates",
    # Prompts
    "prompts_view",
    "examples_view",
    "prompt_suggestions_api",
    "prompts_list_api",
    "prompt_create_api",
    "prompt_update_api",
    "prompt_delete_api",
    # Documents
    "documents_view",
    "document_upload_view",
    "document_library_view",
    "document_upload_api",
    "document_delete_api",
    # API: Agents
    "agent_set_default",
    "agent_update",
    "agent_create",
    "agent_remove",
    # API: Workflows
    "workflow_create",
    "generate_workflow_user_story",
    "workflow_favorite_api",
    "workflow_save",
    "workflow_restore_version",
    "workflow_tag_version",
    "workflow_version_files",
    # API: Schedules
    "schedule_list_api",
    "schedule_list_or_create_api",
    "schedule_create_api",
    "schedule_detail_api",
    "schedule_update_api",
    "schedule_delete_api",
    "schedule_run_now_api",
    # API: System
    "cache_stats_api",
    "cache_clear_api",
    "context_settings_api",
    "section_508_api",
    # API: Sessions
    "chat_sessions_api",
    "create_session_api",
    "rename_session_api",
    "delete_session_api",
    "export_session_api",
    # API: Notifications
    "notifications_list_api",
    "notification_mark_read_api",
    "notification_mark_all_read_api",
    # API: Chat
    "chat_api",
    "chat_history_api",
    "serve_agent_chart",
    # API: Cards
    "cards_view",
    "card_create_view",
    "card_edit_view",
    "card_delete_view",
    "cards_list_api",
    "cards_by_agent_api",
    "card_use_api",
    "card_patch_api",
    "card_favorite_api",
    # Admin
    "dashboard_view",
    "docs_view",
    "tools_view",
    "settings_view",
    "logs_api",
    "log_view",
    "logs_view",
    "prometheus_metrics",
    "prometheus_metrics_bi",
    "prometheus_view",
    "diagram_view",
]
