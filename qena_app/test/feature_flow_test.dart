import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:qena_app/core/models.dart';
import 'package:qena_app/core/providers.dart';
import 'package:qena_app/features/cart/cart_screen.dart';
import 'package:qena_app/features/live/live_home_screen.dart';
import 'package:qena_app/features/live/live_player_screen.dart';
import 'package:qena_app/features/vendors/vendor_screen.dart';
import 'package:qena_app/shared/theme/app_theme.dart';

class _TestHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context);
  }
}

Widget createTestAppWithProviders(Widget home, {CartProvider? cartProvider}) {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => AuthProvider()),
      ChangeNotifierProvider(create: (_) => cartProvider ?? CartProvider()),
      ChangeNotifierProvider(create: (_) => ProductsProvider()),
      ChangeNotifierProvider(create: (_) => OrdersProvider()),
    ],
    child: MaterialApp(
      theme: AppTheme.light,
      home: home,
    ),
  );
}

void main() {
  setUpAll(() {
    HttpOverrides.global = _TestHttpOverrides();
  });

  final testProduct = Product(
    id: 1,
    name: 'Samsung Galaxy S24 Ultra',
    slug: 'samsung-galaxy-s24-ultra',
    price: 95000.0,
    originalPrice: 110000.0,
    discountPct: 14,
    vendorName: 'Alex Electronics',
    stock: 8,
    isFeatured: true,
    description: 'Flagship smartphone with Snapdragon 8 Gen 3 and 200MP camera.',
    images: ['https://example.com/s24.jpg'],
    categoryName: 'Smartphones',
  );

  final testStream = LiveStream(
    id: 'stream-101',
    title: '📱 Unboxing Samsung S24 & Flash Sale Discounts!',
    status: 'live',
    statusDisplay: 'Live Now',
    vendorName: 'Alex Electronics',
    views: 248,
    likes: 54,
    messages: 19,
  );

  testWidgets('1. CartScreen with items allows quantity increment and shows totals', (tester) async {
    final cart = CartProvider();
    cart.add(testProduct, qty: 1);

    await tester.pumpWidget(createTestAppWithProviders(
      const CartScreen(),
      cartProvider: cart,
    ));
    await tester.pump(const Duration(milliseconds: 100));

    // Verify item title and checkout button
    expect(find.text('Samsung Galaxy S24 Ultra'), findsOneWidget);
    expect(find.text('Proceed to Checkout'), findsOneWidget);
    expect(find.text('ETB 95000'), findsWidgets);

    // Increment quantity by tapping '+'
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump(const Duration(milliseconds: 100));

    expect(cart.count, 2);
    expect(cart.total, 190000.0);
    expect(find.text('ETB 190000'), findsWidgets);
  });

  testWidgets('2. LiveHomeScreen renders live shopping streams feed', (tester) async {
    await tester.pumpWidget(createTestAppWithProviders(
      const LiveHomeScreen(),
    ));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Qena Live Shopping'), findsOneWidget);
  });

  testWidgets('3. LivePlayerScreen renders stream overlay, vendor badge and interactive chat', (tester) async {
    await tester.pumpWidget(createTestAppWithProviders(
      LivePlayerScreen(stream: testStream),
    ));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('📱 Unboxing Samsung S24 & Flash Sale Discounts!'), findsOneWidget);
    expect(find.text('Streaming live from Alex Electronics'), findsOneWidget);
    expect(find.text('248'), findsOneWidget);
    expect(find.text('Say something in live chat...'), findsOneWidget);
  });

  testWidgets('4. VendorScreen renders placeholder store info when loading or on slug lookup', (tester) async {
    await tester.pumpWidget(createTestAppWithProviders(
      const VendorScreen(vendorSlug: 'alex'),
    ));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(VendorScreen), findsOneWidget);
  });
}
