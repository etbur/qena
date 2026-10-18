from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    path('',                                    views.dashboard,          name='dashboard'),
    # Users
    path('users/',                              views.users,              name='users'),
    path('users/<int:pk>/toggle/',              views.user_toggle_active, name='user_toggle'),
    # Vendors
    path('vendors/',                                      views.vendors,                  name='vendors'),
    path('vendors/<int:pk>/approve/',                     views.vendor_approve,           name='vendor_approve'),
    path('vendors/<int:pk>/suspend/',                     views.vendor_suspend,           name='vendor_suspend'),
    path('vendors/<int:pk>/reject/',                      views.vendor_reject,            name='vendor_reject'),
    path('vendors/<int:pk>/storefront-approve/',          views.vendor_storefront_approve,name='vendor_storefront_approve'),
    path('vendors/<int:pk>/storefront-reject/',           views.vendor_storefront_reject, name='vendor_storefront_reject'),
    # Payouts
    path('payouts/',                            views.payouts,            name='payouts'),
    path('payouts/<int:pk>/process/',           views.payout_process,     name='payout_process'),
    # Agents
    path('agents/',                             views.agents,             name='agents'),
    path('agents/<int:pk>/toggle/',             views.agent_toggle,       name='agent_toggle'),
    path('agent-commissions/',                  views.agent_commissions,  name='agent_commissions'),
    # Products
    path('products/',                           views.products,           name='products'),
    path('products/<int:pk>/toggle/',           views.product_toggle,     name='product_toggle'),
    # Categories
    path('categories/',                         views.categories,         name='categories'),
    path('categories/<int:pk>/toggle/',         views.category_toggle,    name='category_toggle'),
    # Orders
    path('orders/',                             views.orders,             name='orders'),
    path('orders/<int:pk>/status/',             views.order_update_status,name='order_status'),
    # Disputes
    path('disputes/',                           views.disputes,           name='disputes'),
    path('disputes/<int:pk>/resolve/',          views.dispute_resolve,    name='dispute_resolve'),
    # Analytics
    path('analytics/',                          views.analytics,          name='analytics'),
    # Audit & Settings
    path('audit/',                              views.audit_logs,         name='audit_logs'),
    path('settings/',                           views.settings_view,      name='settings'),
]
