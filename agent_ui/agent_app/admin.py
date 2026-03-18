from django.contrib import admin

from .models import AssistantCard, ChatMessage, ChatSession

admin.site.register(AssistantCard)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
