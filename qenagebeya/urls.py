from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponse


def storefront_router(request):
    """Route to vendor storefront if subdomain/custom domain detected."""
    if request.vendor_storefront:
        from django.urls import resolve, Resolver404
        from vendors.storefront_urls import urlpatterns as sf_patterns
        from django.urls import URLResolver
        resolver = URLResolver('/', sf_patterns)
        path_info = request.path_info or '/'
        try:
            match = resolver.resolve(path_info)
            return match.func(request, *match.args, **match.kwargs)
        except Exception:
            from vendors.storefront_views import sf_home
            return sf_home(request)
    return None


class StorefrontMiddlewareRouter:
    """Used by urlpatterns — catches all paths when vendor_storefront is set."""
    pass


# Language switcher (outside i18n_patterns)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('accounts/', include('accounts.urls')),
    path('vendor/', include('vendors.urls')),
    path('agent/', include('agents.urls')),
    path('orders/', include('orders.urls')),
    path('portal/', include('admin_portal.urls')),
    path('makerspace/', include('makerspace.urls')),
    path('live/', include('live.urls')),
    prefix_default_language=False,
)

# API — outside i18n_patterns (no language prefix needed)
from django.urls import path as _path
urlpatterns += [
    _path('api/v1/', include('api.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
