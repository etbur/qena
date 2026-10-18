"""
White-label vendor storefront views.
Served when request.vendor_storefront is set (subdomain/custom domain hit).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib import messages
from store.models import Product, Category
from orders.models import Cart, CartItem


def _get_vendor(request):
    v = getattr(request, 'vendor_storefront', None)
    if not v:
        raise Http404
    return v


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not getattr(request, 'session', None):
            return None
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def sf_home(request):
    vendor   = _get_vendor(request)
    products = vendor.products.filter(is_active=True).order_by('-created_at')
    featured = products.filter(is_featured=True)[:6]
    flash    = products.filter(is_flash_deal=True)[:4]
    cats     = Category.objects.filter(
        products__vendor=vendor, products__is_active=True
    ).distinct()
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(name__icontains=q)
    cat_slug = request.GET.get('cat', '')
    if cat_slug:
        products = products.filter(category__slug=cat_slug)
    return render(request, 'storefront/home.html', {
        'vendor': vendor,
        'products': products[:60],
        'featured': featured,
        'flash': flash,
        'categories': cats,
        'q': q,
        'cat_slug': cat_slug,
    })


def sf_product(request, pk):
    vendor  = _get_vendor(request)
    product = get_object_or_404(Product, pk=pk, vendor=vendor, is_active=True)
    related = vendor.products.filter(
        category=product.category, is_active=True
    ).exclude(pk=pk)[:4]
    return render(request, 'storefront/product.html', {
        'vendor': vendor,
        'product': product,
        'related': related,
    })


def sf_about(request):
    vendor = _get_vendor(request)
    return render(request, 'storefront/about.html', {'vendor': vendor})


def sf_contact(request):
    vendor = _get_vendor(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        messages.success(request, f'Thank you {name or "valued customer"}! Your message has been sent to {vendor.store_name}. We will get back to you shortly.')
        return redirect('/contact/')
    return render(request, 'storefront/contact.html', {'vendor': vendor})


def sf_cart(request):
    vendor = _get_vendor(request)
    cart = _get_or_create_cart(request)
    items = cart.items.filter(product__vendor=vendor).select_related('product') if cart else []
    subtotal = sum(item.subtotal for item in items)
    return render(request, 'storefront/cart.html', {
        'vendor': vendor,
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
    })


def sf_cart_add(request, pk):
    vendor = _get_vendor(request)
    product = get_object_or_404(Product, pk=pk, vendor=vendor, is_active=True)
    cart = _get_or_create_cart(request)
    if cart:
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
            item.save()
        messages.success(request, f'"{product.name}" added to cart.')
    next_url = request.META.get('HTTP_REFERER') or '/cart/'
    return redirect(next_url)


def sf_cart_remove(request, pk):
    vendor = _get_vendor(request)
    cart = _get_or_create_cart(request)
    if cart:
        item = get_object_or_404(CartItem, pk=pk, cart=cart, product__vendor=vendor)
        item.delete()
        messages.info(request, 'Item removed from cart.')
    return redirect('/cart/')
