import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import Client
from store.models import Product
from vendors.models import Vendor
from agents.models import Agent

client = Client()

print("=" * 70)
print("TESTING MOBILE RESPONSIVENESS AND VIEWS")
print("=" * 70)

# 1. Test Agent Card View
agent = Agent.objects.first()
resp = client.get(f'/agent/card/{agent.pk}/')
assert resp.status_code == 200, f"Agent card failed with status {resp.status_code}"
assert "viewport" in resp.content.decode('utf-8')
assert "quick-connect-grid" in resp.content.decode('utf-8')
assert "Official Agent QR Code" in resp.content.decode('utf-8')
print(" [PASS] /agent/card/<pk>/ rendered responsive markup successfully.")

# 2. Test Product Detail View
product = Product.objects.first()
resp = client.get(product.get_absolute_url())
assert resp.status_code == 200, f"Product detail failed with status {resp.status_code}"
assert "productQRModal" in resp.content.decode('utf-8')
assert "max-width:768px" in resp.content.decode('utf-8')
print(" [PASS] /products/<slug>/ rendered responsive layout & QR modal successfully.")

# 3. Test Vendor Store View
vendor = Vendor.objects.first()
resp = client.get(f'/vendor/store/{vendor.slug}/')
assert resp.status_code == 200, f"Vendor store failed with status {resp.status_code}"
assert "vendorStoreQRModal" in resp.content.decode('utf-8')
print(" [PASS] /vendor/store/<slug>/ rendered responsive banner & QR modal successfully.")

# 5. Test Category and Product List Filter View
resp = client.get('/products/?category=electronics')
assert resp.status_code == 200, f"Category filter failed with status {resp.status_code}"
assert "mobile-cat-strip" in resp.content.decode('utf-8')
assert "product-grid" in resp.content.decode('utf-8')
print(" [PASS] /products/?category=electronics rendered mobile category pills & products.")

resp = client.get('/category/electronics/')
assert resp.status_code == 200, f"Category view failed with status {resp.status_code}"
assert "product-grid" in resp.content.decode('utf-8')
print(" [PASS] /category/electronics/ rendered category header & products.")

print("=" * 70)
print("ALL MOBILE RESPONSIVENESS TESTS PASSED 100%!")
print("=" * 70)
