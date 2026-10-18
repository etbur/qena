from django.contrib import admin
from .models import LiveStream, LiveChat


class LiveChatInline(admin.TabularInline):
    model      = LiveChat
    extra      = 0
    readonly_fields = ('user', 'username', 'msg_type', 'text', 'created_at')
    can_delete = False


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display  = ('title', 'vendor', 'status', 'total_views', 'total_likes', 'total_messages', 'started_at')
    list_editable = ('status',)
    list_filter   = ('status',)
    search_fields = ('title', 'vendor__store_name')
    readonly_fields = ('stream_id', 'total_views', 'total_likes', 'total_messages', 'stream_key')
    inlines = [LiveChatInline]


@admin.register(LiveChat)
class LiveChatAdmin(admin.ModelAdmin):
    list_display  = ('stream', 'username', 'msg_type', 'text', 'created_at')
    list_filter   = ('msg_type',)
    search_fields = ('username', 'text')
