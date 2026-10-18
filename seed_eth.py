"""
Ethiopian seed data — updates existing products to ETB prices
and adds more Ethiopian-specific products/categories.
Run: python seed_eth.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from decimal import Decimal
from django.utils.text import slugify
from store.models import Category, Product
from vendors.models import Vendor
from accounts.models import User

print("Updating to Ethiopian context...")

# ── Update existing categories with Ethiopian context ─────────────────────
eth_categories = [
    ("Electronics",          "fas fa-mobile-alt",    0),
    ("Fragrance & Oud",      "fas fa-crown",         1),
    ("Fashion & Habesha",    "fas fa-tshirt",        2),
    ("Coffee & Pantry",      "fas fa-mug-hot",       3),
    ("Home & Decoration",    "fas fa-couch",         4),
    ("Beauty & Skin",        "fas fa-spa",           5),
    ("Sport & Fitness",      "fas fa-shoe-prints",   6),
    ("Fresh Grocery",        "fas fa-apple-alt",     7),
    ("Toys & Baby",          "fas fa-baby",          8),
    ("Health & Wellness",    "fas fa-heartbeat",     9),
    ("Ethiopian Crafts",     "fas fa-palette",      10),
    ("Spices & Herbs",       "fas fa-seedling",     11),
    ("Rent",                 "fas fa-key",          12),
    ("Maintenance Service",  "fas fa-wrench",       13),
    ("Digital Sales",        "fas fa-laptop-code",  14),
    ("Job",                  "fas fa-briefcase",    15),
]
for name, icon, order in eth_categories:
    slug = slugify(name)
    Category.objects.update_or_create(
        slug=slug,
        defaults={"name": name, "icon": icon, "order": order, "is_active": True}
    )
print(f"  {len(eth_categories)} categories updated")

# ── Update product prices to ETB equivalents ─────────────────────────────
# 1 USD ≈ 57 ETB (approximate)
etb_updates = {
    "iPhone 16 Pro Max 256GB":     (Decimal("289000"), Decimal("315000")),
    "Sony WH-1000XM6 Headphones":  (Decimal("86000"),  Decimal("103000")),
    "Samsung Galaxy S25 Ultra":     (Decimal("225000"), Decimal("248000")),
    "Embroidered Silk Sheila":      (Decimal("2800"),   Decimal("3200")),
    "Kandura Premium White":        (Decimal("2200"),   Decimal("2600")),
    "Tom Ford Tobacco Vanille":     (Decimal("51000"),  Decimal("57000")),
    "Oud Al Shuyukh":               (Decimal("25000"),  Decimal("31500")),
    "Tecno Spark 20 Pro":           (Decimal("34500"),  Decimal("40000")),
    "HP Pavilion Laptop 15":        (Decimal("161000"), Decimal("184000")),
    "Premium Arabic Coffee Beans 1kg": (Decimal("1200"), Decimal("1600")),
    "Habesha Handwoven Scarf":      (Decimal("2200"),   None),
    "Medjool Dates 1kg Premium":    (Decimal("950"),    Decimal("1200")),
}
updated = 0
for name, (price, orig) in etb_updates.items():
    count = Product.objects.filter(name=name).update(
        price=price, original_price=orig
    )
    updated += count
print(f"  {updated} product prices updated to ETB")

# ── Add Ethiopian-specific products ──────────────────────────────────────
vendor = Vendor.objects.filter(status=Vendor.STATUS_APPROVED).first()
if vendor:
    eth_products = [
        ("Habesha Kemis — White & Gold",    "Fashion & Habesha",  Decimal("4500"),  Decimal("5500"),  30, True,  False),
        ("Ethiopian Coffee Jebena Set",      "Coffee & Pantry",    Decimal("850"),   Decimal("1100"),  50, True,  True),
        ("Yirgacheffe Coffee 500g",          "Coffee & Pantry",    Decimal("750"),   Decimal("950"),   80, True,  True),
        ("Berbere Spice Mix 250g",           "Spices & Herbs",     Decimal("180"),   Decimal("250"),  120, True,  False),
        ("Mitmita Hot Spice 200g",           "Spices & Herbs",     Decimal("150"),   Decimal("200"),  100, True,  False),
        ("Traditional Gabi Blanket",         "Ethiopian Crafts",   Decimal("2800"),  Decimal("3200"),  25, True,  False),
        ("Kitfo Seasoning Bundle",           "Spices & Herbs",     Decimal("350"),   Decimal("500"),   60, True,  True),
        ("Injera Flour (Teff) 2kg",          "Fresh Grocery",      Decimal("280"),   Decimal("360"),  200, True,  False),
        ("Ethiopian Honey (Tej) 1kg",        "Coffee & Pantry",    Decimal("480"),   Decimal("600"),   45, False, False),
        ("Handwoven Basket (Mesob)",         "Ethiopian Crafts",   Decimal("1200"),  Decimal("1500"),  35, True,  False),
        ("Eritrean Incense (Etan)",          "Fragrance & Oud",    Decimal("320"),   Decimal("450"),   70, True,  True),
        ("Netch Gomen (Garlic Spice)",       "Spices & Herbs",     Decimal("120"),   None,            150, True,  False),
        ("Bole 3-Bedroom Villa for Rent",    "Rent",               Decimal("45000"), Decimal("50000"),  1, True,  False),
        ("Toyota Corolla Daily Rent",        "Rent",               Decimal("2500"),  Decimal("3000"),   5, True,  True),
        ("AC & Ventilation Maintenance",     "Maintenance Service",Decimal("1200"),  Decimal("1500"),  30, True,  False),
        ("Emergency Plumbing Service",       "Maintenance Service",Decimal("600"),   Decimal("800"),   50, True,  False),
        ("Antivirus 1-Year Digital License", "Digital Sales",      Decimal("1400"),  Decimal("2000"), 100, True,  False),
        ("Amharic Dictionary License Key",   "Digital Sales",      Decimal("450"),   Decimal("600"),  200, True,  True),
        ("Delivery Driver Position (Bole)",  "Job",                Decimal("0"),     None,              1, True,  False),
        ("Python Developer Job Vacancy",     "Job",                Decimal("0"),     None,              1, True,  False),
    ]
    added = 0
    for name, cat_name, price, orig, stock, featured, flash in eth_products:
        cat = Category.objects.filter(slug=slugify(cat_name)).first()
        slug = slugify(name)
        base, n = slug, 1
        while Product.objects.filter(slug=slug).exclude(name=name).exists():
            slug = f"{base}-{n}"; n += 1
        _, created = Product.objects.get_or_create(
            name=name, vendor=vendor,
            defaults={
                "slug": slug, "category": cat,
                "price": price, "original_price": orig,
                "stock": stock, "is_active": True,
                "is_featured": featured, "is_flash_deal": flash,
            }
        )
        if created: added += 1
    print(f"  {added} Ethiopian products added")

# ── Update customer addresses to Ethiopian cities ─────────────────────────
eth_addresses = [
    ("customer1", "Bole Sub-city, Addis Ababa",         "Addis Ababa",  "Ethiopia"),
    ("customer2", "Kirkos, Arat Kilo, Addis Ababa",     "Addis Ababa",  "Ethiopia"),
    ("customer3", "Hawassa City Center, SNNPR",          "Hawassa",      "Ethiopia"),
]
for uname, addr, city, country in eth_addresses:
    User.objects.filter(username=uname).update(
        address=addr, city=city, country=country
    )
print(f"  Customer addresses updated to Ethiopian cities")

# ── Update orders shipping to ETB & Ethiopia ─────────────────────────────
from orders.models import Order
Order.objects.all().update(shipping_country="Ethiopia")
Order.objects.filter(shipping_city="Dubai").update(shipping_city="Addis Ababa")
Order.objects.filter(shipping_address__contains="Marina").update(
    shipping_address="Bole Road, Addis Ababa"
)
print("  Orders updated to Ethiopian addresses")

print("\n[SUCCESS] Ethiopian seed complete!")
print("Currency: ETB (Ethiopian Birr)")
print("Timezone: Africa/Addis_Ababa")
print("Languages: English / Amharic / Afaan Oromoo")
