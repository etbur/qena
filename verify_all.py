"""Full verification: URLs, templates, DB counts, language files, images."""
import os
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
import django
django.setup()

from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

print("=" * 65)
print("  QENAGEBEYA 🇪🇹 — Full Platform Verification")
print("=" * 65)

# ── 1. URL resolution ─────────────────────────────────────────────────────────
print("\n1. URL Resolution")
urls = [
    # Store
    ('store:home',                    []),
    ('store:product_list',            []),
    ('store:cart',                    []),
    ('store:wishlist',                []),
    # Accounts
    ('accounts:login',                []),
    ('accounts:register',             []),
    ('accounts:profile',              []),
    ('accounts:role_redirect',        []),
    # Orders
    ('orders:checkout',               []),
    ('orders:order_list',             []),
    # Vendors
    ('vendors:setup',                 []),
    ('vendors:pending',               []),
    ('vendors:dashboard',             []),
    ('vendors:products',              []),
    ('vendors:product_add',           []),
    ('vendors:analytics',             []),
    ('vendors:settings',              []),
    ('vendors:orders',                []),
    ('vendors:inventory',             []),
    ('vendors:payouts',               []),
    ('vendors:customers',             []),
    # Agents
    ('agents:dashboard',              []),
    ('agents:clients',                []),
    ('agents:client_add',             []),
    ('agents:deals',                  []),
    ('agents:deal_add',               []),
    ('agents:inquiries',              []),
    ('agents:inquiry_create',         []),
    ('agents:tasks',                  []),
    ('agents:proposals',              []),
    ('agents:commissions',            []),
    ('agents:performance',            []),
    # Admin portal
    ('admin_portal:dashboard',        []),
    ('admin_portal:users',            []),
    ('admin_portal:vendors',          []),
    ('admin_portal:agents',           []),
    ('admin_portal:products',         []),
    ('admin_portal:categories',       []),
    ('admin_portal:orders',           []),
    ('admin_portal:payouts',          []),
    ('admin_portal:disputes',         []),
    ('admin_portal:agent_commissions',[]),
    ('admin_portal:analytics',        []),
    ('admin_portal:audit_logs',       []),
    ('admin_portal:settings',         []),
]
ok = fail = 0
for name, args in urls:
    try:
        url = reverse(name, args=args)
        print(f'  ✓  {url:48s} {name}')
        ok += 1
    except Exception as e:
        print(f'  ✗  FAIL {name}: {e}')
        fail += 1
print(f'\n  {ok} OK  |  {fail} FAILED')

# ── 2. Template files ─────────────────────────────────────────────────────────
print("\n2. Template Files")
templates_needed = [
    'base.html',
    # Store
    'store/home.html', 'store/product_list.html', 'store/product_detail.html',
    'store/cart.html', 'store/wishlist.html', 'store/category.html',
    # Accounts
    'accounts/login.html', 'accounts/register.html', 'accounts/profile.html',
    # Orders
    'orders/checkout.html', 'orders/order_list.html', 'orders/order_detail.html',
    # Vendors
    'vendors/base_vendor.html', 'vendors/dashboard.html', 'vendors/products.html',
    'vendors/product_form.html', 'vendors/orders.html', 'vendors/settings.html',
    'vendors/setup.html', 'vendors/pending.html', 'vendors/store.html',
    'vendors/analytics.html', 'vendors/product_confirm_delete.html',
    'vendors/inventory.html', 'vendors/payouts.html', 'vendors/customers.html',
    # Agents
    'agents/base_agent.html', 'agents/dashboard.html', 'agents/clients.html',
    'agents/client_form.html', 'agents/deals.html', 'agents/deal_form.html',
    'agents/inquiries.html', 'agents/inquiry_detail.html', 'agents/inquiry_form.html',
    'agents/performance.html', 'agents/tasks.html', 'agents/proposals.html',
    'agents/commissions.html', 'agents/confirm_delete.html',
    # Admin portal
    'admin_portal/base_admin.html', 'admin_portal/dashboard.html',
    'admin_portal/users.html', 'admin_portal/vendors.html', 'admin_portal/agents.html',
    'admin_portal/products.html', 'admin_portal/categories.html',
    'admin_portal/orders.html', 'admin_portal/payouts.html',
    'admin_portal/disputes.html', 'admin_portal/agent_commissions.html',
    'admin_portal/analytics.html', 'admin_portal/audit_logs.html',
    'admin_portal/settings.html',
]
tok = tfail = 0
for t in templates_needed:
    try:
        get_template(t)
        print(f'  ✓  {t}')
        tok += 1
    except TemplateDoesNotExist:
        print(f'  ✗  MISSING: {t}')
        tfail += 1
    except Exception as e:
        print(f'  ✗  ERROR {t}: {e}')
        tfail += 1
print(f'\n  {tok} OK  |  {tfail} MISSING/ERROR')

# ── 3. Database records ───────────────────────────────────────────────────────
print("\n3. Database Records")
from accounts.models import User
from vendors.models import Vendor, VendorPayout
from agents.models import Agent, Client, Deal, Task, Proposal, AgentCommission
from store.models import Category, Product
from orders.models import Order
from admin_portal.models import AuditLog, Dispute

rows = [
    ('Users',            User.objects.count()),
    ('Vendors',          Vendor.objects.count()),
    ('Agents',           Agent.objects.count()),
    ('Clients',          Client.objects.count()),
    ('Deals',            Deal.objects.count()),
    ('Tasks',            Task.objects.count()),
    ('Proposals',        Proposal.objects.count()),
    ('AgentCommissions', AgentCommission.objects.count()),
    ('VendorPayouts',    VendorPayout.objects.count()),
    ('Categories',       Category.objects.count()),
    ('Products',         Product.objects.count()),
    ('Orders',           Order.objects.count()),
    ('AuditLogs',        AuditLog.objects.count()),
    ('Disputes',         Dispute.objects.count()),
]
for label, count in rows:
    status = '✓' if count > 0 else '○'
    print(f'  {status}  {label}: {count}')

# ── 4. Product images ─────────────────────────────────────────────────────────
print("\n4. Product Images")
from django.conf import settings
products_with_img = 0
products_missing  = 0
for p in Product.objects.all():
    if p.image:
        path = settings.MEDIA_ROOT / str(p.image)
        if os.path.exists(path):
            products_with_img += 1
        else:
            print(f'  ✗  FILE MISSING: {p.image} ({p.name})')
            products_missing += 1
    else:
        products_missing += 1
        print(f'  ○  NO IMAGE: {p.name}')
print(f'  Images on disk: {products_with_img} / {Product.objects.count()}')

# ── 5. Translation files ──────────────────────────────────────────────────────
print("\n5. Translation Files")
locale_base = os.path.join(os.path.dirname(__file__), 'locale')
for lang in ['am', 'om']:
    po  = os.path.join(locale_base, lang, 'LC_MESSAGES', 'django.po')
    mo  = os.path.join(locale_base, lang, 'LC_MESSAGES', 'django.mo')
    print(f'  {lang}: .po {"✓" if os.path.exists(po) else "✗"}  '
          f'.mo {"✓" if os.path.exists(mo) else "✗"}')

# ── 6. Credentials ────────────────────────────────────────────────────────────
print("\n6. Login Credentials")
portal_map = {
    'admin':    '/portal/',
    'vendor':   '/vendor/dashboard/',
    'agent':    '/agent/dashboard/',
    'customer': '/',
}
for u in User.objects.all().order_by('role', 'username'):
    portal = portal_map.get(u.role, '/')
    print(f'  {u.username:20s} role={u.role:8s} staff={str(u.is_staff):5s} → {portal}')

print("\n" + "=" * 65)
print("  python manage.py runserver")
print("  Store     → http://127.0.0.1:8000/")
print("  Admin     → http://127.0.0.1:8000/portal/     admin/admin123")
print("  Vendor    → http://127.0.0.1:8000/vendor/dashboard/")
print("  Agent     → http://127.0.0.1:8000/agent/dashboard/")
print("  Amharic   → http://127.0.0.1:8000/am/")
print("  Oromiffa  → http://127.0.0.1:8000/om/")
print("=" * 65)
