from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('setup/',                              views.setup,             name='setup'),
    path('pending/',                            views.pending,           name='pending'),
    path('dashboard/',                          views.dashboard,         name='dashboard'),
    # Products
    path('products/',                           views.products,          name='products'),
    path('products/add/',                       views.product_add,       name='product_add'),
    path('products/<int:pk>/edit/',             views.product_edit,      name='product_edit'),
    path('products/<int:pk>/delete/',           views.product_delete,    name='product_delete'),
    # Orders
    path('orders/',                             views.orders_view,       name='orders'),
    path('orders/fulfill/<int:order_item_id>/', views.order_fulfill,     name='order_fulfill'),
    # Inventory
    path('inventory/',                          views.inventory,         name='inventory'),
    path('inventory/add/',                      views.inventory_add,     name='inventory_add'),
    path('inventory/<int:pk>/edit/',            views.inventory_edit,    name='inventory_edit'),
    path('inventory/<int:pk>/delete/',          views.inventory_delete,  name='inventory_delete'),
    path('inventory/<int:pk>/update/',          views.inventory_update,  name='inventory_update'),
    path('inventory/<int:pk>/adjust/',          views.inventory_adjust,  name='inventory_adjust'),
    path('warehouses/',                         views.warehouse_list,    name='warehouses'),
    path('suppliers/',                          views.supplier_list,     name='suppliers'),
    path('purchase-orders/',                    views.purchase_orders,   name='purchase_orders'),
    path('stock-movements/',                    views.stock_movements,   name='stock_movements'),
    # Payouts
    path('payouts/',                            views.payouts,           name='payouts'),
    # Customers
    path('customers/',                          views.customers,         name='customers'),
    # Analytics & Settings
    path('analytics/',                          views.analytics,             name='analytics'),
    path('settings/',                           views.settings_view,         name='settings'),
    path('storefront/',                         views.storefront_settings,   name='storefront_settings'),
    # Public store
    path('store/<slug:slug>/',                  views.vendor_store,          name='store'),
    path('store/<slug:slug>/qr/',               views.vendor_qr_image,       name='vendor_qr'),
]
