from django.urls import path
from . import views

app_name = 'makerspace'

urlpatterns = [
    # ── Customer-facing ──────────────────────────────────────────────────────
    path('',                               views.makerspace_landing, name='landing'),
    path('workshop/3d-printing/',          views.workshop_3d,        name='workshop_3d'),
    path('workshop/laser-cutting/',        views.workshop_laser,     name='workshop_laser'),
    path('workshop/cnc-machining/',        views.workshop_cnc,       name='workshop_cnc'),
    path('workshop/design-service/',       views.workshop_design,    name='workshop_design'),
    path('api/ai-cad-generate/',           views.api_ai_cad_generate, name='api_ai_cad_generate'),
    path('submit/',                        views.submit_order,       name='submit_order'),
    path('submit/<slug:vendor_slug>/',     views.submit_order,       name='submit_order_vendor'),
    path('orders/',                        views.my_orders,          name='my_orders'),
    path('orders/<int:pk>/',               views.order_detail,       name='order_detail'),
    path('orders/<int:pk>/accept/',        views.accept_quote,       name='accept_quote'),
    path('orders/<int:pk>/cancel/',        views.cancel_order,       name='cancel_order'),

    # ── Vendor portal ────────────────────────────────────────────────────────
    path('vendor/',                        views.vendor_dashboard,    name='vendor_dashboard'),
    path('vendor/orders/',                 views.vendor_orders,       name='vendor_orders'),
    path('vendor/orders/<int:pk>/',        views.vendor_order_detail, name='vendor_order_detail'),
    path('vendor/settings/',              views.vendor_settings,     name='vendor_settings'),
]
