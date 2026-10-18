import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import RequestFactory, Client
from store.models import Product
from vendors.models import Vendor
from agents.models import Agent

def verify_all_qr():
    print("=" * 60)
    print("VERIFYING QR CODE GENERATION FOR PRODUCTS, VENDORS, AND AGENTS")
    print("=" * 60)
    
    rf = RequestFactory()
    c = Client()
    
    # 1. Product QR Code Verification
    product = Product.objects.filter(is_active=True).first()
    if product:
        print(f"\n[1] Testing Product QR Code for: {product.name} (Slug: {product.slug})")
        data_uri = product.qr_code_data_uri
        assert data_uri.startswith("data:image/png;base64,"), "Product QR data URI invalid"
        print(f"  [OK] Data URI generated successfully: {data_uri[:45]}...")
        
        # Test Raw QR endpoint
        resp_raw = c.get(f"/products/{product.slug}/qr/?format=raw")
        assert resp_raw.status_code == 200, f"Raw QR endpoint returned {resp_raw.status_code}"
        assert resp_raw['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'), "Raw QR is not valid PNG"
        print(f"  [OK] Raw QR Endpoint (/products/{product.slug}/qr/?format=raw): 200 OK ({len(resp_raw.content)} bytes)")
        
        # Test Badge QR endpoint
        resp_badge = c.get(f"/products/{product.slug}/qr/?format=badge&download=1")
        assert resp_badge.status_code == 200, f"Badge QR endpoint returned {resp_badge.status_code}"
        assert resp_badge['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert 'attachment' in resp_badge['Content-Disposition'], "Content-Disposition not attachment"
        assert resp_badge.content.startswith(b'\x89PNG\r\n\x1a\n'), "Badge QR is not valid PNG"
        print(f"  [OK] Branded Flyer Badge Endpoint: 200 OK ({len(resp_badge.content)} bytes)")
    else:
        print("  [!] No products found in database.")

    # 2. Vendor QR Code Verification
    vendor = Vendor.objects.filter(status=Vendor.STATUS_APPROVED).first()
    if vendor:
        print(f"\n[2] Testing Vendor QR Code for: {vendor.store_name} (Slug: {vendor.slug})")
        data_uri = vendor.qr_code_data_uri
        assert data_uri.startswith("data:image/png;base64,"), "Vendor QR data URI invalid"
        print(f"  [OK] Data URI generated successfully: {data_uri[:45]}...")
        
        # Test Raw QR endpoint
        resp_raw = c.get(f"/vendor/store/{vendor.slug}/qr/?format=raw")
        assert resp_raw.status_code == 200, f"Vendor Raw QR returned {resp_raw.status_code}"
        assert resp_raw['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'), "Raw QR is not valid PNG"
        print(f"  [OK] Raw QR Endpoint (/vendor/store/{vendor.slug}/qr/?format=raw): 200 OK ({len(resp_raw.content)} bytes)")

        # Test Badge QR endpoint
        resp_badge = c.get(f"/vendor/store/{vendor.slug}/qr/?format=badge&download=1")
        assert resp_badge.status_code == 200, f"Vendor Badge QR returned {resp_badge.status_code}"
        assert resp_badge['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert 'attachment' in resp_badge['Content-Disposition'], "Content-Disposition not attachment"
        print(f"  [OK] Branded Store Badge Endpoint: 200 OK ({len(resp_badge.content)} bytes)")
    else:
        print("  [!] No approved vendors found in database.")

    # 3. Agent QR Code Verification
    agent = Agent.objects.filter(is_active=True).first()
    if agent:
        name = agent.user.get_full_name() or agent.user.username
        print(f"\n[3] Testing Agent QR Code for: {name} (PK: {agent.pk})")
        data_uri = agent.qr_code_data_uri
        assert data_uri.startswith("data:image/png;base64,"), "Agent QR data URI invalid"
        print(f"  [OK] Data URI generated successfully: {data_uri[:45]}...")
        
        # Test Public Card endpoint
        resp_card = c.get(f"/agent/card/{agent.pk}/")
        assert resp_card.status_code == 200, f"Agent public card returned {resp_card.status_code}"
        print(f"  [OK] Public Digital Card Landing Page (/agent/card/{agent.pk}/): 200 OK")
        
        # Test Raw QR endpoint
        resp_raw = c.get(f"/agent/qr/{agent.pk}/?format=raw")
        assert resp_raw.status_code == 200, f"Agent Raw QR returned {resp_raw.status_code}"
        assert resp_raw['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert resp_raw.content.startswith(b'\x89PNG\r\n\x1a\n'), "Raw QR is not valid PNG"
        print(f"  [OK] Raw QR Endpoint (/agent/qr/{agent.pk}/?format=raw): 200 OK ({len(resp_raw.content)} bytes)")

        # Test Badge QR endpoint
        resp_badge = c.get(f"/agent/qr/{agent.pk}/?format=badge&download=1")
        assert resp_badge.status_code == 200, f"Agent Badge QR returned {resp_badge.status_code}"
        assert resp_badge['Content-Type'] == 'image/png', "Content-Type is not image/png"
        assert 'attachment' in resp_badge['Content-Disposition'], "Content-Disposition not attachment"
        print(f"  [OK] Branded Business Card Endpoint: 200 OK ({len(resp_badge.content)} bytes)")
    else:
        print("  [!] No active agents found in database.")

    print("\n" + "=" * 60)
    print("ALL QR CODE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    verify_all_qr()
