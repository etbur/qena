import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';
import '../orders/checkout_screen.dart';

class CartScreen extends StatelessWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Cart')),
      body: Consumer<CartProvider>(builder: (_, cart, __) {
        if (cart.items.isEmpty)
          return const Center(
              child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.shopping_cart_outlined,
                  size: 80, color: AppTheme.textGrey),
              SizedBox(height: 16),
              Text('Your cart is empty',
                  style: TextStyle(
                      fontSize: 18,
                      color: AppTheme.textGrey,
                      fontWeight: FontWeight.w600)),
              SizedBox(height: 8),
              Text('Add some products to get started',
                  style: TextStyle(color: AppTheme.textGrey)),
            ],
          ));
        return Column(children: [
          Expanded(
              child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: cart.items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (_, i) {
              final item = cart.items[i];
              return Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFEEF2F6))),
                child: Row(children: [
                  ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: item.product.imageUrl != null
                          ? CachedNetworkImage(
                              imageUrl: item.product.imageUrl!,
                              width: 72,
                              height: 72,
                              fit: BoxFit.cover)
                          : Container(
                              width: 72,
                              height: 72,
                              color: const Color(0xFFF1F4F9),
                              child: const Icon(Icons.image_outlined,
                                  color: AppTheme.textGrey))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                        Text(item.product.name,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                                fontWeight: FontWeight.w600, fontSize: 14)),
                        const SizedBox(height: 4),
                        Text('ETB ${item.product.price.toStringAsFixed(0)}',
                            style: const TextStyle(
                                color: AppTheme.secondary,
                                fontWeight: FontWeight.w700)),
                      ])),
                  Column(children: [
                    Row(children: [
                      _qtyBtn(
                          Icons.remove,
                          () => cart.updateQty(
                              item.product.id, item.quantity - 1)),
                      Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text('${item.quantity}',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w700, fontSize: 16))),
                      _qtyBtn(
                          Icons.add,
                          () => cart.updateQty(
                              item.product.id, item.quantity + 1)),
                    ]),
                    const SizedBox(height: 6),
                    Text('ETB ${item.subtotal.toStringAsFixed(0)}',
                        style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            color: AppTheme.primary)),
                    TextButton(
                        onPressed: () => cart.remove(item.product.id),
                        child: const Text('Remove',
                            style: TextStyle(
                                color: AppTheme.secondary, fontSize: 12))),
                  ]),
                ]),
              );
            },
          )),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Color(0xFFEEF2F6)))),
            child: SafeArea(
                child: Column(children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                const Text('Total:',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                Text('ETB ${cart.total.toStringAsFixed(0)}',
                    style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.secondary)),
              ]),
              const SizedBox(height: 14),
              SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => const CheckoutScreen())),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.secondary,
                        padding: const EdgeInsets.symmetric(vertical: 16)),
                    child: const Text('Checkout · ዕዳ ክፈል',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w800)),
                  )),
            ])),
          ),
        ]);
      }),
    );
  }

  Widget _qtyBtn(IconData icon, VoidCallback onPressed) => GestureDetector(
        onTap: onPressed,
        child: Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFEEF2F6)),
                borderRadius: BorderRadius.circular(6)),
            child: Icon(icon, size: 16)),
      );
}
