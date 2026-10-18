"""
Qenagebeya API Serializers
Covers: Auth, Products, Categories, Cart, Orders, Vendors, Live, Makerspace
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User
from store.models import Product, Category
from vendors.models import Vendor
from orders.models import Order, OrderItem
from live.models import LiveStream, LiveChat


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        pwd = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(pwd)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'role', 'city', 'country', 'avatar_url')

    def get_avatar_url(self, obj):
        if obj.avatar:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.avatar.url) if req else obj.avatar.url
        return None


# ── Categories ────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ('id', 'name', 'slug', 'icon', 'image_url')

    def get_image_url(self, obj):
        if obj.image:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.image.url) if req else obj.image.url
        return None


# ── Products ─────────────────────────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    image_url      = serializers.SerializerMethodField()
    category_name  = serializers.CharField(source='category.name', default='')
    vendor_name    = serializers.CharField(source='vendor.store_name')
    discount_pct   = serializers.IntegerField(source='discount_percent')
    qr_code_url    = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ('id', 'name', 'slug', 'price', 'original_price', 'discount_pct',
                  'image_url', 'category_name', 'vendor_name', 'is_featured',
                  'is_flash_deal', 'stock', 'qr_code_url')

    def get_image_url(self, obj):
        if obj.image:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.image.url) if req else obj.image.url
        return None

    def get_qr_code_url(self, obj):
        req = self.context.get('request')
        url = obj.get_qr_url()
        return req.build_absolute_uri(url) if req else url


class ProductDetailSerializer(ProductListSerializer):
    images     = serializers.SerializerMethodField()
    vendor     = serializers.SerializerMethodField()
    category   = CategorySerializer()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ('description', 'images', 'vendor', 'category')

    def get_images(self, obj):
        req = self.context.get('request')
        imgs = []
        for f in [obj.image, obj.image2, obj.image3]:
            if f:
                imgs.append(req.build_absolute_uri(f.url) if req else f.url)
        return imgs

    def get_vendor(self, obj):
        v = obj.vendor
        req = self.context.get('request')
        return {
            'id':         v.pk,
            'store_name': v.store_name,
            'slug':       v.slug,
            'logo':       req.build_absolute_uri(v.logo.url) if v.logo and req else None,
            'subdomain':  v.subdomain,
            'qr_code_url': req.build_absolute_uri(v.get_qr_url()) if req else v.get_qr_url(),
        }


# ── Vendors ───────────────────────────────────────────────────────────────────

class VendorSerializer(serializers.ModelSerializer):
    logo_url   = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model  = Vendor
        fields = ('id', 'store_name', 'slug', 'description', 'store_tagline',
                  'logo_url', 'banner_url', 'phone', 'email', 'city', 'country',
                  'tier', 'whatsapp', 'instagram', 'facebook', 'products_count',
                  'subdomain', 'custom_domain', 'qr_code_url')

    def get_logo_url(self, obj):
        if obj.logo:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.logo.url) if req else obj.logo.url
        return None

    def get_banner_url(self, obj):
        if obj.banner:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.banner.url) if req else obj.banner.url
        return None

    def get_qr_code_url(self, obj):
        req = self.context.get('request')
        url = obj.get_qr_url()
        return req.build_absolute_uri(url) if req else url

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ('id', 'product_name', 'product_price', 'quantity',
                  'subtotal', 'product_image')

    def get_product_image(self, obj):
        if obj.product and obj.product.image:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.product.image.url) if req else obj.product.image.url
        return None


class OrderSerializer(serializers.ModelSerializer):
    items  = OrderItemSerializer(source='order_items', many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Order
        fields = ('id', 'order_number', 'status', 'status_display', 'total',
                  'shipping_name', 'shipping_address', 'shipping_phone',
                  'payment_method', 'created_at', 'items')


class PlaceOrderSerializer(serializers.Serializer):
    """Used when customer places an order from the app cart."""
    items          = serializers.ListField(child=serializers.DictField())
    shipping_name  = serializers.CharField()
    shipping_phone = serializers.CharField()
    shipping_address = serializers.CharField()
    payment_method = serializers.ChoiceField(choices=['telebirr', 'cbe_birr', 'amole', 'cash'])


# ── Live Streams ──────────────────────────────────────────────────────────────

class LiveStreamSerializer(serializers.ModelSerializer):
    vendor_name   = serializers.CharField(source='vendor.store_name')
    vendor_logo   = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display')
    has_host      = serializers.SerializerMethodField()

    class Meta:
        model  = LiveStream
        fields = ('id', 'stream_id', 'title', 'description', 'status', 'status_display',
                  'vendor_name', 'vendor_logo', 'thumbnail_url',
                  'total_views', 'live_viewers', 'total_likes', 'total_messages',
                  'is_paused', 'has_host',
                  'started_at', 'ended_at', 'created_at')

    def get_has_host(self, obj):
        return bool(obj.host_channel)

    def get_vendor_logo(self, obj):
        if obj.vendor.logo:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.vendor.logo.url) if req else obj.vendor.logo.url
        return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            req = self.context.get('request')
            return req.build_absolute_uri(obj.thumbnail.url) if req else obj.thumbnail.url
        return None


class LiveChatSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LiveChat
        fields = ('id', 'username', 'msg_type', 'text', 'created_at')


# ── Makerspace ────────────────────────────────────────────────────────────────

class MakerspaceOrderSerializer(serializers.ModelSerializer):
    status_display  = serializers.CharField(source='get_status_display', read_only=True)
    service_display = serializers.CharField(source='get_service_type_display', read_only=True)
    vendor_name     = serializers.CharField(source='vendor.store_name', default='', read_only=True)

    class Meta:
        from makerspace.models import MakerspaceOrder
        model  = MakerspaceOrder
        fields = ('id', 'service_type', 'service_display', 'material', 'quantity',
                  'status', 'status_display', 'system_price', 'vendor_price',
                  'final_price', 'vendor_name', 'vendor_note', 'created_at')
