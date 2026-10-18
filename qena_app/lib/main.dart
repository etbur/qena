import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/providers.dart';
import 'shared/theme/app_theme.dart';
import 'features/home/home_screen.dart';
import 'features/cart/cart_screen.dart';
import 'features/orders/orders_screen.dart';
import 'features/live/live_home_screen.dart';
import 'features/profile/profile_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/register_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final auth = AuthProvider();
  await auth.init();
  runApp(
    MultiProvider(providers: [
      ChangeNotifierProvider.value(value: auth),
      ChangeNotifierProvider(create: (_) => CartProvider()),
      ChangeNotifierProvider(create: (_) => ProductsProvider()),
      ChangeNotifierProvider(create: (_) => OrdersProvider()),
    ], child: const QenaApp()),
  );
}

class QenaApp extends StatelessWidget {
  const QenaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Qenagebeya',
      theme: AppTheme.light,
      debugShowCheckedModeBanner: false,
      initialRoute: '/',
      routes: {
        '/': (_) => const MainShell(),
        '/cart': (_) => const CartScreen(),
        '/orders': (_) => const OrdersScreen(),
        '/login': (_) => const LoginScreen(),
        '/register': (_) => const RegisterScreen(),
        '/live': (_) => const LiveHomeScreen(),
      },
    );
  }
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _tab = 0;

  final _screens = const [
    HomeScreen(),
    LiveHomeScreen(),
    OrdersScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _tab, children: _screens),
      bottomNavigationBar: Consumer<CartProvider>(
        builder: (_, cart, __) => BottomNavigationBar(
          currentIndex: _tab,
          onTap: (i) => setState(() => _tab = i),
          items: [
            const BottomNavigationBarItem(
                icon: Icon(Icons.home_outlined),
                activeIcon: Icon(Icons.home),
                label: 'Home'),
            const BottomNavigationBarItem(
                icon: Icon(Icons.live_tv_outlined),
                activeIcon: Icon(Icons.live_tv),
                label: 'Live'),
            BottomNavigationBarItem(
              icon: Stack(clipBehavior: Clip.none, children: [
                const Icon(Icons.shopping_bag_outlined),
                if (cart.count > 0)
                  Positioned(
                      right: -4,
                      top: -4,
                      child: Container(
                          width: 14,
                          height: 14,
                          decoration: const BoxDecoration(
                              color: AppTheme.secondary,
                              shape: BoxShape.circle),
                          child: Center(
                              child: Text('${cart.count}',
                                  style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 9,
                                      fontWeight: FontWeight.w800))))),
              ]),
              activeIcon: const Icon(Icons.shopping_bag),
              label: 'Orders',
            ),
            const BottomNavigationBarItem(
                icon: Icon(Icons.person_outline),
                activeIcon: Icon(Icons.person),
                label: 'Profile'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.secondary,
        onPressed: () => Navigator.pushNamed(context, '/cart'),
        child: Stack(clipBehavior: Clip.none, children: [
          const Icon(Icons.shopping_cart_outlined, color: Colors.white),
          Consumer<CartProvider>(
              builder: (_, cart, __) => cart.count > 0
                  ? Positioned(
                      right: -4,
                      top: -4,
                      child: Container(
                          width: 16,
                          height: 16,
                          decoration: const BoxDecoration(
                              color: Colors.white, shape: BoxShape.circle),
                          child: Center(
                              child: Text('${cart.count}',
                                  style: const TextStyle(
                                      color: AppTheme.secondary,
                                      fontSize: 9,
                                      fontWeight: FontWeight.w900)))))
                  : const SizedBox.shrink()),
        ]),
      ),
    );
  }
}
