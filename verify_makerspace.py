"""Final makerspace verification."""
import os, sys, struct, tempfile
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
import django; django.setup()

from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

print('=' * 55)
print('  MAKERSPACE MODULE — Final Verification')
print('=' * 55)

# ── 1. URLs ───────────────────────────────────────────────────
print('\n1. URL Resolution')
urls = [
    ('makerspace:landing',             []),
    ('makerspace:workshop_3d',         []),
    ('makerspace:workshop_laser',      []),
    ('makerspace:workshop_cnc',        []),
    ('makerspace:workshop_design',     []),
    ('makerspace:submit_order',        []),
    ('makerspace:my_orders',           []),
    ('makerspace:order_detail',        [1]),
    ('makerspace:accept_quote',        [1]),
    ('makerspace:cancel_order',        [1]),
    ('makerspace:vendor_dashboard',    []),
    ('makerspace:vendor_orders',       []),
    ('makerspace:vendor_order_detail', [1]),
    ('makerspace:vendor_settings',     []),
]
ok = fail = 0
for name, args in urls:
    try:
        url = reverse(name, args=args)
        print(f'  OK  {url:42s} {name}')
        ok += 1
    except Exception as e:
        print(f'  FAIL {name}: {e}')
        fail += 1
print(f'  {ok} OK  |  {fail} FAILED')

# ── 2. Templates ──────────────────────────────────────────────
print('\n2. Template Files')
templates = [
    'makerspace/landing.html',
    'makerspace/workshop_3d.html',
    'makerspace/workshop_laser.html',
    'makerspace/workshop_cnc.html',
    'makerspace/workshop_design.html',
    'makerspace/submit_order.html',
    'makerspace/order_detail.html',
    'makerspace/my_orders.html',
    'makerspace/confirm_cancel.html',
    'makerspace/vendor/dashboard.html',
    'makerspace/vendor/orders.html',
    'makerspace/vendor/order_detail.html',
    'makerspace/vendor/settings.html',
]
tok = tfail = 0
for t in templates:
    try:
        get_template(t)
        print(f'  OK  {t}')
        tok += 1
    except TemplateDoesNotExist:
        print(f'  MISSING: {t}')
        tfail += 1
    except Exception as e:
        print(f'  ERROR   {t}: {e}')
        tfail += 1
print(f'  {tok} OK  |  {tfail} errors')

# ── 3. Database ───────────────────────────────────────────────
print('\n3. Database Records')
from makerspace.models import MakerspaceProfile, MakerspaceOrder
print(f'  Profiles: {MakerspaceProfile.objects.count()}')
print(f'  Active:   {MakerspaceProfile.objects.filter(is_active=True).count()}')
print(f'  Orders:   {MakerspaceOrder.objects.count()}')
for o in MakerspaceOrder.objects.all():
    print(f'    {o.order_number}  {o.get_service_type_display():20s}  {o.get_status_display()}  ETB {o.final_price}')

# ── 4. File analysis ──────────────────────────────────────────
print('\n4. STL File Analysis Test')
from makerspace.file_analysis import analyse_file, calculate_price

# Build a tiny binary STL (1 right triangle, legs 10mm each)
with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
    f.write(b'\x00' * 80)
    f.write(struct.pack('<I', 1))
    f.write(struct.pack('<3f', 0, 0, 1))   # normal
    f.write(struct.pack('<3f', 0, 0, 0))   # v1
    f.write(struct.pack('<3f', 10, 0, 0))  # v2
    f.write(struct.pack('<3f', 0, 10, 0))  # v3
    f.write(b'\x00\x00')
    stl_path = f.name

result = analyse_file(stl_path, '3d_print', '3d_pla', 30)
os.unlink(stl_path)
print(f'  volume  = {result["volume_cm3"]:.4f} cm³')
print(f'  grams   = {result["grams"]:.4f} g  (at 30% infill, PLA 1.24 g/cm³)')
print(f'  type    = {result["file_type"]}')
print(f'  error   = {result["error"]}')

profile = MakerspaceProfile.objects.filter(is_active=True).first()
if profile:
    price = calculate_price(result, '3d_print', '3d_pla', 30, 2, profile)
    print(f'  price   = ETB {price:.2f}  (qty=2, rate=ETB {profile.price_pla_per_gram}/g)')

# ── 5. Summary ────────────────────────────────────────────────
print('\n' + '=' * 55)
print('  Access Points:')
print('  Customer landing: http://127.0.0.1:8000/makerspace/')
print('  Submit order:     http://127.0.0.1:8000/makerspace/submit/')
print('  My orders:        http://127.0.0.1:8000/makerspace/orders/')
print('  Vendor dashboard: http://127.0.0.1:8000/makerspace/vendor/')
print()
print('  Login as ahmed_store / vendor123 to manage makerspace orders.')
print('  Login as customer1 / customer123 to submit and track orders.')
print('=' * 55)
