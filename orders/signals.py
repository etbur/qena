from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='orders.Order')
def update_vendor_balance_on_delivery(sender, instance, **kwargs):
    """When an order is delivered, credit vendor balances."""
    if instance.status != 'delivered':
        return
    from orders.models import OrderItem
    for item in instance.items.all():
        if item.product and item.product.vendor:
            vendor = item.product.vendor
            # Net amount = subtotal - commission
            net = item.subtotal - item.vendor_commission
            vendor.balance += net
            vendor.save(update_fields=['balance'])
