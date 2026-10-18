"""URL patterns for the white-label vendor storefront."""
from django.urls import path
from . import storefront_views as sf

app_name = 'storefront'

urlpatterns = [
    path('',                     sf.sf_home,        name='home'),
    path('product/<int:pk>/',    sf.sf_product,     name='product'),
    path('about/',               sf.sf_about,       name='about'),
    path('contact/',             sf.sf_contact,     name='contact'),
    path('cart/',                sf.sf_cart,        name='cart'),
    path('cart/add/<int:pk>/',   sf.sf_cart_add,    name='cart_add'),
    path('cart/remove/<int:pk>/',sf.sf_cart_remove, name='cart_remove'),
]
