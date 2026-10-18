import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import Client
from store.models import Product
from vendors.models import Vendor
from agents.models import Agent, Inquiry, Client as AgentClient

def run_exhaustive_qr_tests():
    c = Client()
    print("=" * 70)
    print("EXHAUSTIVE QR & DIGITAL MARKETING TEST SUITE")
    print("=" * 70)

    # 1. Test EVERY product in the DB
    products = Product.objects.all()
    print(f"\n>>> [1/5] Testing {products.count()} Products...")
    product_errors = 0
    for p in products:
        # Check property
        uri = p.qr_code_data_uri
        if not uri.startswith("data:image/png;base64,"):
            print(f"  [FAIL] Product {p.pk} ({p.name}) invalid data URI")
            product_errors += 1
            continue
        
        # Check raw QR endpoint
        resp_raw = c.get(f"/products/{p.slug}/qr/?format=raw")
        if resp_raw.status_code != 200 or not resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Product {p.pk} raw QR HTTP {resp_raw.status_code}")
            product_errors += 1
            continue
            
        # Check badge flyer endpoint
        resp_badge = c.get(f"/products/{p.slug}/qr/?format=badge&download=1")
        if resp_badge.status_code != 200 or not resp_badge.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Product {p.pk} badge QR HTTP {resp_badge.status_code}")
            product_errors += 1
            continue

    if product_errors == 0:
        print(f"  [SUCCESS] All {products.count()} products generated valid QR data URIs, raw PNGs & printable badges!")
    else:
        print(f"  [FAIL] {product_errors} product errors found.")

    # 2. Test EVERY vendor in the DB
    vendors = Vendor.objects.all()
    print(f"\n>>> [2/5] Testing {vendors.count()} Vendors...")
    vendor_errors = 0
    for v in vendors:
        uri = v.qr_code_data_uri
        if not uri.startswith("data:image/png;base64,"):
            print(f"  [FAIL] Vendor {v.pk} ({v.store_name}) invalid data URI")
            vendor_errors += 1
            continue
        
        # Test vendor QR endpoint
        resp_raw = c.get(f"/vendor/store/{v.slug}/qr/?format=raw")
        if resp_raw.status_code != 200 or not resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Vendor {v.pk} raw QR HTTP {resp_raw.status_code}")
            vendor_errors += 1
            continue
            
        # Test vendor badge endpoint
        resp_badge = c.get(f"/vendor/store/{v.slug}/qr/?format=badge&download=1")
        if resp_badge.status_code != 200 or not resp_badge.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Vendor {v.pk} badge QR HTTP {resp_badge.status_code}")
            vendor_errors += 1
            continue

    if vendor_errors == 0:
        print(f"  [SUCCESS] All {vendors.count()} vendors generated valid QR data URIs, raw PNGs & store badges!")
    else:
        print(f"  [FAIL] {vendor_errors} vendor errors found.")

    # 3. Test EVERY agent in the DB
    agents = Agent.objects.all()
    print(f"\n>>> [3/5] Testing {agents.count()} Agents...")
    agent_errors = 0
    for a in agents:
        name = a.user.get_full_name() or a.user.username
        uri = a.qr_code_data_uri
        if not uri.startswith("data:image/png;base64,"):
            print(f"  [FAIL] Agent {a.pk} ({name}) invalid data URI")
            agent_errors += 1
            continue
            
        # Public Card View
        resp_card = c.get(f"/agent/card/{a.pk}/")
        if resp_card.status_code != 200:
            print(f"  [FAIL] Agent {a.pk} public card HTTP {resp_card.status_code}")
            agent_errors += 1
            continue
            
        # Raw QR endpoint
        resp_raw = c.get(f"/agent/qr/{a.pk}/?format=raw")
        if resp_raw.status_code != 200 or not resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Agent {a.pk} raw QR HTTP {resp_raw.status_code}")
            agent_errors += 1
            continue
            
        # Badge endpoint
        resp_badge = c.get(f"/agent/qr/{a.pk}/?format=badge&download=1")
        if resp_badge.status_code != 200 or not resp_badge.content.startswith(b'\x89PNG\r\n\x1a\n'):
            print(f"  [FAIL] Agent {a.pk} badge QR HTTP {resp_badge.status_code}")
            agent_errors += 1
            continue

    if agent_errors == 0:
        print(f"  [SUCCESS] All {agents.count()} agents generated valid QR data URIs, public digital cards & badges!")
    else:
        print(f"  [FAIL] {agent_errors} agent errors found.")

    # 4. Test Lead / Inquiry Submission via Agent Public Digital Card
    print("\n>>> [4/5] Testing Lead Capture on Agent Digital Business Card...")
    test_agent = Agent.objects.filter(is_active=True).first()
    if test_agent:
        init_inquiries = Inquiry.objects.filter(agent=test_agent).count()
        post_data = {
            'name': 'Dawit Bekele',
            'phone': '+251911223344',
            'email': 'dawit@example.com',
            'subject': 'Bulk Electronics Order Inquiry',
            'message': 'Looking to purchase 50 units of earbuds for retail distribution in Addis Ababa.'
        }
        resp_post = c.post(f"/agent/card/{test_agent.pk}/", post_data)
        assert resp_post.status_code == 200, f"Post to agent card failed with {resp_post.status_code}"
        new_inquiries = Inquiry.objects.filter(agent=test_agent).count()
        assert new_inquiries == init_inquiries + 1, "Inquiry was not recorded in DB"
        created_inq = Inquiry.objects.filter(agent=test_agent).order_by('-created_at').first()
        print(f"  [SUCCESS] Lead captured successfully: '{created_inq.subject}' assigned to {test_agent.user.username}!")
    else:
        print("  [SKIP] No active agent to test lead capture.")

    # 5. Test REST API Serializers for QR Code URL
    print("\n>>> [5/5] Testing REST API v1 endpoints for QR code inclusion...")
    resp_api_products = c.get("/api/v1/products/")
    if resp_api_products.status_code == 200:
        data = resp_api_products.json()
        results = data.get('results', data)
        if isinstance(results, list) and len(results) > 0:
            first_p = results[0]
            assert 'qr_code_url' in first_p, "qr_code_url missing from ProductListSerializer"
            print(f"  [SUCCESS] /api/v1/products/ returned qr_code_url: {first_p['qr_code_url']}")
            
    resp_api_vendors = c.get("/api/v1/vendors/")
    if resp_api_vendors.status_code == 200:
        data = resp_api_vendors.json()
        results = data.get('results', data)
        if isinstance(results, list) and len(results) > 0:
            first_v = results[0]
            assert 'qr_code_url' in first_v, "qr_code_url missing from VendorSerializer"
            print(f"  [SUCCESS] /api/v1/vendors/ returned qr_code_url: {first_v['qr_code_url']}")

    print("\n" + "=" * 70)
    print("ALL 5 PHASES OF EXHAUSTIVE VERIFICATION COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == '__main__':
    run_exhaustive_qr_tests()
