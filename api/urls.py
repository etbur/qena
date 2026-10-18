"""
Qenagebeya REST API URL Configuration
Base: /api/v1/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────────────────
    path('auth/register/',      views.RegisterView.as_view(),      name='api_register'),
    path('auth/login/',         views.LoginView.as_view(),         name='api_login'),
    path('auth/refresh/',       TokenRefreshView.as_view(),        name='api_token_refresh'),
    path('auth/profile/',       views.ProfileView.as_view(),       name='api_profile'),

    # ── Home & Search ────────────────────────────────────────────────────────
    path('home/',               views.home_data,                   name='api_home'),
    path('search/',             views.search,                      name='api_search'),

    # ── Categories ───────────────────────────────────────────────────────────
    path('categories/',         views.CategoryListView.as_view(),  name='api_categories'),

    # ── Products ─────────────────────────────────────────────────────────────
    path('products/',           views.ProductListView.as_view(),   name='api_products'),
    path('products/<int:pk>/',  views.ProductDetailView.as_view(), name='api_product_detail'),

    # ── Vendors ──────────────────────────────────────────────────────────────
    path('vendors/',                            views.VendorListView.as_view(),    name='api_vendors'),
    path('vendors/<slug:slug>/',                views.VendorDetailView.as_view(),  name='api_vendor_detail'),
    path('vendors/<slug:slug>/products/',       views.VendorProductsView.as_view(),name='api_vendor_products'),

    # ── Orders ───────────────────────────────────────────────────────────────
    path('orders/',             views.MyOrdersView.as_view(),      name='api_orders'),
    path('orders/place/',       views.PlaceOrderView.as_view(),    name='api_order_place'),
    path('orders/<int:pk>/',    views.OrderDetailView.as_view(),   name='api_order_detail'),

    # ── Live ─────────────────────────────────────────────────────────────────
    path('live/',                                  views.LiveListView.as_view(),   name='api_live'),
    path('live/<uuid:stream_id>/',                 views.LiveDetailView.as_view(), name='api_live_detail'),
    path('live/<uuid:stream_id>/chat/',            views.LiveChatView.as_view(),   name='api_live_chat'),

    # ── Makerspace ───────────────────────────────────────────────────────────
    path('makerspace/my-orders/', views.MyMakerspaceOrdersView.as_view(), name='api_mk_orders'),
]
