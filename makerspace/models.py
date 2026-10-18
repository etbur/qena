"""
Makerspace module models.

Flow:
  Customer uploads file → system calculates estimated price
  → Customer places order → Vendor reviews → Accept/Reject
  → Vendor updates status (printing / ready / delivered)
"""
import uuid
import os
from decimal import Decimal
from django.db import models
from django.core.validators import FileExtensionValidator


# ── Vendor Makerspace Profile ─────────────────────────────────────────────────

class MakerspaceProfile(models.Model):
    """
    A vendor opts-in to the Makerspace and configures their pricing rates.
    """
    vendor      = models.OneToOneField(
        'vendors.Vendor', on_delete=models.CASCADE,
        related_name='makerspace_profile'
    )
    is_active   = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    # 3D Printing pricing (per gram, per material)
    price_pla_per_gram    = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('2.50'))
    price_petg_per_gram   = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('3.00'))
    price_abs_per_gram    = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('3.20'))
    price_resin_per_gram  = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('5.00'))

    # Laser / CNC pricing (per cm²)
    price_laser_per_cm2   = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.80'))
    price_cnc_per_cm2     = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.20'))

    # Design / other flat fee
    price_design_service  = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('150.00'))

    # Infill surcharge (%), lead time days
    min_lead_time_days    = models.PositiveIntegerField(default=3)
    max_lead_time_days    = models.PositiveIntegerField(default=7)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vendor.store_name} — Makerspace'

    def price_per_gram(self, material: str) -> Decimal:
        return {
            '3d_pla':   self.price_pla_per_gram,
            '3d_petg':  self.price_petg_per_gram,
            '3d_abs':   self.price_abs_per_gram,
            '3d_resin': self.price_resin_per_gram,
        }.get(material, self.price_pla_per_gram)


# ── Makerspace Order ──────────────────────────────────────────────────────────

def makerspace_upload_path(instance, filename):
    ext  = os.path.splitext(filename)[1].lower()
    name = f'mk_{uuid.uuid4().hex[:12]}{ext}'
    return os.path.join('makerspace', 'uploads', name)


class MakerspaceOrder(models.Model):

    # Service types
    SERVICE_3D_PRINT  = '3d_print'
    SERVICE_LASER     = 'laser'
    SERVICE_CNC       = 'cnc'
    SERVICE_DESIGN    = 'design'
    SERVICE_OTHER     = 'other'
    SERVICE_CHOICES   = [
        (SERVICE_3D_PRINT, '3D Printing'),
        (SERVICE_LASER,    'Laser Cutting/Engraving'),
        (SERVICE_CNC,      'CNC Machining'),
        (SERVICE_DESIGN,   'Design Service'),
        (SERVICE_OTHER,    'Other / Custom'),
    ]

    # 3D printing materials
    MATERIAL_PLA   = '3d_pla'
    MATERIAL_PETG  = '3d_petg'
    MATERIAL_ABS   = '3d_abs'
    MATERIAL_RESIN = '3d_resin'
    MATERIAL_CHOICES = [
        (MATERIAL_PLA,   'PLA (Standard)'),
        (MATERIAL_PETG,  'PETG (Durable)'),
        (MATERIAL_ABS,   'ABS (Heat-resistant)'),
        (MATERIAL_RESIN, 'Resin (High detail)'),
        ('laser_wood',   'Wood (Laser)'),
        ('laser_acrylic','Acrylic (Laser)'),
        ('laser_metal',  'Metal (Laser)'),
        ('cnc_wood',     'Wood (CNC)'),
        ('cnc_aluminum', 'Aluminum (CNC)'),
        ('none',         'Not Applicable'),
    ]

    # Infill choices for 3D printing
    INFILL_15  = 15
    INFILL_30  = 30
    INFILL_50  = 50
    INFILL_75  = 75
    INFILL_100 = 100
    INFILL_CHOICES = [
        (15,  '15% — Draft'),
        (30,  '30% — Standard'),
        (50,  '50% — Strong'),
        (75,  '75% — Very Strong'),
        (100, '100% — Solid'),
    ]

    # Status workflow
    STATUS_QUOTE_PENDING  = 'quote_pending'   # file uploaded, awaiting vendor review
    STATUS_QUOTED         = 'quoted'           # vendor set a final price
    STATUS_ACCEPTED       = 'accepted'         # customer accepted quote
    STATUS_IN_PRODUCTION  = 'in_production'    # vendor is printing/cutting
    STATUS_READY          = 'ready'            # ready for pickup / shipping
    STATUS_DELIVERED      = 'delivered'        # completed
    STATUS_REJECTED       = 'rejected'         # vendor rejected
    STATUS_CANCELLED      = 'cancelled'        # customer cancelled
    STATUS_CHOICES = [
        (STATUS_QUOTE_PENDING, 'Quote Pending'),
        (STATUS_QUOTED,        'Quoted'),
        (STATUS_ACCEPTED,      'Accepted'),
        (STATUS_IN_PRODUCTION, 'In Production'),
        (STATUS_READY,         'Ready'),
        (STATUS_DELIVERED,     'Delivered'),
        (STATUS_REJECTED,      'Rejected'),
        (STATUS_CANCELLED,     'Cancelled'),
    ]

    order_number = models.CharField(max_length=30, unique=True, editable=False)
    customer     = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='makerspace_orders'
    )
    vendor       = models.ForeignKey(
        'vendors.Vendor', on_delete=models.SET_NULL, null=True,
        related_name='makerspace_orders'
    )

    # Service
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, default=SERVICE_3D_PRINT)
    material     = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default=MATERIAL_PLA)
    infill       = models.PositiveIntegerField(choices=INFILL_CHOICES, default=30)
    quantity     = models.PositiveIntegerField(default=1)
    color        = models.CharField(max_length=60, blank=True, help_text='e.g. White, Black, Blue')
    notes        = models.TextField(blank=True)

    # Uploaded file
    design_file  = models.FileField(
        upload_to=makerspace_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['stl', 'dxf', 'dwg', 'svg', 'pdf', 'obj', 'step', 'stp', 'iges', 'igs']
        )]
    )
    file_type    = models.CharField(max_length=10, blank=True)   # stl / dxf / pdf …

    # Auto-calculated from file
    estimated_volume_cm3 = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    estimated_grams      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_area_cm2   = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    # Pricing
    system_price  = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # auto-calculated
    vendor_price  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # vendor override
    final_price   = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUOTE_PENDING)
    vendor_note   = models.TextField(blank=True)  # vendor message to customer
    rejection_reason = models.TextField(blank=True)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_number} — {self.get_service_type_display()}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'MK-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    @property
    def file_name(self):
        return os.path.basename(self.design_file.name) if self.design_file else '—'

    @property
    def status_color(self):
        return {
            self.STATUS_QUOTE_PENDING: 'pending',
            self.STATUS_QUOTED:        'processing',
            self.STATUS_ACCEPTED:      'shipped',
            self.STATUS_IN_PRODUCTION: 'processing',
            self.STATUS_READY:         'shipped',
            self.STATUS_DELIVERED:     'delivered',
            self.STATUS_REJECTED:      'cancelled',
            self.STATUS_CANCELLED:     'cancelled',
        }.get(self.status, 'pending')

    @property
    def can_accept(self):
        return self.status == self.STATUS_QUOTED

    @property
    def can_cancel(self):
        return self.status in (self.STATUS_QUOTE_PENDING, self.STATUS_QUOTED, self.STATUS_ACCEPTED)


# ── Makerspace Order Status Log ───────────────────────────────────────────────

class MakerspaceStatusLog(models.Model):
    order      = models.ForeignKey(MakerspaceOrder, on_delete=models.CASCADE, related_name='logs')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    note       = models.TextField(blank=True)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.order.order_number}: {self.old_status} → {self.new_status}'
