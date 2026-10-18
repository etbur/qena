from django.contrib import admin
from .models import Agent, Client, Deal, Inquiry


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'commission_rate', 'is_active', 'created_at')
    list_editable = ('tier', 'is_active')
    list_filter = ('tier', 'is_active')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'agent', 'tier', 'email', 'phone', 'created_at')
    list_filter = ('tier', 'agent')
    search_fields = ('full_name', 'email', 'phone')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'client', 'value', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'agent')
    search_fields = ('title', 'client__full_name')


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('subject', 'agent', 'client', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status',)
