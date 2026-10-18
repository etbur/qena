import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
django.setup()

from django.test import Client
from store.models import Product, Category

def run_tests():
    c = Client()
    
    print("Testing /try-on/ ...")
    res = c.get('/try-on/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Virtual Try-On Fitting Room" in res.content, "Studio title missing"
    print("-> /try-on/ OK!")
    
    print("Testing /try-on/habesha-kemis-white-gold/ ...")
    res2 = c.get('/try-on/habesha-kemis-white-gold/')
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}"
    assert b"Habesha Kemis" in res2.content, "Preselected item missing in studio"
    print("-> /try-on/habesha-kemis-white-gold/ OK!")
    
    print("Testing /api/try-on/items/ ...")
    res3 = c.get('/api/try-on/items/')
    assert res3.status_code == 200, f"Expected 200, got {res3.status_code}"
    data = res3.json()
    assert data.get('success') is True, "API success flag missing"
    assert len(data.get('items', [])) > 0, "No items returned by try on api"
    print(f"-> /api/try-on/items/ returned {len(data['items'])} items. OK!")

    print("Testing Fashion Product Detail page for Try-On button ...")
    p = Product.objects.filter(slug='habesha-kemis-white-gold').first()
    if p:
        assert p.is_try_on_eligible, "Product should be try_on_eligible"
        res4 = c.get(p.get_absolute_url())
        assert res4.status_code == 200
        assert b"Try-On" in res4.content
        assert b"Virtual Fitting Room" in res4.content
        print("-> Product detail try-on buttons OK!")

    print("Testing Fashion Category page for Try-On banner ...")
    cat = Category.objects.filter(slug='fashion-habesha').first()
    if cat:
        res5 = c.get(cat.get_absolute_url())
        assert res5.status_code == 200
        assert b"Virtual Try-On Studio" in res5.content
        print("-> Category page try-on banner OK!")

    print("\nALL VIRTUAL TRY-ON TESTS PASSED SUCCESSFULLY! [ET][STAR]")

if __name__ == '__main__':
    run_tests()
