"""
/api/search-suggest/?q=... → returns JSON suggestions for the popup autocomplete.
"""
import json
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category
from .fuzzy import normalise, trigram_similarity, tokenise


def search_suggest(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'suggestions': []})

    q_norm = normalise(q)

    # 1. Exact / contains matches (fast)
    products = Product.objects.filter(
        is_active=True
    ).filter(
        Q(name__icontains=q) |
        Q(category__name__icontains=q) |
        Q(vendor__store_name__icontains=q)
    ).select_related('category', 'vendor').values(
        'name', 'price', 'slug', 'category__name'
    )[:6]

    suggestions = [
        {
            'label': p['name'],
            'sub': p['category__name'] or '',
            'price': f"ETB {int(p['price']):,}",
            'url': f"/products/{p['slug']}/",
            'type': 'product',
        }
        for p in products
    ]

    # 2. Category suggestions
    cats = Category.objects.filter(
        is_active=True, name__icontains=q
    ).values('name', 'slug')[:3]

    for c in cats:
        suggestions.append({
            'label': c['name'],
            'sub': 'Category',
            'price': '',
            'url': f"/category/{c['slug']}/",
            'type': 'category',
        })

    # 3. If still few results, add fuzzy-matched product names
    if len(suggestions) < 4:
        all_names = list(
            Product.objects.filter(is_active=True)
            .values('name', 'price', 'slug', 'category__name')[:200]
        )
        scored = []
        tokens = tokenise(q)
        for p in all_names:
            # Skip already included
            if any(s['label'] == p['name'] for s in suggestions):
                continue
            score = trigram_similarity(q_norm, normalise(p['name']))
            # Boost if any token is a substring
            for t in tokens:
                if t in normalise(p['name']):
                    score += 0.3
            if score >= 0.25:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, p in scored[:4 - len(suggestions)]:
            suggestions.append({
                'label': p['name'],
                'sub': p['category__name'] or '',
                'price': f"ETB {int(p['price']):,}",
                'url': f"/products/{p['slug']}/",
                'type': 'fuzzy',
            })

    return JsonResponse({'suggestions': suggestions[:8], 'query': q})
