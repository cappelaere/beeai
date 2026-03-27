from django.db import models

from agents.base import DEFAULT_MODEL, get_django_model_choices
from agents.registry import get_default_agent_id, get_django_agent_choices


class AssistantCard(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prompt = models.TextField()
    is_favorite = models.BooleanField(default=False)
    agent_type = models.CharField(
        max_length=50,
        default=get_default_agent_id,
        choices=get_django_agent_choices,
        help_text="Which agent this card is for",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.agent_type})"


class ChatSession(models.Model):
    session_key = models.CharField(max_length=255, db_index=True)
    user_id = models.IntegerField(db_index=True, default=9)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["session_key", "user_id"]),
        ]

    def __str__(self):
        return self.title or f"Session {self.pk}"


class ChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [(ROLE_USER, "User"), (ROLE_ASSISTANT, "Assistant")]

    FEEDBACK_POSITIVE = "positive"
    FEEDBACK_NEGATIVE = "negative"
    FEEDBACK_CHOICES = [
        (FEEDBACK_POSITIVE, "Positive"),
        (FEEDBACK_NEGATIVE, "Negative"),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)  # Track tokens per message
    elapsed_ms = models.IntegerField(default=0)  # Track response time
    feedback = models.CharField(max_length=20, choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_comment = models.TextField(blank=True)  # Optional feedback text
    feedback_at = models.DateTimeField(null=True, blank=True)
    audio_url = models.CharField(
        max_length=512, null=True, blank=True, help_text="TTS audio URL for Section 508 mode"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class Document(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documents/%Y/%m/")
    file_type = models.CharField(max_length=50, blank=True)  # pdf, docx, txt, etc.
    file_size = models.BigIntegerField(default=0)  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class PromptSuggestion(models.Model):
    """Store prompt suggestions for autocomplete"""

    prompt = models.TextField(unique=True)
    usage_count = models.IntegerField(default=0)
    is_predefined = models.BooleanField(default=False)  # True for seeded prompts
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-usage_count", "-last_used"]
        indexes = [
            models.Index(fields=["prompt"]),
            models.Index(fields=["-usage_count", "-last_used"]),
        ]

    def __str__(self):
        return self.prompt[:100]


class UserPreference(models.Model):
    """Store user preferences for agent and model selection"""

    session_key = models.CharField(max_length=255, db_index=True)
    user_id = models.IntegerField(db_index=True, default=9)
    selected_agent = models.CharField(
        max_length=50,
        default=get_default_agent_id,
        choices=get_django_agent_choices,  # Callable - single source of truth from agents.yaml
    )
    selected_model = models.CharField(
        max_length=100,
        default=DEFAULT_MODEL,
        choices=get_django_model_choices,  # Callable - single source of truth from agents/base.py
    )
    saved_prompts = models.TextField(null=True, blank=True, help_text="JSON-encoded saved prompts")
    section_508_enabled = models.BooleanField(
        null=True,
        blank=True,
        help_text="Enable Section 508 accessibility features (TTS, high contrast, screen reader optimizations). Null uses environment default.",
    )
    context_message_count = models.IntegerField(
        default=0,
        help_text="Number of previous messages from current session to include as context (0 = no context, 20 = last 20 messages)",
    )
    favorite_workflows = models.TextField(
        null=True,
        blank=True,
        default="[]",
        help_text="JSON-encoded list of favorite workflow IDs",
    )
    notification_preferences = models.JSONField(
        blank=True,
        default=dict,
        help_text='e.g. {"notify_on_workflow_complete": true, "daily_digest": false}',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["session_key", "user_id"]),
        ]

    def __str__(self):
        return f"User {self.user_id}: {self.selected_agent} ({self.selected_model})"


class IdentityVerification(models.Model):
    """Audit trail for identity verifications (no PII stored directly)"""

    # Primary identifier - SHA256 hash of all PII fields concatenated
    verification_hash = models.CharField(max_length=64, unique=True, db_index=True)

    # Searchable field hashes (for name, city, state only - no sensitive IDs)
    name_hash = models.CharField(max_length=64, db_index=True)
    city_hash = models.CharField(max_length=64, db_index=True, blank=True)
    state_hash = models.CharField(max_length=64, db_index=True, blank=True)

    # Verification details
    verification_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()  # verification_date + 1 year
    is_valid = models.BooleanField()

    # Audit metadata (NO actual PII)
    fields_provided = models.JSONField()  # e.g., ["name", "city", "state", "drivers_license"]
    verification_details = models.TextField()  # Reason for valid/invalid

    # Request tracking
    requested_by_session = models.CharField(max_length=255)
    requested_by_agent = models.CharField(max_length=50, default="idv")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional notes
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-verification_date"]
        indexes = [
            models.Index(fields=["name_hash", "city_hash", "state_hash"]),
            models.Index(fields=["expiration_date", "is_valid"]),
        ]

    def __str__(self):
        return f"Verification {self.verification_hash[:8]}... ({self.verification_date.date()})"


class Workflow(models.Model):
    """
    Canonical list of workflows; enforces unique workflow_id and workflow_number.
    Synced from the filesystem registry on registry reload.
    """

    workflow_id = models.CharField(max_length=100, unique=True, db_index=True)
    workflow_number = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["workflow_number"]
        indexes = [
            models.Index(fields=["workflow_number"]),
        ]

    def __str__(self):
        return f"#{self.workflow_number} {self.name} ({self.workflow_id})"


class WorkflowRun(models.Model):
    """Track asynchronous workflow executions"""

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_WAITING_FOR_TASK = "waiting_for_task"
    STATUS_WAITING_BPMN_TIMER = "waiting_for_bpmn_timer"
    STATUS_WAITING_BPMN_MESSAGE = "waiting_for_bpmn_message"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_WAITING_FOR_TASK, "Waiting for Task"),
        (STATUS_WAITING_BPMN_TIMER, "Waiting for BPMN timer"),
        (STATUS_WAITING_BPMN_MESSAGE, "Waiting for BPMN message"),
    ]

    # Identifiers
    run_id = models.CharField(max_length=8, primary_key=True, db_index=True)
    workflow_id = models.CharField(max_length=100, db_index=True)
    workflow_name = models.CharField(max_length=255)

    # Execution details (longer values for BPMN intermediate catch waits, PAR-015)
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    user_id = models.IntegerField(default=9, db_index=True)

    # Data
    input_data = models.JSONField()
    output_data = models.JSONField(null=True, blank=True)
    progress_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at", "-created_at"]
        indexes = [
            models.Index(fields=["user_id", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["workflow_id", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.run_id}: {self.workflow_name} ({self.status})"

    def get_duration(self):
        """Calculate duration if workflow is completed"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def bpmn_failure_summary(self) -> dict | None:
        """Structured failure/cancel/timeout info from progress_data."""
        if not self.progress_data:
            return None
        if self.status not in (self.STATUS_FAILED, self.STATUS_CANCELLED):
            return None
        pd = self.progress_data
        reason = pd.get("failure_reason")
        node = pd.get("failed_node_id")
        meta = pd.get("condition_failure_metadata")

        def _parallel_block(eng: dict) -> dict:
            out: dict = {}
            pj = eng.get("pending_joins") if isinstance(eng.get("pending_joins"), dict) else {}
            if pj:
                out["parallel_failure_waiting_join_ids"] = sorted(str(k) for k in pj)
                tokens = (
                    eng.get("active_tokens") if isinstance(eng.get("active_tokens"), list) else []
                )
                at_join = [
                    t.get("current_element_id")
                    for t in tokens
                    if isinstance(t, dict)
                    and t.get("current_element_id")
                    and str(t["current_element_id"]) in pj
                ]
                out["parallel_failure_branches_at_join"] = sorted({str(x) for x in at_join if x})
                label = (
                    "cancelled or timed out"
                    if reason in ("cancelled", "timeout")
                    else "Failure occurred"
                )
                out["parallel_failure_context"] = (
                    f"{label} during parallel execution. One or more branches were waiting "
                    f"at join(s): {', '.join(out['parallel_failure_waiting_join_ids'])}."
                )
            return out

        eng = pd.get("engine_state") or {}
        if self.status == self.STATUS_CANCELLED:
            out = {
                "failure_reason": reason or "cancelled",
                "failed_node_id": node,
                "last_successful_node_id": pd.get("last_successful_node_id"),
                "condition_failure_metadata": meta or {},
                "cancelled_at": pd.get("cancelled_at") or (meta or {}).get("cancelled_at"),
            }
            out.update(_parallel_block(eng if isinstance(eng, dict) else {}))
            return out

        if not any([reason, node, meta]):
            return None
        out = {
            "failure_reason": reason,
            "failed_node_id": node,
            "last_successful_node_id": pd.get("last_successful_node_id"),
            "condition_failure_metadata": meta,
        }
        if reason == "timeout":
            out["timeout_seconds"] = pd.get("timeout_seconds")
            out["timed_out_at"] = pd.get("timed_out_at") or (meta or {}).get("timed_out_at")
        if reason == "retry_exhausted":
            out["retry_attempts"] = meta.get("retry_attempts") if isinstance(meta, dict) else None
            out["bpmn_max_task_retries"] = (
                meta.get("bpmn_max_task_retries") if isinstance(meta, dict) else None
            )
            out["retry_exhausted_branch_id"] = (
                meta.get("branch_id") if isinstance(meta, dict) else None
            )
            out["last_retryable_error_message"] = (
                meta.get("last_error") if isinstance(meta, dict) else None
            )
        out.update(_parallel_block(eng if isinstance(eng, dict) else {}))
        return out


class ScheduledWorkflow(models.Model):
    """Schedule a workflow to run at a specific time or on a recurring interval."""

    TYPE_ONCE = "once"
    TYPE_INTERVAL = "interval"
    TYPE_CHOICES = [
        (TYPE_ONCE, "Once"),
        (TYPE_INTERVAL, "Interval"),
    ]

    user_id = models.IntegerField(db_index=True)
    workflow_id = models.CharField(max_length=100, db_index=True)
    run_name = models.CharField(max_length=255, blank=True)
    input_data = models.JSONField(default=dict)
    schedule_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    run_at = models.DateTimeField(null=True, blank=True)
    interval_minutes = models.PositiveIntegerField(null=True, blank=True)
    next_run_at = models.DateTimeField(db_index=True)
    timezone = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_run_at"]
        indexes = [
            models.Index(fields=["is_active", "next_run_at"]),
            models.Index(fields=["user_id", "-created_at"]),
        ]

    def __str__(self):
        return f"ScheduledWorkflow({self.workflow_id}, next={self.next_run_at})"


class HumanTask(models.Model):
    """Human tasks created by workflows requiring user interaction"""

    # Task types
    TYPE_APPROVAL = "approval"
    TYPE_REVIEW = "review"
    TYPE_DATA_COLLECTION = "data_collection"
    TYPE_VERIFICATION = "verification"

    TYPE_CHOICES = [
        (TYPE_APPROVAL, "Approval"),
        (TYPE_REVIEW, "Review"),
        (TYPE_DATA_COLLECTION, "Data Collection"),
        (TYPE_VERIFICATION, "Verification"),
    ]

    # Task statuses
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    # Roles
    ROLE_USER = "user"
    ROLE_MANAGER = "manager"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_ADMIN, "Admin"),
    ]

    # Identifiers
    task_id = models.CharField(max_length=8, primary_key=True, db_index=True)
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name="tasks")

    # Task details
    task_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True
    )
    required_role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=ROLE_USER, db_index=True
    )

    # Assignment
    assigned_to_user_id = models.IntegerField(null=True, blank=True, db_index=True)

    # Content
    title = models.CharField(max_length=255)
    description = models.TextField()
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by_user_id = models.IntegerField(null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["required_role", "status", "-created_at"]),
            models.Index(fields=["workflow_run", "-created_at"]),
            models.Index(fields=["expires_at", "status"]),
            models.Index(fields=["assigned_to_user_id", "status"]),
        ]

    def __str__(self):
        return f"{self.task_id}: {self.title} ({self.status})"

    def is_expired(self):
        """Check if task has expired"""
        from django.utils import timezone

        return self.expires_at < timezone.now() and self.status in [
            self.STATUS_OPEN,
            self.STATUS_IN_PROGRESS,
        ]

    def can_be_claimed_by(self, user_id: int, user_role: str) -> bool:
        """Check if user can claim this task"""
        if self.status != self.STATUS_OPEN:
            return False
        if self.is_expired():
            return False

        # Role hierarchy: admin > manager > user
        role_hierarchy = {self.ROLE_ADMIN: 3, self.ROLE_MANAGER: 2, self.ROLE_USER: 1}
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(self.required_role, 0)

        return user_level >= required_level


class Notification(models.Model):
    """In-app notifications for task assignments, due dates, and workflow completion/failure."""

    KIND_TASK_ASSIGNED = "task_assigned"
    KIND_TASK_DUE_SOON = "task_due_soon"
    KIND_WORKFLOW_COMPLETED = "workflow_completed"
    KIND_WORKFLOW_FAILED = "workflow_failed"

    KIND_CHOICES = [
        (KIND_TASK_ASSIGNED, "Task assigned"),
        (KIND_TASK_DUE_SOON, "Task due soon"),
        (KIND_WORKFLOW_COMPLETED, "Workflow completed"),
        (KIND_WORKFLOW_FAILED, "Workflow failed"),
    ]

    user_id = models.IntegerField(db_index=True)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    task_id = models.CharField(max_length=8, null=True, blank=True, db_index=True)
    workflow_run_id = models.CharField(max_length=8, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["user_id", "read_at"]),
        ]

    def __str__(self):
        return f"{self.kind} for user {self.user_id}: {self.title[:50]}"


class WorkflowVersion(models.Model):
    """Track versions of workflow definitions for version control"""

    # Identifiers
    workflow_id = models.CharField(max_length=100, db_index=True)
    version_number = models.IntegerField()  # Sequential version number

    # Optional tags for marking releases
    version_tag = models.CharField(
        max_length=50, null=True, blank=True, help_text="Tag like 'v1.0', 'stable', etc."
    )

    # Metadata
    created_by_user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, help_text="Version description/changelog entry")
    is_current = models.BooleanField(
        default=False, db_index=True, help_text="Mark if this is the active version"
    )

    # Storage path to versioned files
    version_path = models.CharField(
        max_length=255, help_text="Path to version folder relative to workflow directory"
    )

    # File checksums for integrity verification
    metadata_checksum = models.CharField(max_length=64, help_text="SHA256 of metadata.yaml")
    workflow_checksum = models.CharField(max_length=64, help_text="SHA256 of workflow.py")

    class Meta:
        ordering = ["-version_number"]
        unique_together = [["workflow_id", "version_number"]]
        indexes = [
            models.Index(fields=["workflow_id", "-version_number"]),
            models.Index(fields=["workflow_id", "is_current"]),
            models.Index(fields=["created_by_user_id", "-created_at"]),
        ]

    def __str__(self):
        tag_str = f" ({self.version_tag})" if self.version_tag else ""
        current_str = " [CURRENT]" if self.is_current else ""
        return f"{self.workflow_id} v{self.version_number}{tag_str}{current_str}"
