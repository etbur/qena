import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({super.key});
  @override
  State<OrdersScreen> createState() => _State();
}

class _State extends State<OrdersScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      if (auth.isLoggedIn) context.read<OrdersProvider>().loadOrders();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn)
      return Scaffold(
        appBar: AppBar(title: const Text('My Orders')),
        body: Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.lock_outline, size: 64, color: AppTheme.textGrey),
          const SizedBox(height: 16),
          const Text('Login to view orders',
              style: TextStyle(fontSize: 16, color: AppTheme.textGrey)),
          const SizedBox(height: 20),
          ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/login'),
              child: const Text('Login')),
        ])),
      );

    return Scaffold(
      appBar: AppBar(title: const Text('My Orders')),
      body: Consumer<OrdersProvider>(builder: (_, o, __) {
        if (o.loading) return const Center(child: CircularProgressIndicator());
        if (o.orders.isEmpty)
          return const Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.inbox_outlined, size: 64, color: AppTheme.textGrey),
            SizedBox(height: 12),
            Text('No orders yet',
                style: TextStyle(fontSize: 16, color: AppTheme.textGrey)),
          ]));
        return ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: o.orders.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (_, i) => _OrderCard(order: o.orders[i]),
        );
      }),
    );
  }
}

class _OrderCard extends StatelessWidget {
  final Order order;
  const _OrderCard({required this.order});

  Color _statusColor() =>
      {
        'delivered': AppTheme.accent,
        'shipped': const Color(0xFF1A4B8A),
        'processing': const Color(0xFFB85A1A),
        'pending': AppTheme.secondary,
        'cancelled': AppTheme.textGrey,
      }[order.status] ??
      AppTheme.textGrey;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFEEF2F6))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text('#${order.orderNumber}',
                style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: AppTheme.primary)),
            const Spacer(),
            Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                    color: _statusColor().withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20)),
                child: Text(order.statusDisplay,
                    style: TextStyle(
                        color: _statusColor(),
                        fontSize: 12,
                        fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 8),
          Text(
              '${order.items.length} item${order.items.length != 1 ? "s" : ""}',
              style: const TextStyle(color: AppTheme.textGrey, fontSize: 13)),
          const SizedBox(height: 4),
          Row(children: [
            Text('Total: ',
                style: const TextStyle(color: AppTheme.textGrey, fontSize: 13)),
            Text('ETB ${order.total.toStringAsFixed(0)}',
                style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: AppTheme.secondary)),
            const Spacer(),
            Text(
                order.createdAt.length > 10
                    ? order.createdAt.substring(0, 10)
                    : order.createdAt,
                style: const TextStyle(color: AppTheme.textGrey, fontSize: 12)),
          ]),
        ]),
      );
}
