"""
Run with:  python seed_data.py
Creates sample categories, vendors, agents, products and orders so every
portal dashboard has realistic data on first launch.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from decimal import Decimal
from accounts.models import User
from vendors.models import Vendor
from agents.models import Agent, Client, Deal, Inquiry
from store.models import Category, Product
from orders.models import Order, OrderItem, Cart, CartItem
from admin_portal.models import AuditLog

print("Seeding …")

# ── Categories ────────────────────────────────────────────────────────────────
cat_data = [
    ("Electronics",      "fas fa-mobile-alt"),
    ("Fragrance & Oud",  "fas fa-crown"),
    ("Fashion",          "fas fa-tshirt"),
    ("Coffee & Pantry",  "fas fa-mug-hot"),
    ("Home & Majlis",    "fas fa-couch"),
    ("Beauty",           "fas fa-spa"),
    ("Sport",            "fas fa-shoe-prints"),
    ("Grocery",          "fas fa-apple-alt"),
    ("Toys & Baby",      "fas fa-baby"),
    ("Health",           "fas fa-heartbeat"),
]
categories = {}
for i, (name, icon) in enumerate(cat_data):
    from django.utils.text import slugify
    slug = slugify(name)
    cat, _ = Category.objects.get_or_create(
        slug=slug,
        defaults={"name": name, "icon": icon, "order": i, "is_active": True}
    )
    categories[name] = cat
print(f"  {len(categories)} categories")

# ── Vendor users ──────────────────────────────────────────────────────────────
vendor_users_data = [
    ("ahmed_store",   "Ahmed",   "Al Maktoum",  "ahmed@qena.ae"),
    ("fatima_shop",   "Fatima",  "Al Qasimi",   "fatima@qena.ae"),
    ("khalid_market", "Khalid",  "Al Suwaidi",  "khalid@qena.ae"),
    ("mariam_goods",  "Mariam",  "Al Hashimi",  "mariam@qena.ae"),
]
vendor_store_data = [
    ("Ahmed Tech Store",   "gold",     Decimal("9.50")),
    ("Fatima Fashion Hub", "platinum", Decimal("8.00")),
    ("Khalid Electronics", "silver",   Decimal("10.00")),
    ("Mariam Home Decor",  "bronze",   Decimal("12.00")),
]
vendors = []
for (uname, fn, ln, email), (sname, tier, comm) in zip(vendor_users_data, vendor_store_data):
    user, created = User.objects.get_or_create(
        username=uname,
        defaults={"first_name": fn, "last_name": ln, "email": email,
                  "role": "vendor", "is_active": True}
    )
    if created:
        user.set_password("vendor123")
        user.save()
    from django.utils.text import slugify
    vendor, _ = Vendor.objects.get_or_create(
        user=user,
        defaults={
            "store_name": sname,
            "slug": slugify(sname),
            "tier": tier,
            "status": Vendor.STATUS_APPROVED,
            "commission_rate": comm,
            "total_sales": Decimal("0"),
            "phone": "+251 911 234 567" if "Ahmed" in sname else ("+251 912 345 678" if "Fatima" in sname else ("+251 913 456 789" if "Khalid" in sname else "+251 914 567 890")),
            "email": f"{uname}@qenagebeya.com",
            "address": "Bole, Addis Ababa" if "Ahmed" in sname else ("Merkato, Addis Ababa" if "Fatima" in sname else ("Megenagna, Addis Ababa" if "Khalid" in sname else "Piazza, Addis Ababa")),
        }
    )
    vendors.append(vendor)
print(f"  {len(vendors)} vendors")

# ── Products ──────────────────────────────────────────────────────────────────
products_data = [
    (vendors[0], "Electronics",     "iPhone 16 Pro Max 256GB",      Decimal("4999"), Decimal("5499"), 24,  True,  True),
    (vendors[0], "Electronics",     "Sony WH-1000XM6 Headphones",   Decimal("1499"), Decimal("1799"), 18,  True,  False),
    (vendors[0], "Electronics",     "Samsung Galaxy S25 Ultra",      Decimal("3899"), Decimal("4299"), 12,  True,  True),
    (vendors[1], "Fashion",         "Embroidered Silk Sheila",       Decimal("350"),  Decimal("420"),  55,  True,  True),
    (vendors[1], "Fashion",         "Kandura Premium White",         Decimal("280"),  Decimal("320"),  40,  True,  False),
    (vendors[1], "Fragrance & Oud", "Tom Ford Tobacco Vanille",      Decimal("890"),  Decimal("990"),  15,  True,  True),
    (vendors[1], "Fragrance & Oud", "Oud Al Shuyukh",                Decimal("450"),  Decimal("550"),  22,  True,  False),
    (vendors[2], "Electronics",     "Tecno Spark 20 Pro",            Decimal("599"),  Decimal("699"),  30,  True,  False),
    (vendors[2], "Electronics",     "HP Pavilion Laptop 15",         Decimal("2799"), Decimal("3200"), 8,   False, False),
    (vendors[3], "Coffee & Pantry", "Premium Arabic Coffee Beans 1kg",Decimal("85"),  Decimal("110"),  100, True,  False),
    (vendors[3], "Home & Majlis",   "Habesha Handwoven Scarf",       Decimal("149"),  None,            60,  True,  False),
    (vendors[3], "Grocery",         "Medjool Dates 1kg Premium",     Decimal("65"),   Decimal("80"),   200, True,  True),
]
products = []
for v, cat_name, name, price, orig, stock, featured, flash in products_data:
    from django.utils.text import slugify
    slug = slugify(name)
    # make unique slug
    base_slug, n = slug, 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{n}"; n += 1
    p, created = Product.objects.get_or_create(
        name=name,
        vendor=v,
        defaults={
            "slug": slug,
            "category": categories.get(cat_name),
            "price": price,
            "original_price": orig,
            "stock": stock,
            "is_active": True,
            "is_featured": featured,
            "is_flash_deal": flash,
        }
    )
    products.append(p)
print(f"  {len(products)} products")

# ── Agent users ───────────────────────────────────────────────────────────────
agent_users_data = [
    ("omar_agent",   "Omar",   "Al Falasi",  "omar@qena.ae",  "senior"),
    ("noor_agent",   "Noor",   "Al Suwaidi", "noor@qena.ae",  "junior"),
    ("rashid_agent", "Rashid", "Al Mazroui", "rashid@qena.ae","lead"),
]
agents = []
for uname, fn, ln, email, tier in agent_users_data:
    user, created = User.objects.get_or_create(
        username=uname,
        defaults={"first_name": fn, "last_name": ln, "email": email,
                  "role": "agent", "is_active": True}
    )
    if created:
        user.set_password("agent123")
        user.save()
    agent, _ = Agent.objects.get_or_create(
        user=user,
        defaults={"tier": tier, "commission_rate": Decimal("5.00"), "is_active": True}
    )
    agents.append(agent)
print(f"  {len(agents)} agents")

# ── Clients ───────────────────────────────────────────────────────────────────
clients_data = [
    (agents[0], "Mohammed Al Rashid", "mohammed@example.ae", "+971 50 111 2233", "gold"),
    (agents[0], "Layla Al Qasimi",    "layla@example.ae",    "+971 55 444 5566", "platinum"),
    (agents[1], "Hassan Al Blooshi",  "hassan@example.ae",   "+971 50 777 8899", "standard"),
    (agents[1], "Sara Al Mansoori",   "sara@example.ae",     "+971 55 222 3344", "silver"),
    (agents[2], "Tariq Al Ameri",     "tariq@example.ae",    "+971 50 999 0011", "gold"),
]
clients = []
for agent, name, email, phone, tier in clients_data:
    c, _ = Client.objects.get_or_create(
        full_name=name,
        agent=agent,
        defaults={"email": email, "phone": phone, "tier": tier}
    )
    clients.append(c)
print(f"  {len(clients)} clients")

# ── Deals ─────────────────────────────────────────────────────────────────────
deals_data = [
    (agents[0], clients[0], "iPhone 16 Bulk Purchase",     Decimal("14997"), Deal.STATUS_CLOSED),
    (agents[0], clients[1], "Fragrance Bundle Deal",        Decimal("8900"),  Deal.STATUS_CLOSED),
    (agents[0], clients[0], "Sony Headphones × 5",         Decimal("7495"),  Deal.STATUS_NEGOTIATING),
    (agents[1], clients[2], "Coffee Subscription 12mo",    Decimal("1020"),  Deal.STATUS_CLOSED),
    (agents[1], clients[3], "Home Decor Package",          Decimal("3500"),  Deal.STATUS_NEW),
    (agents[2], clients[4], "Corporate Electronics Order", Decimal("25000"), Deal.STATUS_CLOSED),
]
for agent, client, title, value, status in deals_data:
    Deal.objects.get_or_create(
        agent=agent, client=client, title=title,
        defaults={"value": value, "status": status}
    )
print(f"  {len(deals_data)} deals")

# ── Inquiries ─────────────────────────────────────────────────────────────────
inquiries_data = [
    (agents[0], clients[0], "Bulk iPhone pricing",     "Need pricing for 10+ iPhones",        Inquiry.STATUS_IN_PROGRESS),
    (agents[0], clients[1], "Fragrance gift sets",     "Looking for Ramadan gift set options", Inquiry.STATUS_PENDING),
    (agents[1], clients[2], "Coffee subscription",     "Monthly coffee delivery inquiry",      Inquiry.STATUS_COMPLETED),
    (agents[2], clients[4], "Corporate laptop quote",  "Need 20 laptops for office",           Inquiry.STATUS_PENDING),
]
for agent, client, subject, msg, status in inquiries_data:
    Inquiry.objects.get_or_create(
        agent=agent, subject=subject,
        defaults={"client": client, "message": msg, "status": status}
    )
print(f"  {len(inquiries_data)} inquiries")

# ── Customer users ────────────────────────────────────────────────────────────
customer_data = [
    ("customer1", "Amina",    "Al Zaabi",    "amina@example.ae"),
    ("customer2", "Yusuf",    "Al Nuaimi",   "yusuf@example.ae"),
    ("customer3", "Khadija",  "Al Ketbi",    "khadija@example.ae"),
]
customers = []
for uname, fn, ln, email in customer_data:
    user, created = User.objects.get_or_create(
        username=uname,
        defaults={"first_name": fn, "last_name": ln, "email": email,
                  "role": "customer", "is_active": True,
                  "address": "Flat 4, Marina Tower, Dubai", "city": "Dubai", "country": "UAE"}
    )
    if created:
        user.set_password("customer123")
        user.save()
    customers.append(user)
print(f"  {len(customers)} customers")

# ── Orders ────────────────────────────────────────────────────────────────────
import uuid

orders_data = [
    (customers[0], products[0],  1, Order.STATUS_DELIVERED),
    (customers[0], products[3],  2, Order.STATUS_SHIPPED),
    (customers[1], products[5],  1, Order.STATUS_DELIVERED),
    (customers[1], products[9],  3, Order.STATUS_PROCESSING),
    (customers[2], products[1],  1, Order.STATUS_DELIVERED),
    (customers[2], products[11], 2, Order.STATUS_PENDING),
]
for user, product, qty, status in orders_data:
    subtotal     = product.price * qty
    shipping_fee = Decimal("0") if subtotal >= 99 else Decimal("15")
    total        = subtotal + shipping_fee
    order        = Order.objects.create(
        user             = user,
        status           = status,
        payment_method   = Order.PAYMENT_COD,
        payment_status   = (status == Order.STATUS_DELIVERED),
        shipping_name    = user.get_full_name(),
        shipping_phone   = "+971 50 000 0000",
        shipping_address = "123 Marina Walk, Dubai",
        shipping_city    = "Dubai",
        shipping_country = "UAE",
        subtotal         = subtotal,
        shipping_fee     = shipping_fee,
        total            = total,
    )
    commission = product.vendor.commission_rate / 100 * product.price
    OrderItem.objects.create(
        order            = order,
        product          = product,
        product_name     = product.name,
        product_price    = product.price,
        quantity         = qty,
        vendor_commission= commission * qty,
    )
    # Update vendor totals
    product.vendor.total_sales += total
    product.vendor.save()
print(f"  {len(orders_data)} orders")

# ── Audit logs ────────────────────────────────────────────────────────────────
admin_user = User.objects.filter(username='admin').first()
if admin_user:
    logs = [
        (AuditLog.ACTION_APPROVE, "Approved vendor: Ahmed Tech Store"),
        (AuditLog.ACTION_APPROVE, "Approved vendor: Fatima Fashion Hub"),
        (AuditLog.ACTION_LOGIN,   "Admin logged in"),
        (AuditLog.ACTION_UPDATE,  "Updated platform settings"),
        (AuditLog.ACTION_APPROVE, "Approved vendor: Khalid Electronics"),
    ]
    for action, desc in logs:
        AuditLog.objects.create(actor=admin_user, action=action,
                                description=desc, ip_address="127.0.0.1")
    print(f"  {len(logs)} audit log entries")

print("\n[OK] Seed complete!")
print("\nLogin credentials:")
print("  Admin    -> admin       / admin123")
print("  Vendors  -> ahmed_store / vendor123  (and fatima_shop, khalid_market, mariam_goods)")
print("  Agents   -> omar_agent  / agent123   (and noor_agent, rashid_agent)")
print("  Customers-> customer1   / customer123 (and customer2, customer3)")
print("\nRun:  python manage.py runserver")
print("URLs:")
print("  Store  -> http://127.0.0.1:8000/")
print("  Admin  -> http://127.0.0.1:8000/portal/")
print("  Vendor -> http://127.0.0.1:8000/vendor/dashboard/")
print("  Agent  -> http://127.0.0.1:8000/agent/dashboard/")
print("  Django -> http://127.0.0.1:8000/admin/")
