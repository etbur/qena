from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem, Cart, CartItem
from .forms import CheckoutForm


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    sk = request.session.session_key
    return Cart.objects.filter(session_key=sk, user=None).first() if sk else None


@login_required
def checkout(request):
    cart = _get_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')

    initial = {}
    if request.user.is_authenticated:
        initial = {
            'shipping_name': f'{request.user.first_name} {request.user.last_name}'.strip() or request.user.username,
            'shipping_phone': request.user.phone,
            'shipping_address': request.user.address,
            'shipping_city': request.user.city,
            'shipping_country': request.user.country,
        }

    form = CheckoutForm(request.POST or None, initial=initial)
    if form.is_valid():
        order = form.save(commit=False)
        order.user = request.user
        order.subtotal = cart.total
        order.shipping_fee = 0 if cart.total >= 500 else 50
        order.total = order.subtotal + order.shipping_fee - order.discount
        order.save()

        for item in cart.items.all():
            commission = item.product.vendor.commission_rate / 100 * item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                vendor_commission=commission * item.quantity,
            )
            # Decrease stock
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save()

        # Update vendor total_sales
        for oi in order.items.all():
            if oi.product:
                vendor = oi.product.vendor
                vendor.total_sales += oi.subtotal
                vendor.save()

        # Clear cart
        cart.items.all().delete()

        messages.success(request, f'Order #{order.order_number} placed successfully!')
        return redirect('orders:order_detail', pk=order.pk)

    context = {
        'form': form,
        'cart': cart,
        'shipping_fee': 0 if cart.total >= 500 else 50,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
        order.status = Order.STATUS_CANCELLED
        order.save()
        messages.success(request, f'Order #{order.order_number} cancelled.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    return redirect('orders:order_detail', pk=pk)
