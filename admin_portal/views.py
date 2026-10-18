from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.models import User
from vendors.models import Vendor
from agents.models import Agent
from orders.models import Order, OrderItem
from store.models import Product
from .models import AuditLog, Dispute


# ─── Access guard ────────────────────────────────────────────────────────────

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_staff or request.user.role == 'admin'):
            messages.error(request, 'Admin access required.')
            return redirect('store:home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _log(request, action, description):
    ip = request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(actor=request.user, action=action,
                             description=description, ip_address=ip)


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    import json
    from datetime import timezone
    from django.db.models.functions import TruncMonth

    total_users    = User.objects.count()
    total_vendors  = Vendor.objects.count()
    total_agents   = Agent.objects.count()
    total_orders   = Order.objects.count()
    total_revenue  = Order.objects.filter(
        status=Order.STATUS_DELIVERED
    ).aggregate(r=Sum('total'))['r'] or 0
    total_products = Product.objects.filter(is_active=True).count()
    open_disputes  = Dispute.objects.filter(status=Dispute.STATUS_OPEN).count()

    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    fulfillment_rate = round((delivered_orders / total_orders * 100), 1) if total_orders > 0 else 100.0

    platform_sales_target = 250000.0
    target_achieved_pct = min(100.0, round((float(total_revenue) / platform_sales_target) * 100, 1))

    # Platform overview: recent users
    recent_users = User.objects.order_by('-date_joined')[:8]

    # Top vendors by total_sales
    top_vendors = Vendor.objects.filter(
        status=Vendor.STATUS_APPROVED
    ).order_by('-total_sales')[:4]

    # Recent audit logs
    recent_logs = AuditLog.objects.select_related('actor').order_by('-created_at')[:5]

    # Chart 1: Monthly Platform Revenue Trend
    monthly_qs = Order.objects.filter(
        status=Order.STATUS_DELIVERED
    ).annotate(
        month=TruncMonth('created_at', tzinfo=timezone.utc)
    ).values('month').annotate(revenue=Sum('total'), orders=Count('id')).order_by('month')

    monthly_labels = []
    monthly_rev_data = []
    monthly_orders_data = []
    for m in monthly_qs:
        monthly_labels.append(m['month'].strftime('%b %Y') if m['month'] else '')
        monthly_rev_data.append(float(m['revenue'] or 0))
        monthly_orders_data.append(int(m['orders'] or 0))

    if not monthly_labels:
        monthly_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        monthly_rev_data = [12000, 24000, 42000, 68000, 95000, float(total_revenue) or 140000]
        monthly_orders_data = [15, 28, 45, 62, 88, max(total_orders, 110)]

    # Chart 2: Order Status Distribution
    status_counts = {
        'pending': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'processing': Order.objects.filter(status=Order.STATUS_PROCESSING).count(),
        'shipped': Order.objects.filter(status=Order.STATUS_SHIPPED).count(),
        'delivered': delivered_orders,
        'cancelled': Order.objects.filter(status=Order.STATUS_CANCELLED).count(),
    }
    if sum(status_counts.values()) == 0:
        status_counts = {'pending': 2, 'processing': 3, 'shipped': 5, 'delivered': 12, 'cancelled': 1}

    # Chart 3: User Role Distribution
    role_map = {'customer': 0, 'vendor': 0, 'agent': 0, 'admin': 0}
    for r in User.objects.values('role').annotate(c=Count('id')):
        if r['role'] in role_map:
            role_map[r['role']] = r['c']
    if sum(role_map.values()) == 0:
        role_map = {'customer': 45, 'vendor': 12, 'agent': 8, 'admin': 3}

    context = dict(
        total_users=total_users,
        total_vendors=total_vendors,
        total_agents=total_agents,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_products=total_products,
        open_disputes=open_disputes,
        fulfillment_rate=fulfillment_rate,
        platform_sales_target=platform_sales_target,
        target_achieved_pct=target_achieved_pct,
        recent_users=recent_users,
        top_vendors=top_vendors,
        recent_logs=recent_logs,
        # JSON data for charts
        monthly_labels_json=json.dumps(monthly_labels),
        monthly_rev_json=json.dumps(monthly_rev_data),
        monthly_orders_json=json.dumps(monthly_orders_data),
        status_counts_json=json.dumps(status_counts),
        role_counts_json=json.dumps(role_map),
    )
    return render(request, 'admin_portal/dashboard.html', context)


# ─── Users ───────────────────────────────────────────────────────────────────

@admin_required
def users(request):
    q    = request.GET.get('q', '')
    role = request.GET.get('role', '')
    qs   = User.objects.all().order_by('-date_joined')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if role:
        qs = qs.filter(role=role)
    return render(request, 'admin_portal/users.html', {'users': qs, 'q': q, 'role': role})


@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    action = 'activate' if user.is_active else 'suspend'
    _log(request, AuditLog.ACTION_UPDATE, f'{action.title()}d user {user.username}')
    messages.success(request, f'User "{user.username}" {"activated" if user.is_active else "suspended"}.')
    return redirect('admin_portal:users')


# ─── Vendors ─────────────────────────────────────────────────────────────────

@admin_required
def vendors(request):
    q         = request.GET.get('q', '').strip()
    status    = request.GET.get('status', '')
    sf_status = request.GET.get('sf_status', '')
    qs        = Vendor.objects.select_related('user').order_by('-created_at')

    if q:
        qs = qs.filter(
            Q(store_name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(subdomain__icontains=q) |
            Q(custom_domain__icontains=q) |
            Q(storefront_payment_ref__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if sf_status:
        qs = qs.filter(storefront_status=sf_status)

    pending_sf_count = Vendor.objects.filter(storefront_status=Vendor.STOREFRONT_STATUS_PENDING).count()

    return render(request, 'admin_portal/vendors.html', {
        'vendors': qs,
        'q': q,
        'status': status,
        'sf_status': sf_status,
        'pending_sf_count': pending_sf_count,
    })


@admin_required
def vendor_approve(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.status = Vendor.STATUS_APPROVED
    vendor.save()
    _log(request, AuditLog.ACTION_APPROVE, f'Approved vendor: {vendor.store_name}')
    messages.success(request, f'"{vendor.store_name}" approved.')
    return redirect('admin_portal:vendors')


@admin_required
def vendor_suspend(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.status = Vendor.STATUS_SUSPENDED
    vendor.save()
    _log(request, AuditLog.ACTION_SUSPEND, f'Suspended vendor: {vendor.store_name}')
    messages.warning(request, f'"{vendor.store_name}" suspended.')
    return redirect('admin_portal:vendors')


@admin_required
def vendor_storefront_approve(request, pk):
    """Admin approves 10,000 ETB / year Funds Transfer (FT) for vendor standalone domain."""
    from django.utils import timezone
    from datetime import timedelta
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.storefront_status = Vendor.STOREFRONT_STATUS_ACTIVE
    vendor.storefront_enabled = True
    vendor.storefront_approved_at = timezone.now()
    vendor.storefront_expires_at = timezone.now() + timedelta(days=365)
    vendor.save()

    ref_info = f' (FT Ref: {vendor.storefront_payment_ref})' if vendor.storefront_payment_ref else ''
    _log(request, AuditLog.ACTION_APPROVE, f'Approved 10,000 ETB 1-Year Storefront subscription for: {vendor.store_name}{ref_info}')
    messages.success(request, f'Standalone domain unlocked for "{vendor.store_name}"! Active for 1 year (10,000 ETB FT approved).')
    return redirect('admin_portal:vendors')


@admin_required
def vendor_storefront_reject(request, pk):
    """Admin rejects / deactivates vendor standalone storefront."""
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.storefront_status = Vendor.STOREFRONT_STATUS_INACTIVE
    vendor.save()
    _log(request, AuditLog.ACTION_REJECT, f'Rejected standalone storefront for: {vendor.store_name}')
    messages.warning(request, f'Standalone storefront rejected/deactivated for "{vendor.store_name}".')
    return redirect('admin_portal:vendors')


# ─── Agents ──────────────────────────────────────────────────────────────────

@admin_required
def agents(request):
    qs = Agent.objects.select_related('user').annotate(
        deal_count=Count('deals'),
        revenue=Sum('deals__value')
    ).order_by('-revenue')
    return render(request, 'admin_portal/agents.html', {'agents': qs})


@admin_required
def agent_toggle(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    agent.is_active = not agent.is_active
    agent.save()
    messages.success(request, f'Agent "{agent.user.username}" '
                               f'{"activated" if agent.is_active else "deactivated"}.')
    return redirect('admin_portal:agents')


# ─── Products ────────────────────────────────────────────────────────────────

@admin_required
def products(request):
    q  = request.GET.get('q', '')
    qs = Product.objects.select_related('vendor', 'category').order_by('-created_at')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(vendor__store_name__icontains=q))
    return render(request, 'admin_portal/products.html', {'products': qs, 'q': q})


@admin_required
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f'Product "{product.name}" '
                               f'{"activated" if product.is_active else "deactivated"}.')
    return redirect('admin_portal:products')


# ─── Orders ──────────────────────────────────────────────────────────────────

@admin_required
def orders(request):
    status = request.GET.get('status', '')
    qs     = Order.objects.select_related('user').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'admin_portal/orders.html', {'orders': qs, 'status': status})


@admin_required
def order_update_status(request, pk):
    if request.method == 'POST':
        order  = get_object_or_404(Order, pk=pk)
        new_st = request.POST.get('status')
        if new_st in dict(Order.STATUS_CHOICES):
            old = order.get_status_display()
            order.status = new_st
            order.save()
            _log(request, AuditLog.ACTION_UPDATE,
                 f'Order {order.order_number}: {old} → {order.get_status_display()}')
            messages.success(request, f'Order #{order.order_number} updated to '
                                       f'{order.get_status_display()}.')
    return redirect('admin_portal:orders')


# ─── Disputes ────────────────────────────────────────────────────────────────

@admin_required
def disputes(request):
    qs = Dispute.objects.select_related('order', 'raised_by').order_by('-created_at')
    return render(request, 'admin_portal/disputes.html', {'disputes': qs})


@admin_required
def dispute_resolve(request, pk):
    dispute = get_object_or_404(Dispute, pk=pk)
    dispute.status      = Dispute.STATUS_RESOLVED
    dispute.resolved_by = request.user
    dispute.save()
    _log(request, AuditLog.ACTION_UPDATE, f'Resolved dispute #{dispute.pk}: {dispute.subject}')
    messages.success(request, f'Dispute #{dispute.pk} resolved.')
    return redirect('admin_portal:disputes')


# ─── Audit Logs ──────────────────────────────────────────────────────────────

@admin_required
def audit_logs(request):
    logs = AuditLog.objects.select_related('actor').order_by('-created_at')[:200]
    return render(request, 'admin_portal/audit_logs.html', {'logs': logs})


# ─── Settings ────────────────────────────────────────────────────────────────

@admin_required
def settings_view(request):
    from accounts.models import User
    from vendors.models import Vendor
    from store.models import Product
    payment_methods = [
        ('cod',    'Cash on Delivery · ሲደርስ ክፈሉ',  '#1f7b3a'),
        ('card',   'Telebirr · CBE Birr · Amole',     '#1a4b8a'),
        ('wallet', 'HelloCash · M-Pesa · Dashen',     '#b85a1a'),
    ]
    return render(request, 'admin_portal/settings.html', {
        'total_users':    User.objects.count(),
        'total_vendors':  Vendor.objects.count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'payment_methods': payment_methods,
    })


# ─── Vendor Payouts ───────────────────────────────────────────────────────────

@admin_required
def payouts(request):
    from vendors.models import VendorPayout
    qs = VendorPayout.objects.select_related('vendor').order_by('-requested_at')
    return render(request, 'admin_portal/payouts.html', {'payouts': qs})


@admin_required
def payout_process(request, pk):
    from vendors.models import VendorPayout
    from django.utils import timezone
    payout = get_object_or_404(VendorPayout, pk=pk)
    action = request.POST.get('action')
    if action == 'pay':
        payout.status = VendorPayout.STATUS_PAID
        payout.processed_at = timezone.now()
        payout.transaction_id = request.POST.get('transaction_id', '')
        payout.save()
        # Deduct from vendor balance
        payout.vendor.balance = max(0, payout.vendor.balance - payout.amount)
        payout.vendor.save()
        _log(request, AuditLog.ACTION_UPDATE, f'Paid payout #{payout.pk} to {payout.vendor.store_name}: ETB {payout.amount}')
        messages.success(request, f'Payout of ETB {payout.amount} to {payout.vendor.store_name} marked as paid.')
    elif action == 'reject':
        payout.status = VendorPayout.STATUS_REJECTED
        payout.note = request.POST.get('note', 'Rejected by admin')
        payout.processed_at = timezone.now()
        payout.save()
        messages.warning(request, f'Payout #{payout.pk} rejected.')
    return redirect('admin_portal:payouts')


# ─── Vendor reject ────────────────────────────────────────────────────────────

@admin_required
def vendor_reject(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.status = 'rejected' if hasattr(vendor, 'rejected') else Vendor.STATUS_SUSPENDED
    vendor.save()
    reason = request.POST.get('reason', 'Not approved')
    _log(request, AuditLog.ACTION_SUSPEND, f'Rejected vendor: {vendor.store_name} — {reason}')
    messages.warning(request, f'"{vendor.store_name}" rejected.')
    return redirect('admin_portal:vendors')


# ─── Platform Analytics ───────────────────────────────────────────────────────

@admin_required
def analytics(request):
    import json
    from django.db.models.functions import TruncMonth
    from django.db.models import Sum, Count
    from datetime import timezone

    total_revenue = Order.objects.filter(status=Order.STATUS_DELIVERED).aggregate(t=Sum('total'))['t'] or 0
    total_orders = Order.objects.count()
    delivered_orders = Order.objects.filter(status=Order.STATUS_DELIVERED).count()
    pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()
    fulfillment_rate = round((delivered_orders / total_orders * 100), 1) if total_orders > 0 else 100.0

    platform_target = 300000.0
    target_achieved_pct = min(100.0, round((float(total_revenue) / platform_target) * 100, 1))

    # Monthly revenue
    monthly_revenue = Order.objects.filter(
        status=Order.STATUS_DELIVERED
    ).annotate(
        month=TruncMonth('created_at', tzinfo=timezone.utc)
    ).values('month').annotate(revenue=Sum('total'), orders=Count('id')).order_by('month')

    monthly_labels = []
    monthly_rev_data = []
    monthly_orders_data = []
    for m in monthly_revenue:
        monthly_labels.append(m['month'].strftime('%b %Y') if m['month'] else '')
        monthly_rev_data.append(float(m['revenue'] or 0))
        monthly_orders_data.append(int(m['orders'] or 0))

    if not monthly_labels:
        monthly_labels = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        monthly_rev_data = [15000, 32000, 58000, 84000, 120000, float(total_revenue) or 185000]
        monthly_orders_data = [18, 35, 60, 85, 115, max(total_orders, 140)]

    # Top vendors
    top_vendors = Vendor.objects.filter(
        status=Vendor.STATUS_APPROVED
    ).order_by('-total_sales')[:10]

    top_vendor_names = [v.store_name for v in top_vendors[:6]]
    top_vendor_sales = [float(v.total_sales or 0) for v in top_vendors[:6]]
    if not top_vendor_names:
        top_vendor_names = ['Mariam Goods', 'Addis Fashion', 'Sheba Crafts', 'Entoto Coffee', 'Habesha Leather']
        top_vendor_sales = [45000, 32000, 24000, 18000, 12500]

    # Top products
    top_products = OrderItem.objects.values(
        'product__name', 'product__vendor__store_name'
    ).annotate(
        total_sold=Count('id'),
        total_revenue=Sum('product_price')
    ).order_by('-total_revenue')[:10]

    # User registrations by role
    role_counts = User.objects.values('role').annotate(count=Count('id')).order_by('role')
    role_map = {'customer': 0, 'vendor': 0, 'agent': 0, 'admin': 0}
    for r in role_counts:
        if r['role'] in role_map:
            role_map[r['role']] = r['count']
    if sum(role_map.values()) == 0:
        role_map = {'customer': 65, 'vendor': 18, 'agent': 12, 'admin': 4}

    # Order status breakdown
    status_counts = {
        'pending': pending_orders,
        'processing': Order.objects.filter(status=Order.STATUS_PROCESSING).count(),
        'shipped': Order.objects.filter(status=Order.STATUS_SHIPPED).count(),
        'delivered': delivered_orders,
        'cancelled': Order.objects.filter(status=Order.STATUS_CANCELLED).count(),
    }
    if sum(status_counts.values()) == 0:
        status_counts = {'pending': 3, 'processing': 4, 'shipped': 6, 'delivered': 16, 'cancelled': 1}

    context = {
        'monthly_revenue': list(monthly_revenue),
        'top_vendors': top_vendors,
        'top_products': list(top_products),
        'role_counts': list(role_counts),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'fulfillment_rate': fulfillment_rate,
        'platform_target': platform_target,
        'target_achieved_pct': target_achieved_pct,
        # JSON serialized
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_rev_json': json.dumps(monthly_rev_data),
        'monthly_orders_json': json.dumps(monthly_orders_data),
        'top_vendor_names_json': json.dumps(top_vendor_names),
        'top_vendor_sales_json': json.dumps(top_vendor_sales),
        'role_counts_json': json.dumps(role_map),
        'status_counts_json': json.dumps(status_counts),
    }
    return render(request, 'admin_portal/analytics.html', context)


# ─── Agent Commissions ────────────────────────────────────────────────────────

@admin_required
def agent_commissions(request):
    from agents.models import AgentCommission
    comms = AgentCommission.objects.select_related('agent__user', 'deal').order_by('-created_at')
    if request.method == 'POST':
        comm_id = request.POST.get('comm_id')
        from django.utils import timezone
        AgentCommission.objects.filter(pk=comm_id).update(is_paid=True, paid_at=timezone.now())
        messages.success(request, 'Commission marked as paid.')
        return redirect('admin_portal:agent_commissions')
    return render(request, 'admin_portal/agent_commissions.html', {'commissions': comms})


# ─── Categories ───────────────────────────────────────────────────────────────

@admin_required
def categories(request):
    from store.models import Category
    from store.admin import CategoryAdmin
    qs = Category.objects.all().order_by('order', 'name')
    return render(request, 'admin_portal/categories.html', {'categories': qs})


@admin_required
def category_toggle(request, pk):
    from store.models import Category
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save()
    messages.success(request, f'Category "{cat.name}" {"activated" if cat.is_active else "deactivated"}.')
    return redirect('admin_portal:categories')
