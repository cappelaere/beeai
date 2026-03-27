from django.contrib import admin

from .models import (
    AssistantCard,
    ChatMessage,
    ChatSession,
    PageViewEvent,
    TrackedPage,
    TrackedPageQueryParam,
)


@admin.register(PageViewEvent)
class PageViewEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_time",
        "canonical_path",
        "visitor_id",
        "app_user_id",
        "location_country",
        "location_source",
    )
    list_filter = ("location_source", "location_country", "tracked_page")
    search_fields = ("canonical_path", "visitor_id", "session_key_hash")
    date_hierarchy = "event_time"
    ordering = ("-event_time",)
    list_per_page = 50
    show_full_result_count = False
    readonly_fields = [field.name for field in PageViewEvent._meta.fields]


admin.site.register(AssistantCard)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(TrackedPage)
admin.site.register(TrackedPageQueryParam)
