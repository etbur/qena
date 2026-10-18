from vendors.models import Vendor, VendorPayout
from .models import Dispute


def admin_badges(request):
    """Inject sidebar badge counts for admin portal."""
    counts = {
        'pending_vendor_count':  0,
        'open_dispute_count':    0,
        'pending_payout_count':  0,
    }
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and (
        user.is_staff or getattr(user, 'role', '') == 'admin'
    ):
        counts['pending_vendor_count'] = Vendor.objects.filter(
            status=Vendor.STATUS_PENDING
        ).count()
        counts['open_dispute_count'] = Dispute.objects.filter(
            status=Dispute.STATUS_OPEN
        ).count()
        counts['pending_payout_count'] = VendorPayout.objects.filter(
            status=VendorPayout.STATUS_PENDING
        ).count()
    return counts
