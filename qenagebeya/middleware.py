"""
LocalhostRedirectMiddleware — redirects 127.0.0.1 → localhost for camera access.
StorefrontMiddleware — detects vendor subdomain/custom domain and sets request.vendor_storefront.
"""
from django.http import HttpResponsePermanentRedirect


class LocalhostRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.startswith('127.0.0.1'):
            new_host = host.replace('127.0.0.1', 'localhost', 1)
            new_url  = request.build_absolute_uri().replace(host, new_host, 1)
            return HttpResponsePermanentRedirect(new_url)
        return self.get_response(request)


class StorefrontMiddleware:
    """
    Detects vendor subdomains or custom domains (e.g. alex.com, alex.qenagebeya.com, alex.localhost).
    On match: routes request to the vendor's white-label storefront views.
    On no match: passes through to normal marketplace routing.
    """
    BASE_DOMAIN = 'qenagebeya.com'
    DEV_BASE    = 'localhost'
    SYSTEM_HOSTS = {
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        'qenagebeya.com',
        'www.qenagebeya.com',
        'testserver',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.vendor_storefront = None
        path = request.path_info or '/'

        # Always bypass static, media, favicon, and i18n assets so they serve correctly
        if (
            path.startswith('/static/') or
            path.startswith('/media/') or
            path == '/favicon.ico' or
            path.startswith('/__') or
            path.startswith('/i18n/')
        ):
            return self.get_response(request)

        host = request.get_host().lower().split(':')[0].strip()

        vendor = None
        if host not in self.SYSTEM_HOSTS:
            from vendors.models import Vendor
            from django.db.models import Q

            # 1. Subdomain matching (e.g. alex.qenagebeya.com or alex.localhost or alex.127.0.0.1.nip.io)
            if host.endswith('.' + self.BASE_DOMAIN):
                sub = host[:-(len(self.BASE_DOMAIN) + 1)].strip()
                if sub and sub != 'www':
                    vendor = Vendor.objects.filter(
                        subdomain__iexact=sub,
                        storefront_enabled=True,
                        status=Vendor.STATUS_APPROVED
                    ).first()
            elif host.endswith('.' + self.DEV_BASE):
                sub = host[:-(len(self.DEV_BASE) + 1)].strip()
                if sub and sub != 'www':
                    vendor = Vendor.objects.filter(
                        subdomain__iexact=sub,
                        storefront_enabled=True,
                        status=Vendor.STATUS_APPROVED
                    ).first()
            elif '.nip.io' in host or '.lvh.me' in host:
                parts = host.split('.')
                if len(parts) > 1:
                    sub = parts[0].strip()
                    vendor = Vendor.objects.filter(
                        subdomain__iexact=sub,
                        storefront_enabled=True,
                        status=Vendor.STATUS_APPROVED
                    ).first()

            # 2. Custom domain matching (e.g. alex.com, www.alex.com, mybrand.et)
            if not vendor:
                clean_host = host.removeprefix('www.')
                vendor = Vendor.objects.filter(
                    Q(custom_domain__iexact=host) |
                    Q(custom_domain__iexact=clean_host) |
                    Q(custom_domain__iexact='www.' + clean_host) |
                    Q(custom_domain__iexact='http://' + clean_host) |
                    Q(custom_domain__iexact='https://' + clean_host),
                    storefront_enabled=True,
                    status=Vendor.STATUS_APPROVED
                ).first()

            # 3. Fallback: match subdomain/slug directly for dev flexibility
            if not vendor:
                vendor = Vendor.objects.filter(
                    Q(subdomain__iexact=host) | Q(slug__iexact=host),
                    storefront_enabled=True,
                    status=Vendor.STATUS_APPROVED
                ).first()

        request.vendor_storefront = vendor

        # If this is a vendor storefront domain → check subscription approval
        if vendor:
            # Check 10,000 ETB / year Admin Approval & subscription status
            if not vendor.is_storefront_active:
                from django.shortcuts import render
                return render(request, 'storefront/pending_approval.html', {'vendor': vendor})

            from django.urls.resolvers import URLResolver, RoutePattern, Resolver404

            resolver = URLResolver(RoutePattern(''), 'vendors.storefront_urls')
            try:
                # Strip leading slash for resolver matching if needed
                match = resolver.resolve(path.lstrip('/'))
                request.resolver_match = match
                return match.func(request, *match.args, **match.kwargs)
            except Resolver404:
                # Return storefront home on unmatched routes
                from vendors.storefront_views import sf_home
                return sf_home(request)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Storefront routing error: {e}")
                from vendors.storefront_views import sf_home
                return sf_home(request)

        return self.get_response(request)
