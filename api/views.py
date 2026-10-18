"""
Qenagebeya REST API Views
Base URL: /api/v1/
"""
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q

from accounts.models import User
from store.models import Product, Category
from vendors.models import Vendor
from orders.models import Order, OrderItem
from live.models import LiveStream, LiveChat

from .serializers import (
    RegisterSerializer, UserSerializer,
    CategorySerializer,
    ProductListSerializer, ProductDetailSerializer,
    VendorSerializer,
    OrderSerializer, OrderItemSerializer, PlaceOrderSerializer,
    LiveStreamSerializer, LiveChatSerializer,
    MakerspaceOrderSerializer,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            user    = ser.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user':    UserSerializer(user, context={'request': request}).data,
                'tokens':  {'access': str(refresh.access_token), 'refresh': str(refresh)},
            }, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user':   UserSerializer(user, context={'request': request}).data,
            'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)},
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    queryset           = Category.objects.filter(is_active=True)
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]


# ── Products ──────────────────────────────────────────────────────────────────

class ProductListView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['name', 'description', 'category__name', 'vendor__store_name']
    ordering_fields    = ['price', 'created_at']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('vendor', 'category')
        cat   = self.request.query_params.get('category')
        feat  = self.request.query_params.get('featured')
        flash = self.request.query_params.get('flash')
        vendor = self.request.query_params.get('vendor')
        if cat:
            qs = qs.filter(category__slug=cat)
        if feat:
            qs = qs.filter(is_featured=True)
        if flash:
            qs = qs.filter(is_flash_deal=True)
        if vendor:
            qs = qs.filter(vendor__slug=vendor)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset           = Product.objects.filter(is_active=True).select_related('vendor', 'category')
    serializer_class   = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'pk'


# ── Vendors ───────────────────────────────────────────────────────────────────

class VendorListView(generics.ListAPIView):
    queryset           = Vendor.objects.filter(status=Vendor.STATUS_APPROVED)
    serializer_class   = VendorSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['store_name', 'city', 'description']


class VendorDetailView(generics.RetrieveAPIView):
    queryset           = Vendor.objects.filter(status=Vendor.STATUS_APPROVED)
    serializer_class   = VendorSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'slug'


class VendorProductsView(generics.ListAPIView):
    serializer_class   = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs['slug']
        return Product.objects.filter(vendor__slug=slug, is_active=True)


# ── Orders ────────────────────────────────────────────────────────────────────

class MyOrdersView(generics.ListAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class PlaceOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = PlaceOrderSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        items_data = d['items']
        if not items_data:
            return Response({'error': 'Cart is empty'}, status=400)

        # Calculate total
        total = 0
        order_items = []
        for it in items_data:
            try:
                product = Product.objects.get(pk=it['product_id'], is_active=True)
                qty = int(it.get('quantity', 1))
                subtotal = product.price * qty
                total += subtotal
                order_items.append({'product': product, 'qty': qty, 'price': product.price})
            except (Product.DoesNotExist, KeyError, ValueError):
                return Response({'error': f'Invalid product {it.get("product_id")}'}, status=400)

        order = Order.objects.create(
            user=request.user,
            shipping_name    = d['shipping_name'],
            shipping_phone   = d['shipping_phone'],
            shipping_address = d['shipping_address'],
            payment_method   = d['payment_method'],
            total=total,
        )
        for it in order_items:
            OrderItem.objects.create(
                order=order,
                product=it['product'],
                product_name=it['product'].name,
                product_price=it['price'],
                quantity=it['qty'],
            )
            # Decrement stock
            it['product'].stock = max(0, it['product'].stock - it['qty'])
            it['product'].save(update_fields=['stock'])

        return Response(
            OrderSerializer(order, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


# ── Live Streams ──────────────────────────────────────────────────────────────

class LiveListView(generics.ListAPIView):
    serializer_class   = LiveStreamSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        status_f = self.request.query_params.get('status', 'live')
        return LiveStream.objects.filter(status=status_f).select_related('vendor').order_by('-created_at')


class LiveDetailView(generics.RetrieveAPIView):
    queryset           = LiveStream.objects.all()
    serializer_class   = LiveStreamSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = 'stream_id'


class LiveChatView(generics.ListAPIView):
    serializer_class   = LiveChatSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        stream_id = self.kwargs['stream_id']
        return LiveChat.objects.filter(stream__stream_id=stream_id).order_by('-created_at')[:60]


# ── Makerspace ────────────────────────────────────────────────────────────────

class MyMakerspaceOrdersView(generics.ListAPIView):
    serializer_class   = MakerspaceOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from makerspace.models import MakerspaceOrder
        return MakerspaceOrder.objects.filter(customer=self.request.user).order_by('-created_at')


# ── Home / Search API ─────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def home_data(request):
    """Single endpoint — returns everything needed for the app home screen."""
    ctx = {'request': request}
    return Response({
        'featured':   ProductListSerializer(Product.objects.filter(is_active=True, is_featured=True)[:8],  many=True, context=ctx).data,
        'flash_deals':ProductListSerializer(Product.objects.filter(is_active=True, is_flash_deal=True)[:6], many=True, context=ctx).data,
        'new_arrivals':ProductListSerializer(Product.objects.filter(is_active=True).order_by('-created_at')[:12], many=True, context=ctx).data,
        'categories': CategorySerializer(Category.objects.filter(is_active=True)[:12], many=True, context=ctx).data,
        'live_now':   LiveStreamSerializer(LiveStream.objects.filter(status='live')[:4], many=True, context=ctx).data,
        'vendors':    VendorSerializer(Vendor.objects.filter(status=Vendor.STATUS_APPROVED)[:6], many=True, context=ctx).data,
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search(request):
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({'products': [], 'vendors': []})
    ctx = {'request': request}
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q),
        is_active=True
    )[:20]
    vendors = Vendor.objects.filter(
        Q(store_name__icontains=q) | Q(description__icontains=q),
        status=Vendor.STATUS_APPROVED
    )[:8]
    return Response({
        'products': ProductListSerializer(products, many=True, context=ctx).data,
        'vendors':  VendorSerializer(vendors, many=True, context=ctx).data,
    })
