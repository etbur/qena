from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_price', 'quantity', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_method', 'total', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'payment_method', 'payment_status')
    search_fields = ('order_number', 'user__username', 'shipping_name')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'session_key', 'item_count', 'total', 'updated_at')
