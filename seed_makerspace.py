"""
Seed makerspace profiles and a sample order for demo purposes.
Run: python seed_makerspace.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from decimal import Decimal
from vendors.models import Vendor
from accounts.models import User
from makerspace.models import MakerspaceProfile, MakerspaceOrder, MakerspaceStatusLog

print("Seeding makerspace data...")

# ── Create makerspace profiles for approved vendors ───────────────────────────
vendors = Vendor.objects.filter(status=Vendor.STATUS_APPROVED)
profiles_created = 0
for i, vendor in enumerate(vendors):
    profile, created = MakerspaceProfile.objects.get_or_create(
        vendor=vendor,
        defaults={
            'is_active': i < 2,   # first 2 vendors active
            'description': f'{vendor.store_name} Makerspace — 3D printing, laser cutting and CNC machining services in Addis Ababa.',
            'price_pla_per_gram':   Decimal('2.50'),
            'price_petg_per_gram':  Decimal('3.20'),
            'price_abs_per_gram':   Decimal('3.50'),
            'price_resin_per_gram': Decimal('6.00'),
            'price_laser_per_cm2':  Decimal('0.90'),
            'price_cnc_per_cm2':    Decimal('1.50'),
            'price_design_service': Decimal('200.00'),
            'min_lead_time_days':   2,
            'max_lead_time_days':   5,
        }
    )
    if created:
        profiles_created += 1
        print(f'  Created makerspace profile for: {vendor.store_name}')

print(f'  {profiles_created} new profiles created ({MakerspaceProfile.objects.count()} total)')

# ── Create sample makerspace orders ──────────────────────────────────────────
customers = list(User.objects.filter(role='customer')[:3])
active_profile = MakerspaceProfile.objects.filter(is_active=True).first()

if active_profile and customers:
    sample_orders = [
        {
            'customer': customers[0],
            'vendor': active_profile.vendor,
            'service_type': MakerspaceOrder.SERVICE_3D_PRINT,
            'material': MakerspaceOrder.MATERIAL_PLA,
            'infill': 30,
            'quantity': 2,
            'color': 'White',
            'notes': 'Please print slowly for better quality.',
            'estimated_volume_cm3': Decimal('42.5000'),
            'estimated_grams': Decimal('15.80'),
            'system_price': Decimal('79.00'),
            'final_price': Decimal('79.00'),
            'status': MakerspaceOrder.STATUS_QUOTE_PENDING,
            'file_type': 'stl',
        },
        {
            'customer': customers[1] if len(customers) > 1 else customers[0],
            'vendor': active_profile.vendor,
            'service_type': MakerspaceOrder.SERVICE_LASER,
            'material': 'laser_wood',
            'infill': 100,
            'quantity': 1,
            'color': '',
            'notes': 'Cut logo design for wooden sign.',
            'estimated_volume_cm3': Decimal('0.0000'),
            'estimated_grams': Decimal('0.00'),
            'estimated_area_cm2': Decimal('320.0000'),
            'system_price': Decimal('288.00'),
            'final_price': Decimal('288.00'),
            'status': MakerspaceOrder.STATUS_QUOTED,
            'vendor_price': Decimal('270.00'),
            'vendor_note': 'Wood cutting available. Price adjusted for material thickness.',
            'file_type': 'dxf',
        },
        {
            'customer': customers[2] if len(customers) > 2 else customers[0],
            'vendor': active_profile.vendor,
            'service_type': MakerspaceOrder.SERVICE_3D_PRINT,
            'material': MakerspaceOrder.MATERIAL_RESIN,
            'infill': 100,
            'quantity': 1,
            'color': 'Clear',
            'notes': '',
            'estimated_volume_cm3': Decimal('8.2000'),
            'estimated_grams': Decimal('9.02'),
            'system_price': Decimal('54.12'),
            'final_price': Decimal('60.00'),
            'status': MakerspaceOrder.STATUS_IN_PRODUCTION,
            'vendor_price': Decimal('60.00'),
            'vendor_note': 'In production — expected ready in 2 days.',
            'file_type': 'stl',
        },
    ]

    created_count = 0
    for data in sample_orders:
        if not MakerspaceOrder.objects.filter(
            customer=data['customer'],
            service_type=data['service_type'],
            status=data['status']
        ).exists():
            # Create a dummy file placeholder
            import uuid, os
            from django.conf import settings
            dummy_dir = os.path.join(str(settings.MEDIA_ROOT), 'makerspace', 'uploads')
            os.makedirs(dummy_dir, exist_ok=True)
            dummy_fname = f'sample_{uuid.uuid4().hex[:8]}.{data["file_type"]}'
            dummy_path  = os.path.join(dummy_dir, dummy_fname)
            with open(dummy_path, 'wb') as f:
                # Write minimal valid content
                if data['file_type'] == 'stl':
                    # Binary STL header with 0 triangles
                    f.write(b'\x00' * 80 + b'\x00\x00\x00\x00')
                elif data['file_type'] == 'dxf':
                    f.write(b'0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n')
                else:
                    f.write(b'sample file')

            order = MakerspaceOrder(
                customer=data['customer'],
                vendor=data['vendor'],
                service_type=data['service_type'],
                material=data['material'],
                infill=data['infill'],
                quantity=data['quantity'],
                color=data.get('color', ''),
                notes=data.get('notes', ''),
                estimated_volume_cm3=data.get('estimated_volume_cm3', 0),
                estimated_grams=data.get('estimated_grams', 0),
                estimated_area_cm2=data.get('estimated_area_cm2', Decimal('0')),
                system_price=data['system_price'],
                vendor_price=data.get('vendor_price'),
                final_price=data['final_price'],
                status=data['status'],
                vendor_note=data.get('vendor_note', ''),
                file_type=data['file_type'],
            )
            order.design_file.name = f'makerspace/uploads/{dummy_fname}'
            order.save()

            # Add status log
            MakerspaceStatusLog.objects.create(
                order=order,
                old_status='',
                new_status=order.status,
                note='Order created',
                changed_by=data['customer'],
            )
            created_count += 1
            print(f'  Order {order.order_number}: {order.get_service_type_display()} — {order.get_status_display()}')

    print(f'  {created_count} sample orders created')

print(f'\n✅ Makerspace seed complete!')
print(f'   Profiles:  {MakerspaceProfile.objects.count()}')
print(f'   Orders:    {MakerspaceOrder.objects.count()}')
print()
print('Access:')
print('  Customer:  http://127.0.0.1:8000/makerspace/')
print('  Submit:    http://127.0.0.1:8000/makerspace/submit/')
print('  My orders: http://127.0.0.1:8000/makerspace/orders/')
print('  Vendor:    http://127.0.0.1:8000/makerspace/vendor/')
