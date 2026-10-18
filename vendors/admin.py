from django.contrib import admin
from .models import Vendor, VendorBankAccount, VendorPayout


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'tier', 'status', 'total_sales', 'created_at')
    list_editable = ('tier', 'status')
    list_filter = ('tier', 'status')
    search_fields = ('store_name', 'user__username', 'user__email')
    prepopulated_fields = {'slug': ('store_name',)}
    actions = ['approve_vendors', 'suspend_vendors']

    def approve_vendors(self, request, queryset):
        queryset.update(status=Vendor.STATUS_APPROVED)
    approve_vendors.short_description = 'Approve selected vendors'

    def suspend_vendors(self, request, queryset):
        queryset.update(status=Vendor.STATUS_SUSPENDED)
    suspend_vendors.short_description = 'Suspend selected vendors'


@admin.register(VendorBankAccount)
class VendorBankAccountAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'bank_name', 'account_holder')


@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount', 'status', 'requested_at', 'processed_at')
    list_editable = ('status',)
    list_filter = ('status',)
