"""
test_live_http_server.py — Live server test sending real HTTP requests to localhost:8000 with custom Host headers.
"""
import urllib.request
import urllib.parse
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"

def test_request(host_header, path="/", method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {
        'Host': host_header,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TestClient/1.0',
    }
    req = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            return resp.status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8', errors='replace') if e.fp else ''
        return e.code, content
    except Exception as e:
        return None, str(e)

def main():
    print("="*75)
    print(" 🌐 LIVE HTTP DUAL-ACCESS VERIFICATION (PORT 8000)")
    print("="*75)
    passed = 0
    failed = 0

    def check(title, status, expected_text, body):
        nonlocal passed, failed
        if status == 200 and expected_text in body:
            print(f"  [PASS] {title}")
            print(f"         Status: {status} | Verified: '{expected_text}'")
            passed += 1
        else:
            print(f"  [FAIL] {title}")
            print(f"         Status: {status} | Expected: '{expected_text}'")
            if body:
                print(f"         Body preview: {body[:150]}")
            failed += 1

    # 1. Marketplace Home
    st, b = test_request("qenagebeya.com", "/")
    check("Marketplace Home (Host: qenagebeya.com)", st, "Qenagebeya", b)

    # 2. Marketplace Global Search finding Alex's product
    st, b = test_request("qenagebeya.com", "/products/?q=Alex")
    check("Marketplace Search for Alex (Host: qenagebeya.com)", st, "Alex 5G Pro Smartphone", b)

    # 3. Marketplace Store profile for Alex linking to alex.com
    st, b = test_request("qenagebeya.com", "/vendor/store/alex/")
    check("Marketplace Store Page (Host: qenagebeya.com)", st, "alex.com", b)

    # 4. Standalone Storefront Home on alex.com
    st, b = test_request("alex.com", "/")
    check("Storefront Home (Host: alex.com)", st, "Alex Electronics", b)

    # 5. Standalone Storefront Products Grid on alex.com
    st, b = test_request("alex.com", "/")
    check("Storefront Product Catalog on alex.com", st, "Alex Ultra ANC", b)

    # 6. Standalone Storefront About Page on alex.com
    st, b = test_request("alex.com", "/about/")
    check("Storefront About Page (Host: alex.com)", st, "About Alex Electronics", b)

    # 7. Standalone Storefront Contact Page on alex.com
    st, b = test_request("alex.com", "/contact/")
    check("Storefront Contact Page (Host: alex.com)", st, "Get In Touch", b)

    # 8. Standalone Storefront Cart Page on alex.com
    st, b = test_request("alex.com", "/cart/")
    check("Storefront Cart Page (Host: alex.com)", st, "Shopping Cart", b)

    # 9. Subdomain on Localhost (alex.localhost)
    st, b = test_request("alex.localhost", "/")
    check("Subdomain Localhost (Host: alex.localhost)", st, "Alex Electronics", b)

    # 10. Subdomain on Wildcard Production (alex.qenagebeya.com)
    st, b = test_request("alex.qenagebeya.com", "/")
    check("Subdomain Wildcard (Host: alex.qenagebeya.com)", st, "Alex Electronics", b)

    # 11. WWW Domain Alias (www.alex.com)
    st, b = test_request("www.alex.com", "/")
    check("WWW Alias (Host: www.alex.com)", st, "Alex Electronics", b)

    print("\n" + "="*75)
    print(f" LIVE TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {passed+failed})")
    print("="*75)
    return failed == 0

if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
