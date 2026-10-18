from django.db import models
from django.utils.text import slugify


class Vendor(models.Model):
    TIER_BRONZE = 'bronze'
    TIER_SILVER = 'silver'
    TIER_GOLD = 'gold'
    TIER_PLATINUM = 'platinum'
    TIER_CHOICES = [
        (TIER_BRONZE, 'Bronze'),
        (TIER_SILVER, 'Silver'),
        (TIER_GOLD, 'Gold'),
        (TIER_PLATINUM, 'Platinum'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='vendor_profile')
    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='vendors/banners/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='UAE')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default=TIER_BRONZE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    total_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # ── White-label storefront ─────────────────────────────────────────
    # Subdomain: alex → alex.qenagebeya.com  (auto-set from slug)
    subdomain = models.CharField(max_length=100, unique=True, blank=True,
        help_text='Subdomain e.g. "alex" → alex.qenagebeya.com')
    # Custom domain: alex.com (vendor points their domain DNS here)
    custom_domain = models.CharField(max_length=253, blank=True,
        help_text='Custom domain e.g. alex.com — vendor must point DNS to this server')
    storefront_enabled = models.BooleanField(default=True,
        help_text='Allow vendor storefront on subdomain/custom domain')

    # ── 10,000 ETB / Year Annual Subscription & Admin Approval by FT ──
    STOREFRONT_STATUS_INACTIVE = 'inactive'
    STOREFRONT_STATUS_PENDING = 'pending_approval'
    STOREFRONT_STATUS_ACTIVE = 'active'
    STOREFRONT_STATUS_EXPIRED = 'expired'
    STOREFRONT_STATUS_CHOICES = [
        (STOREFRONT_STATUS_INACTIVE, 'Inactive (Unpaid)'),
        (STOREFRONT_STATUS_PENDING, 'Pending Admin Approval (10,000 ETB FT Submitted)'),
        (STOREFRONT_STATUS_ACTIVE, 'Active (10,000 ETB / Year Approved)'),
        (STOREFRONT_STATUS_EXPIRED, 'Expired (Subscription Over)'),
    ]

    storefront_status = models.CharField(
        max_length=30, choices=STOREFRONT_STATUS_CHOICES, default=STOREFRONT_STATUS_INACTIVE,
        help_text='Standalone domain status (10,000 ETB/year by FT)'
    )
    storefront_annual_fee = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    storefront_payment_method = models.CharField(max_length=50, default='bank_transfer', blank=True)
    storefront_payment_ref = models.CharField(max_length=100, blank=True, help_text='FT Reference / Bank Transaction ID')
    storefront_payment_note = models.TextField(blank=True, help_text='Bank details or payment remarks')
    storefront_approved_at = models.DateTimeField(null=True, blank=True)
    storefront_expires_at = models.DateTimeField(null=True, blank=True, help_text='1-year expiry date')
    # ──────────────────────────────────────────────────────────────────

    # Branding
    brand_primary   = models.CharField(max_length=7, default='#0b2b4a', help_text='Hex color e.g. #0b2b4a')
    brand_secondary = models.CharField(max_length=7, default='#d42e2e', help_text='Hex accent color')
    brand_font      = models.CharField(max_length=100, default='Inter', blank=True)
    store_tagline   = models.CharField(max_length=200, blank=True)
    store_keywords  = models.CharField(max_length=300, blank=True, help_text='SEO keywords, comma-separated')
    whatsapp        = models.CharField(max_length=30, blank=True)
    telegram        = models.CharField(max_length=100, blank=True)
    instagram       = models.CharField(max_length=100, blank=True)
    facebook        = models.CharField(max_length=100, blank=True)
    twitter         = models.CharField(max_length=100, blank=True)
    tiktok          = models.CharField(max_length=100, blank=True)
    # ──────────────────────────────────────────────────────────────────

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.store_name

    def clean_domain(self, domain_str):
        if not domain_str:
            return ''
        d = domain_str.strip().lower()
        for prefix in ('https://', 'http://', 'www.'):
            if d.startswith(prefix):
                d = d[len(prefix):]
        return d.rstrip('/')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.store_name) or 'store'
        if not self.subdomain:
            self.subdomain = self.slug
        else:
            self.subdomain = slugify(self.subdomain) or self.slug
        if self.custom_domain:
            self.custom_domain = self.clean_domain(self.custom_domain)
        super().save(*args, **kwargs)

    @property
    def is_storefront_active(self):
        """Returns True if the 10,000 ETB/yr standalone storefront is active and approved."""
        from django.utils import timezone
        if not self.storefront_enabled:
            return False
        if self.storefront_status != self.STOREFRONT_STATUS_ACTIVE:
            return False
        if self.storefront_expires_at and self.storefront_expires_at < timezone.now():
            return False
        return True

    @property
    def storefront_days_left(self):
        from django.utils import timezone
        if self.is_storefront_active and self.storefront_expires_at:
            delta = self.storefront_expires_at - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def total_products(self):
        return self.products.filter(is_active=True).count()

    @property
    def total_orders(self):
        from orders.models import OrderItem
        return OrderItem.objects.filter(product__vendor=self).count()

    @property
    def storefront_url(self):
        """Returns the best URL for this vendor's white-label store."""
        if self.custom_domain:
            return f'http://{self.custom_domain}'
        if self.subdomain:
            return f'http://{self.subdomain}.localhost:8000'
        return f'/vendor/store/{self.slug}/'

    @property
    def marketplace_url(self):
        """Returns the vendor's store page on the main marketplace."""
        return f'/vendor/store/{self.slug}/'

    def get_store_url(self, request=None):
        from django.urls import reverse
        from store.qr_utils import get_base_url
        if self.custom_domain and self.is_storefront_active:
            return f'http://{self.custom_domain}'
        base = get_base_url(request)
        return f"{base}{reverse('vendors:store', kwargs={'slug': self.slug})}"

    def get_qr_code_data_uri(self, request=None):
        from store.qr_utils import generate_qr_data_uri
        return generate_qr_data_uri(self.get_store_url(request), fill_color=self.brand_primary or '#0b2b4a')

    @property
    def qr_code_data_uri(self):
        return self.get_qr_code_data_uri()

    def get_qr_url(self):
        from django.urls import reverse
        return reverse('vendors:vendor_qr', kwargs={'slug': self.slug})

    def get_qr_download_url(self):
        from django.urls import reverse
        return f"{reverse('vendors:vendor_qr', kwargs={'slug': self.slug})}?download=1"

    def get_qr_badge_download_url(self):
        from django.urls import reverse
        return f"{reverse('vendors:vendor_qr', kwargs={'slug': self.slug})}?format=badge&download=1"


class VendorBankAccount(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='bank_account')
    bank_name = models.CharField(max_length=200)
    account_holder = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.vendor.store_name} – {self.bank_name}'


class VendorPayout(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.TextField(blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f'{self.vendor.store_name} – ETB {self.amount} ({self.get_status_display()})'


class VendorInventoryItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='private_inventory')
    item_name = models.CharField(max_length=250)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    category = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    unit = models.CharField(max_length=30, default='pcs', blank=True)
    location = models.CharField(max_length=150, blank=True)
    warehouse = models.ForeignKey('VendorWarehouse', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    supplier = models.ForeignKey('VendorSupplier', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='inventory/', blank=True, null=True)
    is_public = models.BooleanField(default=False)
    linked_product = models.OneToOneField('store.Product', null=True, blank=True, on_delete=models.SET_NULL, related_name='private_item')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.item_name} ({self.vendor.store_name})'

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out'
        if self.quantity <= self.reorder_level:
            return 'low'
        return 'ok'

    @property
    def total_value(self):
        return self.unit_cost * self.quantity


class VendorWarehouse(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f'{self.name} — {self.vendor.store_name}'


class VendorSupplier(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} — {self.vendor.store_name}'


class StockMovement(models.Model):
    TYPE_IN       = 'in'
    TYPE_OUT      = 'out'
    TYPE_TRANSFER = 'transfer'
    TYPE_ADJUST   = 'adjust'
    TYPE_RETURN   = 'return'
    TYPE_CHOICES  = [
        (TYPE_IN,       'Stock In'),
        (TYPE_OUT,      'Stock Out'),
        (TYPE_TRANSFER, 'Transfer'),
        (TYPE_ADJUST,   'Adjustment'),
        (TYPE_RETURN,   'Customer Return'),
    ]
    item      = models.ForeignKey(VendorInventoryItem, on_delete=models.CASCADE, related_name='movements')
    move_type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    quantity  = models.IntegerField()          # positive = in, negative = out
    before_qty = models.IntegerField(default=0)
    after_qty  = models.IntegerField(default=0)
    reference = models.CharField(max_length=200, blank=True)  # order #, PO #, etc.
    note      = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.item.item_name} {self.move_type} {self.quantity}'


class PurchaseOrder(models.Model):
    STATUS_DRAFT     = 'draft'
    STATUS_ORDERED   = 'ordered'
    STATUS_RECEIVED  = 'received'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES   = [
        (STATUS_DRAFT,     'Draft'),
        (STATUS_ORDERED,   'Ordered'),
        (STATUS_RECEIVED,  'Received'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    vendor     = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier   = models.ForeignKey(VendorSupplier, null=True, blank=True, on_delete=models.SET_NULL)
    po_number  = models.CharField(max_length=50, unique=True, blank=True)
    status     = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    note       = models.TextField(blank=True)
    expected_date = models.DateField(null=True, blank=True)
    received_at   = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PO-{self.po_number} ({self.vendor.store_name})'

    def save(self, *args, **kwargs):
        if not self.po_number:
            import uuid
            self.po_number = str(uuid.uuid4()).replace('-','')[:10].upper()
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    po          = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(VendorInventoryItem, null=True, blank=True, on_delete=models.SET_NULL)
    item_name   = models.CharField(max_length=250)
    quantity    = models.PositiveIntegerField(default=1)
    unit_cost   = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_cost * self.quantity

    def __str__(self):
        return f'{self.item_name} x{self.quantity}'

