from django.urls import path
from . import views

app_name = 'live'

urlpatterns = [
    # Public
    path('',                                    views.live_home,        name='home'),
    path('<uuid:stream_uuid>/',                 views.watch_stream,     name='watch'),

    # Vendor portal
    path('vendor/',                             views.vendor_streams,   name='vendor_streams'),
    path('vendor/create/',                      views.stream_create,    name='stream_create'),
    path('vendor/<uuid:stream_uuid>/go-live/',  views.stream_go_live,   name='go_live'),
    path('vendor/<uuid:stream_uuid>/end/',      views.stream_end,       name='stream_end'),

    # AJAX
    path('api/active/',                         views.api_active_streams, name='api_active'),
    path('api/<uuid:stream_uuid>/pin/',         views.api_pin_product,  name='api_pin'),
    path('api/<uuid:stream_uuid>/info/',        views.api_stream_info,  name='api_info'),
]
