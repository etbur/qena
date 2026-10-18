from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .models import Vendor, VendorPayout, VendorInventoryItem
from .forms import VendorSetupForm, ProductForm, BankAccountForm, VendorInventoryItemForm
from store.models import Product
from orders.models import Order, OrderItem


def vendor_required(view_func):
    """Decorator: user must be authenticated and have an approved vendor profile."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'vendor_profile'):
            messages.warning(request, 'Please complete your vendor registration first.')
            return redirect('vendors:setup')
        if request.user.vendor_profile.status != Vendor.STATUS_APPROVED:
            messages.warning(request, 'Your vendor account is pending approval.')
            return redirect('vendors:pending')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@login_required
def setup(request):
    """First-time vendor registration / store setup."""
    if hasattr(request.user, 'vendor_profile'):
        return redirect('vendors:dashboard')
    from django.utils.text import slugify
    form = VendorSetupForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        vendor = form.save(commit=False)
        vendor.user = request.user
        
        # Subdomain setup
        sub = slugify(vendor.subdomain or vendor.store_name)
        if not sub:
            sub = 'store-' + str(request.user.pk)
        if Vendor.objects.filter(subdomain=sub).exists():
            import uuid
            sub = f"{sub}-{uuid.uuid4().hex[:4]}"
        vendor.subdomain = sub
        
        # Custom domain cleanup
        if vendor.custom_domain:
            vendor.custom_domain = vendor.clean_domain(vendor.custom_domain)
            if Vendor.objects.filter(custom_domain=vendor.custom_domain).exists():
                form.add_error('custom_domain', f'Custom domain "{vendor.custom_domain}" is already registered.')
                return render(request, 'vendors/setup.html', {'form': form})

        vendor.save()
        messages.success(request, f'Store "{vendor.store_name}" created! Your storefront is configured.')
        if vendor.status == Vendor.STATUS_APPROVED:
            return redirect('vendors:dashboard')
        return redirect('vendors:pending')
    return render(request, 'vendors/setup.html', {'form': form})


def pending(request):
    return render(request, 'vendors/pending.html')


@vendor_required
def dashboard(request):
    from django.utils import timezone
    from datetime import timedelta, date
    from django.db.models.functions import TruncDate, TruncMonth
    from .models import VendorInventoryItem, StockMovement
    from live.models import LiveStream

    vendor = request.user.vendor_profile
    now    = timezone.now()
    today  = now.date()

    # ── Time range selector ─────────────────────────────────────────────
    range_param = request.GET.get('range', 'all')
    range_map   = {'7': 7, '30': 30, '90': 90, '365': 365}
    range_days  = range_map.get(range_param)
    if range_days:
        range_start = now - timedelta(days=range_days)
    else:
        range_start = None   # all time

    # ── E-commerce ──────────────────────────────────────────────────────
    all_orders = OrderItem.objects.filter(product__vendor=vendor).select_related('order', 'product')
    orders     = all_orders.filter(order__created_at__gte=range_start) if range_start else all_orders

    total_revenue  = all_orders.aggregate(rev=Sum('product_price'))['rev'] or 0
    total_orders   = all_orders.values('order').distinct().count()
    total_products = vendor.products.filter(is_active=True).count()
    pending_orders = all_orders.filter(order__status=Order.STATUS_PENDING).values('order').distinct().count()
    recent_orders  = all_orders.order_by('-order__created_at')[:8]
    top_products   = vendor.products.filter(is_active=True).annotate(
        sold=Count('orderitem')
    ).order_by('-sold')[:5]

    # Order status breakdown (all time)
    status_counts = {}
    for s, _ in Order.STATUS_CHOICES:
        cnt = all_orders.filter(order__status=s).values('order').distinct().count()
        if cnt > 0:
            status_counts[s] = cnt

    # ── Inventory ───────────────────────────────────────────────────────
    inv_items    = VendorInventoryItem.objects.filter(vendor=vendor)
    inv_total    = inv_items.count()
    inv_ok       = sum(1 for i in inv_items if i.stock_status == 'ok')
    inv_low      = sum(1 for i in inv_items if i.stock_status == 'low')
    inv_out      = inv_items.filter(quantity=0).count()
    inv_value    = float(sum(i.unit_cost * i.quantity for i in inv_items))
    recent_moves = StockMovement.objects.filter(item__vendor=vendor).order_by('-created_at')[:5]

    # ── Live streams ────────────────────────────────────────────────────
    live_streams     = LiveStream.objects.filter(vendor=vendor)
    live_total       = live_streams.count()
    live_live_now    = live_streams.filter(status='live').count()
    live_ended       = live_streams.filter(status='ended').count()
    live_total_views = live_streams.aggregate(v=Sum('total_views'))['v'] or 0
    live_total_likes = live_streams.aggregate(l=Sum('total_likes'))['l'] or 0
    live_total_msgs  = live_streams.aggregate(m=Sum('total_messages'))['m'] or 0
    recent_streams   = live_streams.order_by('-created_at')[:4]

    # ── Makerspace ──────────────────────────────────────────────────────
    try:
        from makerspace.models import MakerspaceOrder
        mk_orders     = MakerspaceOrder.objects.filter(vendor=vendor)
        mk_total      = mk_orders.count()
        mk_pending    = mk_orders.filter(status='quote_pending').count()
        mk_production = mk_orders.filter(status='in_production').count()
        mk_completed  = mk_orders.filter(status='delivered').count()
        mk_revenue    = float(mk_orders.filter(status='delivered').aggregate(r=Sum('final_price'))['r'] or 0)
    except Exception:
        mk_total = mk_pending = mk_production = mk_completed = 0
        mk_revenue = 0.0

    # ── Revenue chart: daily for selected range (or last 30 days if all-time) ─
    from django.db.models.functions import TruncDate, TruncMonth
    chart_days = range_days or 30
    chart_start = now - timedelta(days=chart_days)

    daily_qs = (
        all_orders
        .filter(order__created_at__gte=chart_start)
        .annotate(day=TruncDate('order__created_at'))
        .values('day')
        .annotate(rev=Sum('product_price'))
        .order_by('day')
    )
    daily_map = {d['day'].isoformat(): float(d['rev']) for d in daily_qs}

    # Build label/data arrays — group by week if >30 days to keep chart readable
    if chart_days <= 30:
        # Daily points
        d_labels, d_data = [], []
        for i in range(chart_days - 1, -1, -1):
            day = today - timedelta(days=i)
            fmt = '%b %d' if chart_days > 7 else '%a'
            d_labels.append(day.strftime(fmt))
            d_data.append(daily_map.get(day.isoformat(), 0.0))
    else:
        # Weekly aggregation
        weekly = {}
        for i in range(chart_days - 1, -1, -1):
            day = today - timedelta(days=i)
            week_key = day.strftime('W%W %Y')
            weekly[week_key] = weekly.get(week_key, 0.0) + daily_map.get(day.isoformat(), 0.0)
        d_labels = list(weekly.keys())
        d_data   = list(weekly.values())

    # ── Monthly revenue (all-time, up to 12 months) ──────────────────────
    monthly_qs = (
        all_orders
        .annotate(month=TruncMonth('order__created_at'))
        .values('month')
        .annotate(rev=Sum('product_price'))
        .order_by('month')
    )
    monthly_labels = [m['month'].strftime('%b %Y') for m in monthly_qs if m['month']]
    monthly_data   = [float(m['rev']) for m in monthly_qs if m['month']]

    # ── Target & Performance Gauge ──────────────────────────────────────
    sales_target = 10000.0
    target_achieved_pct = min(100.0, round((float(total_revenue) / max(1.0, sales_target)) * 100.0, 1))
    delivered_count = all_orders.filter(order__status=Order.STATUS_DELIVERED).values('order').distinct().count()
    fulfillment_rate = round((delivered_count / max(1, total_orders)) * 100.0, 1) if total_orders > 0 else 100.0

    context = {
        'vendor': vendor,
        'range_param': range_param,
        # performance gauge
        'sales_target': sales_target,
        'target_achieved_pct': target_achieved_pct,
        'fulfillment_rate': fulfillment_rate,
        # ecommerce
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'status_counts': status_counts,
        'status_counts_json': __import__('json').dumps(status_counts),
        # charts — serialized to JSON strings for safe JS embedding
        'monthly_labels_json': __import__('json').dumps(monthly_labels),
        'monthly_data_json':   __import__('json').dumps(monthly_data),
        'd7_labels_json':      __import__('json').dumps(d_labels),
        'd7_data_json':        __import__('json').dumps(d_data),
        'chart_days': chart_days,
        # inventory
        'inv_total': inv_total,
        'inv_ok': inv_ok,
        'inv_low': inv_low,
        'inv_out': inv_out,
        'inv_value': inv_value,
        'recent_moves': recent_moves,
        # live
        'live_total': live_total,
        'live_live_now': live_live_now,
        'live_ended': live_ended,
        'live_total_views': live_total_views,
        'live_total_likes': live_total_likes,
        'live_total_msgs': live_total_msgs,
        'recent_streams': recent_streams,
        # makerspace
        'mk_total': mk_total,
        'mk_pending': mk_pending,
        'mk_production': mk_production,
        'mk_completed': mk_completed,
        'mk_revenue': mk_revenue,
    }
    return render(request, 'vendors/dashboard.html', context)


@vendor_required
def products(request):
    vendor = request.user.vendor_profile
    product_list = vendor.products.all().order_by('-created_at')
    return render(request, 'vendors/products.html', {'vendor': vendor, 'products': product_list})


@vendor_required
def product_add(request):
    vendor = request.user.vendor_profile
    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.vendor = vendor
        product.save()
        messages.success(request, f'"{product.name}" added to your store.')
        return redirect('vendors:products')
    return render(request, 'vendors/product_form.html', {'form': form, 'action': 'Add', 'vendor': vendor})


@vendor_required
def product_edit(request, pk):
    vendor = request.user.vendor_profile
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{product.name}" updated.')
        return redirect('vendors:products')
    return render(request, 'vendors/product_form.html', {'form': form, 'action': 'Edit', 'vendor': vendor, 'product': product})


@vendor_required
def product_delete(request, pk):
    vendor = request.user.vendor_profile
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('vendors:products')
    return render(request, 'vendors/product_confirm_delete.html', {'product': product})


@vendor_required
def orders_view(request):
    vendor = request.user.vendor_profile
    order_items = OrderItem.objects.filter(product__vendor=vendor).select_related('order', 'order__user', 'product').order_by('-order__created_at')

    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        order_items_list = order_items.filter(order__status=status_filter)
    else:
        order_items_list = order_items

    total_count = order_items.values('order').distinct().count()
    pending_count = order_items.filter(order__status=Order.STATUS_PENDING).values('order').distinct().count()
    processing_count = order_items.filter(order__status=Order.STATUS_PROCESSING).values('order').distinct().count()
    shipped_count = order_items.filter(order__status=Order.STATUS_SHIPPED).values('order').distinct().count()
    delivered_count = order_items.filter(order__status=Order.STATUS_DELIVERED).values('order').distinct().count()

    context = {
        'vendor': vendor,
        'order_items': order_items_list,
        'status_filter': status_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'vendors/orders.html', context)


@vendor_required
def storefront_settings(request):
    """Vendor configures their white-label storefront and 10,000 ETB/yr FT subscription."""
    vendor = request.user.vendor_profile
    if request.method == 'POST':
        action = request.POST.get('action', 'save_settings')

        if action == 'submit_ft_payment':
            ref = request.POST.get('storefront_payment_ref', '').strip()
            method = request.POST.get('storefront_payment_method', 'bank_transfer').strip()
            note = request.POST.get('storefront_payment_note', '').strip()

            if not ref:
                messages.error(request, 'Please provide your Funds Transfer (FT) reference or transaction ID.')
                return redirect('vendors:storefront_settings')

            vendor.storefront_payment_ref = ref
            vendor.storefront_payment_method = method
            vendor.storefront_payment_note = note
            vendor.storefront_status = Vendor.STOREFRONT_STATUS_PENDING
            vendor.save()
            messages.success(request, '10,000 ETB Funds Transfer (FT) reference submitted! Your standalone domain is now pending Admin approval.')
            return redirect('vendors:storefront_settings')

        # Basic branding
        vendor.store_tagline   = request.POST.get('store_tagline', '').strip()[:200]
        vendor.store_keywords  = request.POST.get('store_keywords', '').strip()[:300]
        vendor.brand_primary   = request.POST.get('brand_primary', '#0b2b4a').strip()[:7]
        vendor.brand_secondary = request.POST.get('brand_secondary', '#d42e2e').strip()[:7]
        vendor.brand_font      = request.POST.get('brand_font', 'Inter').strip()[:100]
        # Domain config
        sub = request.POST.get('subdomain', '').strip().lower().replace(' ', '-')[:100]
        custom = request.POST.get('custom_domain', '').strip().lower()[:253]
        vendor.storefront_enabled = request.POST.get('storefront_enabled') == 'on'
        # Validate subdomain uniqueness
        from django.utils.text import slugify
        sub = slugify(sub) if sub else vendor.slug
        from vendors.models import Vendor as V
        if sub and V.objects.filter(subdomain=sub).exclude(pk=vendor.pk).exists():
            messages.error(request, f'Subdomain "{sub}" is already taken. Choose another.')
        else:
            vendor.subdomain = sub
        # Custom domain
        custom = vendor.clean_domain(request.POST.get('custom_domain', ''))[:253]
        if custom and V.objects.filter(custom_domain__iexact=custom).exclude(pk=vendor.pk).exists():
            messages.error(request, f'Custom domain "{custom}" is already registered by another vendor.')
        else:
            vendor.custom_domain = custom
        # Social links
        vendor.whatsapp  = request.POST.get('whatsapp', '').strip()[:30]
        vendor.telegram  = request.POST.get('telegram', '').strip()[:100]
        vendor.instagram = request.POST.get('instagram', '').strip()[:100]
        vendor.facebook  = request.POST.get('facebook', '').strip()[:100]
        vendor.twitter   = request.POST.get('twitter', '').strip()[:100]
        vendor.tiktok    = request.POST.get('tiktok', '').strip()[:100]

        vendor.save()
        messages.success(request, 'Storefront settings saved successfully.')
        return redirect('vendors:storefront_settings')

    return render(request, 'vendors/storefront_settings.html', {'vendor': vendor})


@vendor_required
def settings_view(request):
    vendor = request.user.vendor_profile
    form = VendorSetupForm(request.POST or None, request.FILES or None, instance=vendor)
    bank_form = BankAccountForm(
        request.POST or None,
        instance=getattr(vendor, 'bank_account', None)
    )
    if form.is_valid() and bank_form.is_valid():
        form.save()
        bank = bank_form.save(commit=False)
        bank.vendor = vendor
        bank.save()
        messages.success(request, 'Store settings saved.')
        return redirect('vendors:settings')
    return render(request, 'vendors/settings.html', {'vendor': vendor, 'form': form, 'bank_form': bank_form})


@vendor_required
def analytics(request):
    import json
    from datetime import timezone
    from django.db.models.functions import TruncMonth

    vendor = request.user.vendor_profile
    order_items = OrderItem.objects.filter(product__vendor=vendor)
    total_sales = vendor.total_sales or 0
    total_orders = vendor.total_orders or 0
    pending_orders = order_items.filter(order__status=Order.STATUS_PENDING).values('order').distinct().count()
    delivered_orders = order_items.filter(order__status=Order.STATUS_DELIVERED).values('order').distinct().count()

    sales_target = 50000.0
    target_achieved_pct = min(100.0, round((float(total_sales) / sales_target) * 100, 1))
    fulfillment_rate = round((delivered_orders / total_orders * 100), 1) if total_orders > 0 else 100.0

    monthly = order_items.annotate(
        month=TruncMonth('order__created_at', tzinfo=timezone.utc)
    ).values('month').annotate(revenue=Sum('product_price'), count=Count('id')).order_by('month')

    monthly_labels = []
    monthly_rev_data = []
    for m in monthly:
        monthly_labels.append(m['month'].strftime('%b %Y') if m['month'] else '')
        monthly_rev_data.append(float(m['revenue'] or 0))

    if not monthly_labels:
        monthly_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        monthly_rev_data = [4200, 8900, 16500, 24800, 35000, float(total_sales) or 46000]

    # Top products
    top_products = order_items.values(
        'product__name', 'product__price'
    ).annotate(
        total_sold=Count('id'),
        total_revenue=Sum('product_price')
    ).order_by('-total_revenue')[:8]

    # Status distribution
    status_counts = {
        'pending': pending_orders,
        'processing': order_items.filter(order__status=Order.STATUS_PROCESSING).values('order').distinct().count(),
        'shipped': order_items.filter(order__status=Order.STATUS_SHIPPED).values('order').distinct().count(),
        'delivered': delivered_orders,
        'cancelled': order_items.filter(order__status=Order.STATUS_CANCELLED).values('order').distinct().count(),
    }
    if sum(status_counts.values()) == 0:
        status_counts = {'pending': 2, 'processing': 3, 'shipped': 4, 'delivered': 10, 'cancelled': 1}

    context = {
        'vendor': vendor,
        'monthly': list(monthly),
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'sales_target': sales_target,
        'target_achieved_pct': target_achieved_pct,
        'fulfillment_rate': fulfillment_rate,
        'top_products': list(top_products),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_rev_json': json.dumps(monthly_rev_data),
        'status_counts_json': json.dumps(status_counts),
    }
    return render(request, 'vendors/analytics.html', context)


def vendor_store(request, slug):
    """Public vendor store page."""
    vendor = get_object_or_404(Vendor, slug=slug, status=Vendor.STATUS_APPROVED)
    products = vendor.products.filter(is_active=True)
    return render(request, 'vendors/store.html', {'vendor': vendor, 'products': products})


def vendor_qr_image(request, slug):
    """Serve vendor store QR code image (PNG raw or branded printable badge)."""
    import os
    from store.qr_utils import generate_qr_image, generate_branded_badge_image, serve_qr_response
    vendor = get_object_or_404(Vendor, slug=slug)
    store_url = vendor.get_store_url(request)
    fmt = request.GET.get('format', 'badge')
    as_download = request.GET.get('download') in ('1', 'true', 'yes')

    logo_path = None
    if vendor.logo:
        try:
            if os.path.exists(vendor.logo.path):
                logo_path = vendor.logo.path
        except Exception:
            pass

    if fmt == 'raw':
        img = generate_qr_image(store_url, box_size=10, border=3, fill_color=vendor.brand_primary or '#0b2b4a', logo_path=logo_path)
        filename = f"vendor-{vendor.slug}-qr.png"
    else:
        sub = f"Verified Vendor · {vendor.get_tier_display()}"
        if vendor.store_tagline:
            sub = f"{sub} — {vendor.store_tagline}"
        img = generate_branded_badge_image(
            title=vendor.store_name,
            subtitle=sub,
            badge_type="STORE",
            qr_data_str=store_url,
            logo_path=logo_path,
            footer=f"{vendor.store_name} on Qenagebeya 🇪🇹",
            primary_color=vendor.brand_primary or '#0b2b4a',
            secondary_color=vendor.brand_secondary or '#d42e2e'
        )
        filename = f"vendor-{vendor.slug}-store-badge.png"

    return serve_qr_response(img, filename=filename, as_download=as_download)


# ─── Payouts ──────────────────────────────────────────────────────────────────

@vendor_required
def payouts(request):
    vendor = request.user.vendor_profile
    payout_list = vendor.payouts.all()
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '0')
        try:
            from decimal import Decimal
            amount = Decimal(amount_str)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
            elif amount > vendor.balance:
                messages.error(request, f'Insufficient balance. Available: ETB {vendor.balance}')
            else:
                VendorPayout.objects.create(vendor=vendor, amount=amount)
                messages.success(request, f'Payout request of ETB {amount} submitted.')
                return redirect('vendors:payouts')
        except Exception:
            messages.error(request, 'Invalid amount.')
    return render(request, 'vendors/payouts.html', {'vendor': vendor, 'payouts': payout_list})


# ─── Inventory ────────────────────────────────────────────────────────────────

# ─── Private Inventory ────────────────────────────────────────────────────────

@vendor_required
def inventory(request):
    vendor = request.user.vendor_profile
    from .models import VendorWarehouse, VendorSupplier, StockMovement, PurchaseOrder

    # Auto-sync store products to inventory if not yet linked
    store_products = Product.objects.filter(vendor=vendor)
    for p in store_products:
        VendorInventoryItem.objects.get_or_create(
            vendor=vendor, linked_product=p,
            defaults={
                'item_name': p.name,
                'category': p.category.name if p.category else '',
                'unit_cost': p.price,
                'selling_price': p.price,
                'quantity': p.stock,
                'is_public': True,
            }
        )

    items = VendorInventoryItem.objects.filter(vendor=vendor).select_related('warehouse', 'supplier')
    q            = request.GET.get('q', '').strip()
    stock_filter = request.GET.get('filter', 'all')
    cat_filter   = request.GET.get('cat', '').strip()

    if q:
        items = items.filter(item_name__icontains=q) | items.filter(sku__icontains=q) | items.filter(barcode__icontains=q)
    if cat_filter:
        items = items.filter(category__iexact=cat_filter)

    all_items = VendorInventoryItem.objects.filter(vendor=vendor)
    total_count      = all_items.count()
    low_stock_count  = sum(1 for i in all_items if i.stock_status == 'low')
    out_stock_count  = all_items.filter(quantity=0).count()
    in_stock_count   = sum(1 for i in all_items if i.stock_status == 'ok')
    total_value      = sum(i.unit_cost * i.quantity for i in all_items)

    if stock_filter == 'low':
        items = [i for i in items if i.stock_status == 'low']
    elif stock_filter == 'out':
        items = [i for i in items.filter(quantity=0)]
    elif stock_filter == 'ok':
        items = [i for i in items if i.stock_status == 'ok']

    categories = all_items.values_list('category', flat=True).distinct().exclude(category='')
    warehouses = VendorWarehouse.objects.filter(vendor=vendor)
    suppliers  = VendorSupplier.objects.filter(vendor=vendor)
    recent_movements = StockMovement.objects.filter(item__vendor=vendor).select_related('item')[:15]
    pending_pos = PurchaseOrder.objects.filter(vendor=vendor).exclude(status='received').exclude(status='cancelled')[:5]

    return render(request, 'vendors/inventory.html', {
        'vendor': vendor, 'items': items, 'q': q,
        'stock_filter': stock_filter, 'cat_filter': cat_filter,
        'total_count': total_count, 'low_stock_count': low_stock_count,
        'out_stock_count': out_stock_count, 'in_stock_count': in_stock_count,
        'total_value': total_value, 'categories': categories,
        'warehouses': warehouses, 'suppliers': suppliers,
        'recent_movements': recent_movements, 'pending_pos': pending_pos,
    })


@vendor_required
def inventory_adjust(request, pk):
    """Quick stock adjustment with movement log."""
    from .models import StockMovement
    vendor = request.user.vendor_profile
    item = get_object_or_404(VendorInventoryItem, pk=pk, vendor=vendor)
    if request.method == 'POST':
        move_type = request.POST.get('move_type', 'adjust')
        try:
            qty = int(request.POST.get('quantity', 0))
        except ValueError:
            messages.error(request, 'Invalid quantity.')
            return redirect('vendors:inventory')

        note = request.POST.get('note', '')
        before = item.quantity
        if move_type == 'in':
            item.quantity += qty
        elif move_type == 'out':
            item.quantity = max(0, item.quantity - qty)
        elif move_type == 'adjust':
            item.quantity = max(0, qty)
        elif move_type == 'return':
            item.quantity += qty
        else:
            item.quantity += qty

        item.save(update_fields=['quantity'])
        if item.linked_product:
            item.linked_product.stock = item.quantity
            item.linked_product.save(update_fields=['stock'])

        StockMovement.objects.create(
            item=item, move_type=move_type,
            quantity=qty, before_qty=before, after_qty=item.quantity,
            note=note, created_by=request.user,
        )
        messages.success(request, f'Stock updated: {item.item_name} → {item.quantity}')
    return redirect('vendors:inventory')


@vendor_required
def warehouse_list(request):
    from .models import VendorWarehouse
    vendor = request.user.vendor_profile
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            VendorWarehouse.objects.create(
                vendor=vendor, name=name,
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                phone=request.POST.get('phone', ''),
                is_default=not VendorWarehouse.objects.filter(vendor=vendor).exists(),
            )
            messages.success(request, f'Warehouse "{name}" added.')
        return redirect('vendors:warehouses')
    warehouses = VendorWarehouse.objects.filter(vendor=vendor)
    return render(request, 'vendors/warehouses.html', {'vendor': vendor, 'warehouses': warehouses})


@vendor_required
def supplier_list(request):
    from .models import VendorSupplier
    vendor = request.user.vendor_profile
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            VendorSupplier.objects.create(
                vendor=vendor, name=name,
                contact_person=request.POST.get('contact_person', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
            )
            messages.success(request, f'Supplier "{name}" added.')
        return redirect('vendors:suppliers')
    suppliers = VendorSupplier.objects.filter(vendor=vendor)
    return render(request, 'vendors/suppliers.html', {'vendor': vendor, 'suppliers': suppliers})


@vendor_required
def purchase_orders(request):
    from .models import PurchaseOrder, VendorSupplier
    vendor = request.user.vendor_profile
    if request.method == 'POST':
        from decimal import Decimal
        supplier_id = request.POST.get('supplier_id')
        note        = request.POST.get('note', '')
        expected    = request.POST.get('expected_date') or None
        try:
            supplier = VendorSupplier.objects.get(pk=supplier_id, vendor=vendor) if supplier_id else None
        except VendorSupplier.DoesNotExist:
            supplier = None
        po = PurchaseOrder.objects.create(
            vendor=vendor, supplier=supplier,
            note=note, expected_date=expected,
        )
        messages.success(request, f'Purchase order {po.po_number} created.')
        return redirect('vendors:purchase_orders')
    pos = PurchaseOrder.objects.filter(vendor=vendor).select_related('supplier')
    suppliers = VendorSupplier.objects.filter(vendor=vendor)
    return render(request, 'vendors/purchase_orders.html', {
        'vendor': vendor, 'pos': pos, 'suppliers': suppliers,
    })


@vendor_required
def stock_movements(request):
    from .models import StockMovement
    vendor = request.user.vendor_profile
    movements = StockMovement.objects.filter(item__vendor=vendor).select_related('item', 'created_by')[:100]
    return render(request, 'vendors/stock_movements.html', {'vendor': vendor, 'movements': movements})


@vendor_required
def inventory_add(request):
    vendor = request.user.vendor_profile
    form = VendorInventoryItemForm(request.POST or None, request.FILES or None, vendor=vendor)
    if form.is_valid():
        item = form.save(commit=False)
        item.vendor = vendor
        item.save()
        # Log initial stock as a stock-in movement
        from .models import StockMovement
        if item.quantity > 0:
            StockMovement.objects.create(
                item=item, move_type='in',
                quantity=item.quantity, before_qty=0, after_qty=item.quantity,
                note='Initial stock', created_by=request.user,
            )
        messages.success(request, f'"{item.item_name}" added to inventory.')
        return redirect('vendors:inventory')
    return render(request, 'vendors/inventory_form.html', {'form': form, 'action': 'Add', 'vendor': vendor})


@vendor_required
def inventory_edit(request, pk):
    vendor = request.user.vendor_profile
    item = get_object_or_404(VendorInventoryItem, pk=pk, vendor=vendor)
    form = VendorInventoryItemForm(request.POST or None, request.FILES or None, instance=item, vendor=vendor)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{item.item_name}" updated.')
        return redirect('vendors:inventory')
    return render(request, 'vendors/inventory_form.html', {'form': form, 'action': 'Edit', 'vendor': vendor, 'item': item})


@vendor_required
def inventory_delete(request, pk):
    vendor = request.user.vendor_profile
    item = get_object_or_404(VendorInventoryItem, pk=pk, vendor=vendor)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item removed from private inventory.')
        return redirect('vendors:inventory')
    return render(request, 'vendors/inventory_confirm_delete.html', {'item': item})


@vendor_required
def inventory_update(request, pk):
    vendor = request.user.vendor_profile
    item = get_object_or_404(VendorInventoryItem, pk=pk, vendor=vendor)
    if request.method == 'POST':
        new_qty = request.POST.get('stock', '')
        try:
            item.quantity = int(new_qty)
            item.save(update_fields=['quantity'])
            if item.linked_product:
                item.linked_product.stock = item.quantity
                item.linked_product.save(update_fields=['stock'])
            messages.success(request, f'"{item.item_name}" stock quantity updated to {item.quantity}.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity value.')
    return redirect('vendors:inventory')


# ─── Order fulfillment ────────────────────────────────────────────────────────

@vendor_required
def order_fulfill(request, order_item_id):
    vendor = request.user.vendor_profile
    oi = get_object_or_404(OrderItem, pk=order_item_id, product__vendor=vendor)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            oi.order.status = new_status
            oi.order.save(update_fields=['status'])
            messages.success(request, f'Order #{oi.order.order_number} updated to {oi.order.get_status_display()}.')
    return redirect('vendors:orders')


# ─── Customers ────────────────────────────────────────────────────────────────

@vendor_required
def customers(request):
    vendor = request.user.vendor_profile
    from orders.models import OrderItem as OI
    customer_ids = OI.objects.filter(
        product__vendor=vendor
    ).values_list('order__user_id', flat=True).distinct()
    from accounts.models import User as U
    customer_list = U.objects.filter(pk__in=customer_ids).annotate(
        order_count=Count('orders'),
    ).order_by('-order_count')
    return render(request, 'vendors/customers.html', {
        'vendor': vendor,
        'customers': customer_list,
    })
