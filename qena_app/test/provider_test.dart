import 'package:flutter_test/flutter_test.dart';
import 'package:qena_app/core/constants.dart';
import 'package:qena_app/core/models.dart';
import 'package:qena_app/core/providers.dart';

void main() {
  group('1. CartProvider Unit Tests', () {
    late CartProvider cart;
    final testProduct1 = Product(
      id: 1,
      name: 'Samsung Galaxy S24 Ultra',
      slug: 'samsung-galaxy-s24-ultra',
      price: 95000.0,
      originalPrice: 110000.0,
      discountPct: 14,
      vendorName: 'Alex Electronics',
      stock: 10,
      images: ['https://example.com/s24.jpg'],
      categoryName: 'Electronics',
    );

    final testProduct2 = Product(
      id: 2,
      name: 'Ethiopian Traditional Habesha Kemis',
      slug: 'habesha-kemis',
      price: 8500.0,
      originalPrice: 10000.0,
      discountPct: 15,
      vendorName: 'Habesha Fashion',
      stock: 5,
      images: ['https://example.com/kemis.jpg'],
      categoryName: 'Fashion',
    );

    setUp(() {
      cart = CartProvider();
    });

    test('Initial cart is empty with zero count and total', () {
      expect(cart.items, isEmpty);
      expect(cart.count, 0);
      expect(cart.total, 0.0);
    });

    test('Add item increments count and computes correct total', () {
      cart.add(testProduct1, qty: 1);
      expect(cart.items.length, 1);
      expect(cart.count, 1);
      expect(cart.total, 95000.0);

      // Add same item again
      cart.add(testProduct1, qty: 2);
      expect(cart.items.length, 1);
      expect(cart.count, 3);
      expect(cart.total, 285000.0);
    });

    test('Add distinct products updates items list and combined total', () {
      cart.add(testProduct1, qty: 1);
      cart.add(testProduct2, qty: 2);
      expect(cart.items.length, 2);
      expect(cart.count, 3);
      expect(cart.total, 95000.0 + (8500.0 * 2));
    });

    test('Update quantity modifies quantity and removes at 0 quantity', () {
      cart.add(testProduct1, qty: 2);
      cart.updateQty(testProduct1.id, 5);
      expect(cart.count, 5);
      expect(cart.total, 95000.0 * 5);

      cart.updateQty(testProduct1.id, 0);
      expect(cart.items, isEmpty);
      expect(cart.count, 0);
    });

    test('Remove product by ID removes only the target item', () {
      cart.add(testProduct1, qty: 1);
      cart.add(testProduct2, qty: 1);
      expect(cart.items.length, 2);

      cart.remove(testProduct1.id);
      expect(cart.items.length, 1);
      expect(cart.items.first.product.id, testProduct2.id);
      expect(cart.total, 8500.0);
    });

    test('Clear empties all cart items', () {
      cart.add(testProduct1, qty: 2);
      cart.add(testProduct2, qty: 3);
      expect(cart.count, 5);

      cart.clear();
      expect(cart.items, isEmpty);
      expect(cart.count, 0);
      expect(cart.total, 0.0);
    });
  });

  group('2. Model Deserialization Tests', () {
    test('Product.fromJson parses correctly', () {
      final json = {
        'id': 101,
        'name': 'Sony WH-1000XM5 Headphones',
        'slug': 'sony-wh-1000xm5',
        'price': '42000.00',
        'original_price': '48000.00',
        'discount_pct': 12,
        'vendor_name': 'Alex Electronics',
        'category_name': 'Audio & Video',
        'stock': 12,
        'is_featured': true,
        'is_flash_deal': false,
        'images': ['https://example.com/sony.jpg'],
        'description': 'Industry-leading noise cancelling wireless headphones.',
      };

      final product = Product.fromJson(json);
      expect(product.id, 101);
      expect(product.name, 'Sony WH-1000XM5 Headphones');
      expect(product.price, 42000.0);
      expect(product.originalPrice, 48000.0);
      expect(product.vendorName, 'Alex Electronics');
      expect(product.categoryName, 'Audio & Video');
      expect(product.isFeatured, isTrue);
      expect(product.stock, 12);
    });

    test('Vendor.fromJson parses custom domain and metadata', () {
      final json = {
        'id': 4,
        'store_name': 'Alex Electronics',
        'slug': 'alex',
        'tier': 'gold',
        'description': 'Official Alex Electronics Flagship store',
        'custom_domain': 'alex.com',
        'phone': '+251911223344',
        'products_count': 45,
      };

      final vendor = Vendor.fromJson(json);
      expect(vendor.id, 4);
      expect(vendor.storeName, 'Alex Electronics');
      expect(vendor.slug, 'alex');
      expect(vendor.customDomain, 'alex.com');
      expect(vendor.tier, 'gold');
    });

    test('Order & OrderItem deserialization', () {
      final json = {
        'id': 5001,
        'order_number': 'ORD-2026-9921',
        'status': 'Processing',
        'status_display': 'Processing Delivery',
        'total': '95500.00',
        'shipping_name': 'Abebe Bikila',
        'payment_method': 'telebirr',
        'created_at': '2026-09-20T12:00:00Z',
        'items': [
          {
            'id': 1,
            'product_name': 'Samsung Galaxy S24 Ultra',
            'product_price': '95000.00',
            'subtotal': '95000.00',
            'quantity': 1,
            'product_image': 'https://example.com/s24.jpg',
          }
        ],
      };

      final order = Order.fromJson(json);
      expect(order.id, 5001);
      expect(order.orderNumber, 'ORD-2026-9921');
      expect(order.status, 'Processing');
      expect(order.total, 95500.0);
      expect(order.shippingName, 'Abebe Bikila');
      expect(order.paymentMethod, 'telebirr');
      expect(order.items.length, 1);
      expect(order.items.first.productName, 'Samsung Galaxy S24 Ultra');
    });

    test('LiveStream model parses correctly', () {
      final json = {
        'stream_id': 'alex-live-01',
        'title': '🔴 Live Unboxing & Sale',
        'status': 'live',
        'status_display': 'Live Now',
        'vendor_name': 'Alex Electronics',
        'total_views': 350,
        'total_likes': 120,
        'total_messages': 45,
      };

      final stream = LiveStream.fromJson(json);
      expect(stream.id, 'alex-live-01');
      expect(stream.title, '🔴 Live Unboxing & Sale');
      expect(stream.isLive, isTrue);
      expect(stream.vendorName, 'Alex Electronics');
      expect(stream.views, 350);
    });
  });

  group('3. AppConstants Tests', () {
    test('Currency and branding constants', () {
      expect(AppConstants.appName, 'Qenagebeya');
      expect(AppConstants.currency, 'ETB');
      expect(AppConstants.apiBase, 'http://localhost:8000/api/v1');
    });
  });
}
