from django.urls import path
from . import views
from .search_api import search_suggest

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('products/<slug:slug>/qr/', views.product_qr_image, name='product_qr'),
    path('category/<slug:slug>/', views.category_view, name='category'),

    # Search API
    path('api/search-suggest/', search_suggest, name='search_suggest'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    # Virtual Try-On
    path('try-on/', views.try_on_studio, name='try_on'),
    path('try-on/studio/', views.try_on_studio, name='try_on_studio'),
    path('try-on/<slug:slug>/', views.try_on_studio, name='try_on_product'),
    path('api/try-on/items/', views.try_on_items_api, name='try_on_items_api'),
]
