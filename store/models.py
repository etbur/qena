from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, default='fas fa-tag')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:category', kwargs={'slug': self.slug})


class Product(models.Model):
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_flash_deal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    def get_full_url(self, request=None):
        from .qr_utils import get_base_url
        base = get_base_url(request)
        return f"{base}{self.get_absolute_url()}"

    def get_qr_code_data_uri(self, request=None):
        from .qr_utils import generate_qr_data_uri
        return generate_qr_data_uri(self.get_full_url(request))

    @property
    def qr_code_data_uri(self):
        return self.get_qr_code_data_uri()

    def get_qr_url(self):
        return reverse('store:product_qr', kwargs={'slug': self.slug})

    def get_qr_download_url(self):
        return f"{reverse('store:product_qr', kwargs={'slug': self.slug})}?download=1"

    def get_qr_badge_download_url(self):
        return f"{reverse('store:product_qr', kwargs={'slug': self.slug})}?format=badge&download=1"

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(100 - (self.price / self.original_price * 100))
        return 0

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_try_on_eligible(self):
        if not self.category:
            return False
        cat_slug = self.category.slug.lower()
        if cat_slug in ['fashion', 'fashion-habesha', 'ethiopian-crafts', 'home-majlis', 'beauty', 'beauty-skin']:
            return True
        keywords = ['kemis', 'dress', 'kandura', 'sheila', 'scarf', 'gabi', 'jacket', 'shirt', 'suit', 'cloth', 'wear', 'tshirt', 'hoodie', 'habesha']
        name_lower = self.name.lower()
        return any(k in name_lower for k in keywords)

    def get_try_on_url(self):
        return reverse('store:try_on_product', kwargs={'slug': self.slug})

    @property
    def try_on_overlay_url(self):
        slug_lower = (self.slug + ' ' + self.name).lower()
        if 'kemis' in slug_lower or 'dress' in slug_lower:
            return '/media/try_on/overlay_kemis.png'
        elif 'gabi' in slug_lower or 'blanket' in slug_lower:
            return '/media/try_on/overlay_gabi.png'
        elif 'kandura' in slug_lower or 'robe' in slug_lower or 'thobe' in slug_lower:
            return '/media/try_on/overlay_kandura.png'
        elif 'sheila' in slug_lower or 'silk' in slug_lower:
            return '/media/try_on/overlay_sheila.png'
        elif 'scarf' in slug_lower or 'shawl' in slug_lower or 'netela' in slug_lower:
            return '/media/try_on/overlay_scarf.png'
        elif 'mesob' in slug_lower or 'basket' in slug_lower:
            return '/media/try_on/overlay_mesob.png'
        return '/media/try_on/overlay_kemis.png'


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating}★)'


class Wishlist(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} → {self.product.name}'
