from django.contrib import admin
from .models import AuditLog, Dispute


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('actor', 'action', 'description', 'ip_address', 'created_at')
    list_filter   = ('action',)
    search_fields = ('actor__username', 'description')
    readonly_fields = ('actor', 'action', 'description', 'ip_address', 'created_at')


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display  = ('subject', 'order', 'raised_by', 'status', 'created_at')
    list_editable = ('status',)
    list_filter   = ('status',)
