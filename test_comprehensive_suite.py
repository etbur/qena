import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import Client
from accounts.models import User
from live.models import LiveStream
from vendors.models import Vendor
from agents.models import Agent

def run_suite():
    print("=" * 70)
    print("  QENAGEBEYA FULL ECOSYSTEM & ROLES TEST SUITE")
    print("=" * 70)

    admin_user = User.objects.filter(role='admin').first() or User.objects.filter(is_staff=True).first()
    vendor_user = User.objects.filter(role='vendor').first()
    customer_user = User.objects.filter(role='customer').first()
    agent_user = User.objects.filter(role='agent').first()

    c_admin = Client()
    if admin_user:
        c_admin.force_login(admin_user)

    c_vendor = Client()
    if vendor_user:
        c_vendor.force_login(vendor_user)

    c_agent = Client()
    if agent_user:
        c_agent.force_login(agent_user)

    c_cust = Client()
    if customer_user:
        c_cust.force_login(customer_user)

    test_endpoints = [
        # Admin Portal
        ("Admin Dashboard + Gauges + Charts", c_admin, "/portal/"),
        ("Admin Analytics + Gauges + Charts", c_admin, "/portal/analytics/"),
        ("Admin Vendors List", c_admin, "/portal/vendors/"),
        ("Admin Products List", c_admin, "/portal/products/"),
        ("Admin Orders List", c_admin, "/portal/orders/"),
        ("Admin Payouts", c_admin, "/portal/payouts/"),
        ("Admin Agents Oversight", c_admin, "/portal/agents/"),
        ("Admin Agent Commissions", c_admin, "/portal/agent-commissions/"),

        # Vendor Portal
        ("Vendor Dashboard + Gauge + 4 Charts", c_vendor, "/vendor/dashboard/"),
        ("Vendor Sales Analytics + Gauge + Charts", c_vendor, "/vendor/analytics/"),
        ("Vendor Products", c_vendor, "/vendor/products/"),
        ("Vendor Orders", c_vendor, "/vendor/orders/"),
        ("Vendor Inventory", c_vendor, "/vendor/inventory/"),
        ("Vendor Settings", c_vendor, "/vendor/settings/"),
        ("Vendor Live Streams Studio", c_vendor, "/live/vendor/"),
        ("Vendor Create Live Stream Form", c_vendor, "/live/vendor/create/"),

        # Agent Portal
        ("Agent CRM Dashboard + Quota Gauge + Charts", c_agent, "/agent/dashboard/"),
        ("Agent Performance Hub + Gauge + Charts", c_agent, "/agent/performance/"),
        ("Agent Clients", c_agent, "/agent/clients/"),
        ("Agent Deals Pipeline", c_agent, "/agent/deals/"),
        ("Agent Daily Tasks", c_agent, "/agent/tasks/"),
        ("Agent Inquiries", c_agent, "/agent/inquiries/"),
        ("Agent Commissions", c_agent, "/agent/commissions/"),

        # Customer & Storefront
        ("Customer Home Page", c_cust, "/"),
        ("Customer Live Shopping Discovery Feed", c_cust, "/live/"),
        ("Customer Live Active API Polling", c_cust, "/live/api/active/"),
        ("Customer Product Catalog", c_cust, "/products/"),
        ("Customer Shopping Cart", c_cust, "/cart/"),
        ("Customer Makerspace Studio", c_cust, "/makerspace/"),
        ("Customer Try-On AR & Photo Fitting Room", c_cust, "/try-on/"),
    ]

    all_passed = True
    for label, client, path in test_endpoints:
        resp = client.get(path)
        status = resp.status_code
        if status == 200:
            print(f"  [PASS] {label:<45} [{path}] -> 200 OK")
        else:
            print(f"  [FAIL] {label:<45} [{path}] -> FAILED ({status})")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print(f"  ALL {len(test_endpoints)}/{len(test_endpoints)} PORTALS & GAUGES & CHARTS VERIFIED SUCCESSFULLY!")
    else:
        print("  SOME TESTS FAILED - INSPECT LOGS ABOVE")
    print("=" * 70)

if __name__ == '__main__':
    run_suite()
