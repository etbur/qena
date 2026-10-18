"""Full live module verification."""
import os
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
import django; django.setup()

from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

print('=' * 58)
print('  LIVE STREAMS MODULE — Verification')
print('=' * 58)

# ── URLs ──────────────────────────────────────────────────────
print('\n1. URL Resolution')
urls = [
    ('live:home',           []),
    ('live:vendor_streams', []),
    ('live:stream_create',  []),
]
ok = fail = 0
for name, args in urls:
    try:
        url = reverse(name, args=args)
        print(f'  OK  {url:40s} {name}')
        ok += 1
    except Exception as e:
        print(f'  FAIL {name}: {e}')
        fail += 1
# UUID-based URLs need a real UUID
import uuid
test_uuid = uuid.uuid4()
uuid_urls = [
    ('live:watch',       [test_uuid]),
    ('live:go_live',     [test_uuid]),
    ('live:stream_end',  [test_uuid]),
    ('live:api_pin',     [test_uuid]),
    ('live:api_info',    [test_uuid]),
]
for name, args in uuid_urls:
    try:
        url = reverse(name, args=args)
        print(f'  OK  {url[:55]:55s} {name}')
        ok += 1
    except Exception as e:
        print(f'  FAIL {name}: {e}')
        fail += 1
print(f'  {ok} OK  |  {fail} FAILED')

# ── Templates ─────────────────────────────────────────────────
print('\n2. Template Files')
templates = [
    'live/home.html',
    'live/watch.html',
    'live/vendor/streams.html',
    'live/vendor/stream_form.html',
    'live/vendor/go_live.html',
    'live/vendor/end_confirm.html',
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

# ── DB & seed ─────────────────────────────────────────────────
print('\n3. Database & Seed')
from live.models import LiveStream, LiveChat
from vendors.models import Vendor

streams = LiveStream.objects.count()
print(f'  Streams: {streams}')

# Create a demo stream if none exist
if streams == 0:
    vendor = Vendor.objects.filter(status=Vendor.STATUS_APPROVED).first()
    if vendor:
        s = LiveStream.objects.create(
            vendor=vendor,
            title='🇪🇹 Ethiopian Coffee Ceremony Live',
            description='Watch us showcase premium Ethiopian coffee and Habesha crafts live!',
            status=LiveStream.STATUS_LIVE,
        )
        from django.utils import timezone
        s.started_at = timezone.now()
        s.save()
        print(f'  Created demo stream: {s.title}')
        print(f'  UUID: {s.stream_id}')
        print(f'  URL:  http://127.0.0.1:8000/live/{s.stream_id}/')
    else:
        print('  No approved vendor found — run seed_data.py first')
else:
    for s in LiveStream.objects.all():
        print(f'  [{s.status.upper():9s}] {s.title[:40]} — {s.vendor.store_name}')
        print(f'           http://127.0.0.1:8000/live/{s.stream_id}/')

# ── ASGI / Channels ───────────────────────────────────────────
print('\n4. Channels Configuration')
from django.conf import settings
ch = getattr(settings, 'CHANNEL_LAYERS', {})
asgi = getattr(settings, 'ASGI_APPLICATION', '')
print(f'  ASGI_APPLICATION: {asgi}')
print(f'  CHANNEL_LAYERS backend: {ch.get("default", {}).get("BACKEND", "NOT SET")}')

from live.routing import websocket_urlpatterns
print(f'  WebSocket patterns: {len(websocket_urlpatterns)}')
print(f'  Pattern: {websocket_urlpatterns[0].pattern}')

print('\n' + '=' * 58)
print('  HOW TO RUN:')
print()
print('  Development (HTTP only, WebSocket via Daphne):')
print('    daphne -p 8000 qenagebeya.asgi:application')
print()
print('  OR simple runserver (auto-detects channels):')
print('    python manage.py runserver')
print()
print('  Live streams:  http://127.0.0.1:8000/live/')
print('  Vendor panel:  http://127.0.0.1:8000/live/vendor/')
print('  WebSocket:     ws://127.0.0.1:8000/ws/live/<uuid>/')
print('=' * 58)
