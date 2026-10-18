from .models import Category, Product
from orders.models import Cart


def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            sk = request.session.session_key
            cart = Cart.objects.filter(session_key=sk, user=None).first() if sk else None
        if cart:
            count = cart.item_count
    except Exception:
        pass
    return {'cart_count': count}


def categories_ctx(request):
    categories = Category.objects.filter(
        is_active=True, parent__isnull=True
    ).prefetch_related('children')[:12]
    trending = Product.objects.filter(
        is_active=True, is_featured=True
    ).select_related('category').order_by('-created_at')[:6]
    return {
        'nav_categories': categories,
        'nav_trending': trending,
    }
