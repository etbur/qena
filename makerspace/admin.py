from django.contrib import admin
from .models import MakerspaceProfile, MakerspaceOrder, MakerspaceStatusLog


class MakerspaceStatusLogInline(admin.TabularInline):
    model   = MakerspaceStatusLog
    extra   = 0
    readonly_fields = ('old_status', 'new_status', 'note', 'changed_by', 'changed_at')


@admin.register(MakerspaceProfile)
class MakerspaceProfileAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'is_active', 'price_pla_per_gram',
                    'price_laser_per_cm2', 'min_lead_time_days')
    list_editable = ('is_active',)


@admin.register(MakerspaceOrder)
class MakerspaceOrderAdmin(admin.ModelAdmin):
    list_display  = ('order_number', 'customer', 'vendor', 'service_type',
                     'material', 'status', 'final_price', 'created_at')
    list_editable = ('status',)
    list_filter   = ('status', 'service_type', 'material')
    search_fields = ('order_number', 'customer__username', 'vendor__store_name')
    readonly_fields = ('order_number', 'estimated_volume_cm3', 'estimated_grams',
                       'estimated_area_cm2', 'system_price', 'file_type')
    inlines = [MakerspaceStatusLogInline]
