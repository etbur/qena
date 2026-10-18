"""
test_custom_domain_live.py — Comprehensive Test Suite for Vendor Custom Domain (alex.com)
& 10,000 ETB / Year Standalone Storefront Admin Approval by Funds Transfer (FT).
"""
import os
import sys
from datetime import timedelta
import django

# Set UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from vendors.models import Vendor
from store.models import Product, Category
from orders.models import Cart, CartItem

User = get_user_model()

def setup_test_data():
    print("\n" + "="*75)
    print(" [*] SETTING UP TEST VENDOR: ALEX (alex.com & 10,000 ETB FT Subscription)")
    print("="*75)

    # 1. Create Admin User
    admin_user, _ = User.objects.get_or_create(
        username='superadmin',
        defaults={
            'email': 'admin@qenagebeya.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': User.ROLE_ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin_user.role = User.ROLE_ADMIN
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password('AdminPass123!')
    admin_user.save()

    # 2. Create Alex Vendor User
    user, _ = User.objects.get_or_create(
        username='alex',
        defaults={
            'email': 'alex@alextech.et',
            'first_name': 'Alex',
            'last_name': 'Tech',
            'role': User.ROLE_VENDOR,
            'phone': '+251911223344',
            'address': 'Bole Sub-City, Road 4',
            'city': 'Addis Ababa',
            'country': 'Ethiopia',
        }
    )
    user.set_password('AlexPass123!')
    user.role = User.ROLE_VENDOR
    user.save()

    # 3. Create Category
    cat_electronics, _ = Category.objects.get_or_create(
        slug='electronics',
        defaults={'name': 'Electronics', 'description': 'Smart devices & gadgets'}
    )

    # 4. Create or update Alex's Vendor Profile
    vendor, _ = Vendor.objects.get_or_create(
        user=user,
        defaults={'store_name': 'Alex Electronics'}
    )
    vendor.store_name = 'Alex Electronics'
    vendor.slug = 'alex'
    vendor.subdomain = 'alex'
    vendor.custom_domain = 'alex.com'
    vendor.store_tagline = "Ethiopia's Leading Hub for Smart Electronics & Gadgets"
    vendor.description = "Welcome to Alex Electronics! Premium smartphones, smart accessories, and audio gear directly imported with full local warranty."
    vendor.brand_primary = '#1e3a8a'
    vendor.brand_secondary = '#f59e0b'
    vendor.brand_font = 'Inter'
    vendor.phone = '+251911223344'
    vendor.email = 'sales@alextech.et'
    vendor.whatsapp = '251911223344'
    vendor.telegram = 'alexelectronics'
    vendor.address = 'Bole Medhanealem Mall, 3rd Floor'
    vendor.city = 'Addis Ababa'
    vendor.country = 'Ethiopia'
    vendor.status = Vendor.STATUS_APPROVED
    vendor.storefront_enabled = True
    # Start as inactive / pending to test subscription gate
    vendor.storefront_status = Vendor.STOREFRONT_STATUS_INACTIVE
    vendor.storefront_annual_fee = 10000.00
    vendor.storefront_approved_at = None
    vendor.storefront_expires_at = None
    vendor.storefront_payment_ref = ''
    vendor.save()

    # 5. Create Alex's distinct products
    p1, _ = Product.objects.get_or_create(
        vendor=vendor,
        name='Alex 5G Pro Smartphone (256GB)',
        defaults={
            'slug': 'alex-5g-pro-smartphone-256gb',
            'category': cat_electronics,
            'description': 'Flagship 5G smartphone with 120Hz AMOLED display, 108MP camera, and 5000mAh battery.',
            'price': 34500.00,
            'original_price': 38000.00,
            'stock': 15,
            'is_active': True,
            'is_featured': True,
            'is_flash_deal': True,
        }
    )
    p1.price = 34500.00
    p1.stock = 15
    p1.is_active = True
    p1.save()

    p2, _ = Product.objects.get_or_create(
        vendor=vendor,
        name='Alex Ultra ANC Wireless Earbuds',
        defaults={
            'slug': 'alex-ultra-anc-wireless-earbuds',
            'category': cat_electronics,
            'description': 'Active Noise Cancelling true wireless earbuds with 40-hour battery and spatial audio.',
            'price': 4200.00,
            'original_price': 4900.00,
            'stock': 30,
            'is_active': True,
            'is_featured': True,
        }
    )
    p2.price = 4200.00
    p2.stock = 30
    p2.is_active = True
    p2.save()

    print(f"[OK] Vendor setup: '{vendor.store_name}'")
    print(f"   - Custom Domain: {vendor.custom_domain}")
    print(f"   - Subdomain: {vendor.subdomain}")
    print(f"   - Initial Storefront Status: {vendor.storefront_status} (is_active={vendor.is_storefront_active})")
    print(f"   - Annual Fee: {vendor.storefront_annual_fee} ETB / Year")
    print(f"   - Products: {vendor.products.count()} items")
    return admin_user, user, vendor, p1, p2


def run_tests():
    admin_user, vendor_user, vendor, p1, p2 = setup_test_data()
    client = Client()
    passed = 0
    failed = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            if details:
                print(f"         {details}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            if details:
                print(f"         {details}")
            failed += 1

    print("\n" + "="*75)
    print(" TEST SUITE 1: STANDALONE DOMAIN APPROVAL GATE (UNPAID / PENDING)")
    print("="*75)

    # 1.1 Visiting alex.com when inactive shows pending approval template
    res = client.get('/', HTTP_HOST='alex.com')
    html = res.content.decode('utf-8')
    assert_test(
        "Unapproved 'alex.com' renders Pending Approval template (200 OK)",
        res.status_code == 200 and 'Standalone' in html and 'Alex Electronics' in html,
        f"Status: {res.status_code}, Template contains branding and pending notice"
    )
    assert_test(
        "Pending approval page includes link to central marketplace store",
        f'/vendor/store/{vendor.slug}/' in html,
        f"Contains marketplace store link"
    )

    # 1.2 Central marketplace store page is ALREADY active (Dual Access Principle)
    res = client.get(f'/vendor/store/{vendor.slug}/', HTTP_HOST='qenagebeya.com')
    html = res.content.decode('utf-8')
    assert_test(
        "Marketplace store page (/vendor/store/alex/) is fully accessible while standalone is pending",
        res.status_code == 200 and 'Alex Electronics' in html and 'Alex 5G Pro' in html,
        f"Central marketplace store loads seamlessly"
    )


    print("\n" + "="*75)
    print(" TEST SUITE 2: VENDOR SUBMITS 10,000 ETB FUNDS TRANSFER (FT) PAYMENT")
    print("="*75)

    from django.urls import reverse

    # 2.1 Login as vendor Alex
    client.force_login(vendor_user)

    # 2.2 Submit FT payment reference for 10,000 ETB
    post_data = {
        'action': 'submit_ft_payment',
        'storefront_payment_method': 'cbe_ft',
        'storefront_payment_ref': 'FT-2026-ALEX-10000-CBE',
        'storefront_payment_note': 'Transferred 10,000 ETB from Alex CBE Acc #100088992211',
    }
    url_sf_settings = reverse('vendors:storefront_settings')
    res = client.post(url_sf_settings, post_data, HTTP_HOST='localhost', follow=True)
    vendor.refresh_from_db()

    assert_test(
        "Vendor successfully submits 10,000 ETB FT payment reference",
        res.status_code == 200 and vendor.storefront_status == Vendor.STOREFRONT_STATUS_PENDING,
        f"Status updated to: {vendor.storefront_status}, Ref: {vendor.storefront_payment_ref}"
    )
    assert_test(
        "Vendor storefront settings page shows 'Pending Admin Approval' badge",
        'Pending' in res.content.decode('utf-8') and 'FT-2026-ALEX-10000-CBE' in res.content.decode('utf-8'),
        f"Pending banner displayed on vendor dashboard"
    )

    # 2.3 Visiting alex.com now shows Pending Approval with FT Reference
    client.logout()
    res = client.get('/', HTTP_HOST='alex.com')
    html = res.content.decode('utf-8')
    assert_test(
        "alex.com displays 'Pending Admin Approval (10,000 ETB / Year FT)' with submitted FT Ref",
        '10,000 ETB' in html and 'FT-2026-ALEX-10000-CBE' in html,
        f"Shows customer and admin clear payment verification state"
    )


    print("\n" + "="*75)
    print(" TEST SUITE 3: ADMIN APPROVAL WORKFLOW (10,000 ETB FT VERIFICATION)")
    print("="*75)

    # 3.1 Login as Admin
    client.force_login(admin_user)

    # 3.2 View admin vendors list with storefront filter
    url_admin_vendors = reverse('admin_portal:vendors')
    res = client.get(f"{url_admin_vendors}?sf_status=pending_approval", HTTP_HOST='localhost')
    html = res.content.decode('utf-8')
    assert_test(
        "Admin Portal lists vendor Alex under 'Pending 10,000 ETB FT Approval'",
        res.status_code == 200 and 'Alex Electronics' in html and 'FT-2026-ALEX-10000-CBE' in html,
        f"Admin sees FT Ref and 1-Yr Approval action button"
    )

    # 3.3 Admin clicks 'Approve 1-Yr Storefront (10,000 ETB FT)'
    url_approve = reverse('admin_portal:vendor_storefront_approve', kwargs={'pk': vendor.pk})
    res = client.post(url_approve, HTTP_HOST='localhost', follow=True)
    vendor.refresh_from_db()

    assert_test(
        "Admin approves 1-Year Storefront subscription",
        res.status_code == 200 and vendor.storefront_status == Vendor.STOREFRONT_STATUS_ACTIVE,
        f"Vendor storefront_status is now '{vendor.storefront_status}'"
    )
    assert_test(
        "Vendor is_storefront_active is True and expiry is set to 365 days (~1 year)",
        vendor.is_storefront_active and vendor.storefront_expires_at is not None and vendor.storefront_days_left >= 364,
        f"Expires on: {vendor.storefront_expires_at}, Days left: {vendor.storefront_days_left}"
    )


    print("\n" + "="*75)
    print(" TEST SUITE 4: STANDALONE STOREFRONT UNLOCKED (alex.com & alex.localhost)")
    print("="*75)
    client.logout()

    # 4.1 Root home page on alex.com
    res = client.get('/', HTTP_HOST='alex.com')
    html = res.content.decode('utf-8')
    assert_test(
        "alex.com unlocks full White-Label Storefront (200 OK)",
        res.status_code == 200 and 'Alex Electronics' in html and 'Alex 5G Pro Smartphone' in html,
        f"Full standalone storefront rendered with Alex's products"
    )
    assert_test(
        "Storefront applies Alex's custom brand colors (#1e3a8a, #f59e0b)",
        '#1e3a8a' in html and '#f59e0b' in html,
        f"Branding tokens injected"
    )

    # 4.2 WWW custom domain alias
    res = client.get('/', HTTP_HOST='www.alex.com')
    assert_test(
        "www.alex.com routes to Alex's Storefront",
        res.status_code == 200 and 'Alex Electronics' in res.content.decode('utf-8'),
        f"WWW alias matched"
    )

    # 4.3 Subdomain routing (alex.localhost:8000)
    res = client.get('/', HTTP_HOST='alex.localhost:8000')
    assert_test(
        "alex.localhost:8000 routes to Alex's Storefront",
        res.status_code == 200 and 'Alex Electronics' in res.content.decode('utf-8'),
        f"Local development subdomain matched"
    )

    # 4.4 Product Detail Page (/product/<pk>/)
    res = client.get(f'/product/{p1.pk}/', HTTP_HOST='alex.com')
    html = res.content.decode('utf-8')
    assert_test(
        f"Product detail (/product/{p1.pk}/) on alex.com loads with WhatsApp order",
        res.status_code == 200 and 'Alex 5G Pro Smartphone' in html and 'wa.me/251911223344' in html,
        f"Product specs and WhatsApp ordering ready"
    )

    # 4.5 About & Contact Pages
    res_about = client.get('/about/', HTTP_HOST='alex.com')
    res_contact = client.get('/contact/', HTTP_HOST='alex.com')
    assert_test(
        "Storefront /about/ and /contact/ pages render cleanly",
        res_about.status_code == 200 and res_contact.status_code == 200,
        f"About status: {res_about.status_code}, Contact status: {res_contact.status_code}"
    )

    # 4.6 Contact form submission on alex.com
    res = client.post('/contact/', {'name': 'Abebe', 'contact': 'abebe@ethio.et', 'message': 'Bulk order inquiry'}, HTTP_HOST='alex.com', follow=True)
    assert_test(
        "Storefront contact form processes customer inquiry",
        res.status_code == 200 and ('Thank you' in res.content.decode('utf-8') or 'sent' in res.content.decode('utf-8')),
        f"Customer feedback handled"
    )

    # 4.7 Storefront Cart Addition (/cart/add/<pk>/)
    res = client.get(f'/cart/add/{p1.pk}/', HTTP_HOST='alex.com', follow=True)
    html = res.content.decode('utf-8')
    assert_test(
        "Add to Cart on alex.com renders branded standalone cart",
        res.status_code == 200 and 'Alex 5G Pro Smartphone' in html and '34500' in html,
        f"Item added to session cart on alex.com"
    )


    print("\n" + "="*75)
    print(" TEST SUITE 5: DUAL ACCESS & REAL-TIME SHARED DATABASE SYNC")
    print("="*75)

    # 5.1 Update price and stock in central database
    p1.price = 31999.00
    p1.stock = 9
    p1.save()

    res_m = client.get(f'/products/{p1.slug}/', HTTP_HOST='qenagebeya.com')
    res_s = client.get(f'/product/{p1.pk}/', HTTP_HOST='alex.com')

    html_m = res_m.content.decode('utf-8')
    html_s = res_s.content.decode('utf-8')

    assert_test(
        "Price update (31,999 ETB) reflects instantly on marketplace (qenagebeya.com)",
        '31999' in html_m or '31,999' in html_m,
        f"Marketplace displays updated price"
    )
    assert_test(
        "Price update (31,999 ETB) reflects instantly on standalone domain (alex.com)",
        '31999' in html_s or '31,999' in html_s,
        f"Standalone domain displays updated price"
    )
    assert_test(
        "Marketplace store page displays verified alex.com badge",
        'alex.com' in client.get(f'/vendor/store/{vendor.slug}/', HTTP_HOST='qenagebeya.com').content.decode('utf-8'),
        f"Cross-link badge verified on main marketplace"
    )

    print("\n" + "="*75)
    print(f" TEST SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {passed+failed})")
    print("="*75)

    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
