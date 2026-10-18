from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, ProductReview, Wishlist
from orders.models import Cart, CartItem


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related('vendor', 'category')[:12]
    flash_deals = Product.objects.filter(is_active=True, is_flash_deal=True).select_related('vendor', 'category')[:8]
    categories = Category.objects.filter(is_active=True, parent__isnull=True)[:12]
    new_arrivals = Product.objects.filter(is_active=True).select_related('vendor', 'category').order_by('-created_at')[:8]
    from vendors.models import Vendor
    top_vendors = Vendor.objects.filter(status=Vendor.STATUS_APPROVED).order_by('-total_sales')[:6]
    context = {
        'featured': featured,
        'flash_deals': flash_deals,
        'categories': categories,
        'new_arrivals': new_arrivals,
        'top_vendors': top_vendors,
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    from .fuzzy import fuzzy_search

    all_products = Product.objects.filter(is_active=True).select_related('vendor', 'category')
    query        = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    sort         = request.GET.get('sort', '-created_at')
    min_price    = request.GET.get('min_price', '')
    max_price    = request.GET.get('max_price', '')

    did_you_mean = ''

    # ── Category filter (applied before fuzzy) ──
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        all_products = all_products.filter(
            Q(category=category) | Q(category__parent=category)
        )
    else:
        category = None

    # ── Price filter ──
    if min_price:
        try:
            all_products = all_products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            all_products = all_products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # ── Search ──
    if query:
        # 1. Try exact / contains match first (fast DB query)
        exact_qs = all_products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(vendor__store_name__icontains=query)
        )

        if exact_qs.exists():
            # Exact matches found — apply normal sort
            sort_map = {
                'price_asc':  'price',
                'price_desc': '-price',
                'newest':     '-created_at',
                'oldest':     'created_at',
            }
            products = exact_qs.order_by(sort_map.get(sort, '-created_at'))
            total_count = products.count()
        else:
            # 2. No exact matches → fuzzy search across all filtered products
            products, did_you_mean = fuzzy_search(all_products, query)
            # fuzzy_search returns a sorted list; wrap in context directly
            total_count = len(products)
    else:
        sort_map = {
            'price_asc':  'price',
            'price_desc': '-price',
            'newest':     '-created_at',
            'oldest':     'created_at',
        }
        products    = all_products.order_by(sort_map.get(sort, '-created_at'))
        total_count = products.count()

    categories = Category.objects.filter(is_active=True, parent__isnull=True)
    context = {
        'products':     products,
        'query':        query,
        'category':     category,
        'categories':   categories,
        'sort':         sort,
        'min_price':    min_price,
        'max_price':    max_price,
        'total_count':  total_count,
        'did_you_mean': did_you_mean,   # shown in template as "Did you mean: ..."
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:6]
    user_review = None
    in_wishlist = False

    if request.user.is_authenticated:
        user_review = ProductReview.objects.filter(product=product, user=request.user).first()
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        if rating:
            ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={'rating': int(rating), 'comment': comment}
            )
            messages.success(request, 'Review submitted.')
            return redirect('store:product_detail', slug=slug)

    context = {
        'product': product,
        'reviews': reviews,
        'related': related,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'store/product_detail.html', context)


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_active=True
    ).select_related('vendor', 'category')
    return render(request, 'store/category.html', {'category': category, 'products': products})


# ─── Cart ───────────────────────────────────────────────────────────────────

def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create() or request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def cart_view(request):
    cart = _get_or_create_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'store:cart'))


def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    cart = _get_or_create_cart(request)
    if item.cart == cart:
        item.delete()
        messages.info(request, 'Item removed from cart.')
    return redirect('store:cart')


def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    cart = _get_or_create_cart(request)
    qty = int(request.POST.get('quantity', 1))
    if item.cart == cart:
        if qty < 1:
            item.delete()
        else:
            item.quantity = qty
            item.save()
    return redirect('store:cart')


# ─── Wishlist ────────────────────────────────────────────────────────────────

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})


@login_required
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        messages.info(request, f'"{product.name}" removed from wishlist.')
    else:
        messages.success(request, f'"{product.name}" added to wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'store:wishlist'))


def product_qr_image(request, slug):
    """Serve product QR code image (PNG raw or branded printable badge)."""
    import os
    from .qr_utils import generate_qr_image, generate_branded_badge_image, serve_qr_response
    product = get_object_or_404(Product, slug=slug)
    full_url = product.get_full_url(request)
    fmt = request.GET.get('format', 'badge')
    as_download = request.GET.get('download') in ('1', 'true', 'yes')

    logo_path = None
    if product.vendor.logo:
        try:
            if os.path.exists(product.vendor.logo.path):
                logo_path = product.vendor.logo.path
        except Exception:
            pass

    if fmt == 'raw':
        img = generate_qr_image(full_url, box_size=10, border=3, logo_path=logo_path)
        filename = f"product-{product.slug}-qr.png"
    else:
        price_str = f"ETB {product.price:,.2f}"
        badge_sub = f"{price_str} · {product.vendor.store_name}"
        img = generate_branded_badge_image(
            title=product.name,
            subtitle=badge_sub,
            badge_type="PRODUCT",
            qr_data_str=full_url,
            logo_path=logo_path,
            footer="Qenagebeya Marketplace 🇪🇹",
            primary_color=product.vendor.brand_primary or '#0b2b4a',
            secondary_color=product.vendor.brand_secondary or '#d42e2e'
        )
        filename = f"product-{product.slug}-badge.png"

    return serve_qr_response(img, filename=filename, as_download=as_download)


def try_on_studio(request, slug=None):
    """
    Virtual Try-On Fashion Studio.
    Supports Live Camera AR stream and Photo Gallery Upload with interactive controls.
    """
    import json
    fashion_query = (
        Q(category__slug__in=['fashion', 'fashion-habesha', 'ethiopian-crafts', 'home-majlis']) |
        Q(name__icontains='kemis') |
        Q(name__icontains='dress') |
        Q(name__icontains='kandura') |
        Q(name__icontains='sheila') |
        Q(name__icontains='scarf') |
        Q(name__icontains='gabi')
    )
    fashion_products = Product.objects.filter(is_active=True).filter(fashion_query).select_related('vendor', 'category')
    
    if not fashion_products.exists():
        fashion_products = Product.objects.filter(is_active=True).select_related('vendor', 'category')[:8]

    selected_product = None
    if slug:
        selected_product = Product.objects.filter(slug=slug, is_active=True).first()
    
    if not selected_product:
        selected_product = fashion_products.first()

    # Prepare JSON serializable list for fast client-side switching
    items_data = []
    for p in fashion_products:
        items_data.append({
            'id': p.id,
            'slug': p.slug,
            'name': p.name,
            'price': float(p.price),
            'vendor_name': p.vendor.store_name if p.vendor else 'Qenagebeya',
            'category_name': p.category.name if p.category else 'Fashion',
            'image_url': p.image.url if p.image else '',
            'overlay_url': p.try_on_overlay_url,
            'url': p.get_absolute_url(),
            'cart_url': reverse('store:cart_add', kwargs={'product_id': p.id}),
            'in_stock': p.in_stock,
        })

    context = {
        'selected_product': selected_product,
        'fashion_products': fashion_products,
        'items_json': json.dumps(items_data),
        'sample_female_model': '/media/try_on/model_female.png',
        'sample_male_model': '/media/try_on/model_male.png',
    }
    return render(request, 'store/try_on.html', context)


def try_on_items_api(request):
    """API endpoint to get fashion items for virtual fitting."""
    from django.http import JsonResponse
    fashion_query = (
        Q(category__slug__in=['fashion', 'fashion-habesha', 'ethiopian-crafts', 'home-majlis']) |
        Q(name__icontains='kemis') |
        Q(name__icontains='dress') |
        Q(name__icontains='kandura') |
        Q(name__icontains='sheila') |
        Q(name__icontains='scarf') |
        Q(name__icontains='gabi')
    )
    fashion_products = Product.objects.filter(is_active=True).filter(fashion_query).select_related('vendor', 'category')
    data = [{
        'id': p.id,
        'slug': p.slug,
        'name': p.name,
        'price': float(p.price),
        'vendor_name': p.vendor.store_name if p.vendor else 'Qenagebeya',
        'category_name': p.category.name if p.category else 'Fashion',
        'image_url': p.image.url if p.image else '',
        'overlay_url': p.try_on_overlay_url,
        'url': p.get_absolute_url(),
        'cart_url': reverse('store:cart_add', kwargs={'product_id': p.id}),
        'in_stock': p.in_stock,
    } for p in fashion_products]
    return JsonResponse({'success': True, 'items': data, 'count': len(data)})
