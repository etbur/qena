import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:qena_app/core/providers.dart';
import 'package:qena_app/features/cart/cart_screen.dart';
import 'package:qena_app/features/categories/categories_screen.dart';
import 'package:qena_app/features/orders/checkout_screen.dart';
import 'package:qena_app/features/orders/orders_screen.dart';
import 'package:qena_app/features/profile/profile_screen.dart';
import 'package:qena_app/features/auth/login_screen.dart';
import 'package:qena_app/features/auth/register_screen.dart';
import 'package:qena_app/features/shell/main_navigation_shell.dart';
import 'package:qena_app/shared/theme/app_theme.dart';

class _TestHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context);
  }
}

Widget createTestApp(Widget home) {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider(create: (_) => AuthProvider()),
      ChangeNotifierProvider(create: (_) => CartProvider()),
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

  testWidgets('1. Navigation Shell renders 5 bottom tabs', (tester) async {
    await tester.pumpWidget(createTestApp(const MainNavigationShell()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Categories'), findsOneWidget);
    expect(find.text('Live'), findsOneWidget);
    expect(find.text('Cart'), findsOneWidget);
    expect(find.text('Account'), findsOneWidget);
  });

  testWidgets('2. CartScreen empty state and elements render', (tester) async {
    await tester.pumpWidget(createTestApp(const CartScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Shopping Cart'), findsOneWidget);
    expect(find.text('Your cart is empty'), findsOneWidget);
    expect(find.text('Start Shopping'), findsOneWidget);
  });

  testWidgets('3. CheckoutScreen renders delivery & payment methods', (tester) async {
    await tester.pumpWidget(createTestApp(const CheckoutScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Checkout & Delivery'), findsOneWidget);
    expect(find.text('📍 Shipping Address'), findsOneWidget);
    expect(find.text('💳 Payment Method'), findsOneWidget);
    expect(find.text('Telebirr SuperApp'), findsOneWidget);
    expect(find.text('CBE Birr'), findsOneWidget);
  });

  testWidgets('4. OrdersScreen empty state and header render', (tester) async {
    await tester.pumpWidget(createTestApp(const OrdersScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('My Orders'), findsOneWidget);
  });

  testWidgets('5. CategoriesScreen renders header', (tester) async {
    await tester.pumpWidget(createTestApp(const CategoriesScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Browse Categories'), findsOneWidget);
  });

  testWidgets('6. ProfileScreen renders user actions and language options', (tester) async {
    await tester.pumpWidget(createTestApp(const ProfileScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('My Account'), findsOneWidget);
    expect(find.text('Sign In / Register'), findsOneWidget);
    expect(find.text('Language / ቋንቋ'), findsOneWidget);
    expect(find.text('Customer Support'), findsOneWidget);
  });

  testWidgets('7. LoginScreen renders sign in form', (tester) async {
    await tester.pumpWidget(createTestApp(const LoginScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Welcome to Qenagebeya'), findsOneWidget);
    expect(find.text('Username or Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Sign In'), findsOneWidget);
    expect(find.text('Create Account'), findsOneWidget);
  });

  testWidgets('8. RegisterScreen renders customer registration form', (tester) async {
    await tester.pumpWidget(createTestApp(const RegisterScreen()));
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Create Customer Account'), findsOneWidget);
    expect(find.text('Join Qenagebeya Today'), findsOneWidget);
    expect(find.text('First Name *'), findsOneWidget);
    expect(find.text('Last Name *'), findsOneWidget);
    expect(find.text('Email Address *'), findsOneWidget);
  });
}
