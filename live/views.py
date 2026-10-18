from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .models import LiveStream, LiveChat
from .forms import LiveStreamForm, PinProductForm
from vendors.models import Vendor
from store.models import Product


# ─── Public ──────────────────────────────────────────────────────────────────

def live_home(request):
    """Browse all live and upcoming streams — only displays streams actively live with open camera."""
    live_now = LiveStream.objects.filter(
        status=LiveStream.STATUS_LIVE
    ).exclude(
        host_channel=''
    ).select_related('vendor', 'pinned_product')

    upcoming = LiveStream.objects.filter(
        status=LiveStream.STATUS_SCHEDULED
    ).select_related('vendor').order_by('scheduled_at')[:8]

    recent = LiveStream.objects.filter(
        status=LiveStream.STATUS_ENDED
    ).select_related('vendor').order_by('-ended_at')[:8]

    return render(request, 'live/home.html', {
        'live_now': live_now,
        'upcoming': upcoming,
        'recent':   recent,
    })


def watch_stream(request, stream_uuid):
    """The main viewer page."""
    stream = get_object_or_404(LiveStream, stream_id=stream_uuid)
    if stream.status == LiveStream.STATUS_LIVE:
        stream.total_views += 1
        stream.save(update_fields=['total_views'])

    vendor_products = stream.vendor.products.filter(is_active=True)[:20]
    is_host = (
        request.user.is_authenticated
        and hasattr(request.user, 'vendor_profile')
        and request.user.vendor_profile.pk == stream.vendor.pk
    )
    return render(request, 'live/watch.html', {
        'stream':          stream,
        'vendor_products': vendor_products,
        'is_host':         is_host,
    })


# ─── Vendor ───────────────────────────────────────────────────────────────────

def _vendor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not hasattr(request.user, 'vendor_profile'):
            messages.warning(request, 'Vendor account required.')
            return redirect('vendors:setup')
        if request.user.vendor_profile.status != Vendor.STATUS_APPROVED:
            return redirect('vendors:pending')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@_vendor_required
def vendor_streams(request):
    """Vendor: manage their streams."""
    vendor  = request.user.vendor_profile
    streams = LiveStream.objects.filter(vendor=vendor).order_by('-created_at')
    return render(request, 'live/vendor/streams.html', {
        'vendor':  vendor,
        'streams': streams,
    })


@_vendor_required
def stream_create(request):
    """Vendor: create a new stream."""
    vendor = request.user.vendor_profile
    form   = LiveStreamForm(request.POST or None, request.FILES or None, vendor=vendor)
    if form.is_valid():
        stream = form.save(commit=False)
        stream.vendor = vendor
        stream.save()
        messages.success(request, f'Stream "{stream.title}" created.')
        return redirect('live:vendor_streams')
    return render(request, 'live/vendor/stream_form.html', {'form': form, 'vendor': vendor, 'action': 'Create'})


@_vendor_required
def stream_go_live(request, stream_uuid):
    """Vendor starts the stream."""
    vendor = request.user.vendor_profile
    stream = get_object_or_404(LiveStream, stream_id=stream_uuid, vendor=vendor)
    if request.method == 'POST':
        stream.status     = LiveStream.STATUS_LIVE
        stream.started_at = timezone.now()
        stream.save()
        messages.success(request, f'You are now LIVE: {stream.title}')
        return redirect('live:watch', stream_uuid=stream_uuid)
    return render(request, 'live/vendor/go_live.html', {'stream': stream, 'vendor': vendor})


@_vendor_required
def stream_end(request, stream_uuid):
    """Vendor ends the stream via HTTP (also triggered via WS)."""
    vendor = request.user.vendor_profile
    stream = get_object_or_404(LiveStream, stream_id=stream_uuid, vendor=vendor)
    if request.method == 'POST':
        stream.status   = LiveStream.STATUS_ENDED
        stream.ended_at = timezone.now()
        stream.save()
        messages.info(request, 'Stream ended.')
        return redirect('live:vendor_streams')
    return render(request, 'live/vendor/end_confirm.html', {'stream': stream})


# ─── AJAX endpoints ───────────────────────────────────────────────────────────

@login_required
def api_pin_product(request, stream_uuid):
    """Vendor pins a product during live — returns JSON for WS broadcast."""
    stream = get_object_or_404(LiveStream, stream_id=stream_uuid)
    if not (hasattr(request.user, 'vendor_profile') and
            request.user.vendor_profile == stream.vendor):
        return JsonResponse({'ok': False}, status=403)
    product_id = request.POST.get('product_id')
    try:
        product = Product.objects.get(pk=product_id, vendor=stream.vendor, is_active=True)
        stream.pinned_product = product
        stream.save(update_fields=['pinned_product'])
        return JsonResponse({
            'ok':    True,
            'id':    product.pk,
            'name':  product.name,
            'price': str(product.price),
            'image': product.image.url if product.image else '',
            'url':   product.get_absolute_url(),
        })
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Product not found'}, status=404)


def api_stream_info(request, stream_uuid):
    """Returns live stream status as JSON (for polling fallback)."""
    stream = get_object_or_404(LiveStream, stream_id=stream_uuid)
    return JsonResponse({
        'status':       stream.status,
        'is_paused':    stream.is_paused,
        'live_viewers': stream.live_viewers,
        'viewers':      stream.total_views,
        'likes':        stream.total_likes,
        'messages':     stream.total_messages,
        'has_host':     bool(stream.host_channel),
    })


def api_active_streams(request):
    """Returns currently live streams for real-time live discovery (only with active open camera or pause)."""
    live_streams = LiveStream.objects.filter(
        status=LiveStream.STATUS_LIVE
    ).exclude(
        host_channel=''
    ).select_related('vendor')
    data = []
    for s in live_streams:
        data.append({
            'stream_id':    str(s.stream_id),
            'title':        s.title,
            'vendor_name':  s.vendor.store_name,
            'live_viewers': s.live_viewers,
            'total_likes':  s.total_likes,
            'thumbnail':    s.thumbnail.url if s.thumbnail else '',
            'is_paused':    s.is_paused,
            'has_host':     bool(s.host_channel),
            'url':          f'/live/{s.stream_id}/',
        })
    return JsonResponse({'streams': data, 'count': len(data)})
