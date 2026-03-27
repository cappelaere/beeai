from django.contrib import admin

from .models import (
    AssistantCard,
    ChatMessage,
    ChatSession,
    PageViewEvent,
    TrackedPage,
    TrackedPageQueryParam,
)

admin.site.register(AssistantCard)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(TrackedPage)
admin.site.register(TrackedPageQueryParam)
admin.site.register(PageViewEvent)
