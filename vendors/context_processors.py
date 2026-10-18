from orders.models import OrderItem, Order


def vendor_badges(request):
    """Inject sidebar badge counts for vendor portal pages."""
    counts = {'vendor_pending_orders_count': 0}
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and hasattr(user, 'vendor_profile'):
        vendor = user.vendor_profile
        counts['vendor_pending_orders_count'] = OrderItem.objects.filter(
            product__vendor=vendor,
            order__status=Order.STATUS_PENDING
        ).values('order').distinct().count()
    return counts
