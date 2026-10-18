import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class ProductDetailScreen extends StatefulWidget {
  final int productId;
  const ProductDetailScreen({super.key, required this.productId});
  @override
  State<ProductDetailScreen> createState() => _State();
}

class _State extends State<ProductDetailScreen> {
  Product? _product;
  bool _loading = true;
  int _qty = 1;
  int _imgIdx = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final p =
        await context.read<ProductsProvider>().getProduct(widget.productId);
    setState(() {
      _product = p;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading)
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_product == null)
      return const Scaffold(body: Center(child: Text('Product not found')));
    final p = _product!;
    final imgs =
        p.images.isNotEmpty ? p.images : [if (p.imageUrl != null) p.imageUrl!];

    return Scaffold(
      backgroundColor: Colors.white,
      body: CustomScrollView(slivers: [
        SliverAppBar(
          expandedHeight: 320,
          pinned: true,
          backgroundColor: AppTheme.primary,
          flexibleSpace: FlexibleSpaceBar(
            background: Stack(children: [
              PageView.builder(
                itemCount: imgs.isEmpty ? 1 : imgs.length,
                onPageChanged: (i) => setState(() => _imgIdx = i),
                itemBuilder: (_, i) => imgs.isEmpty
                    ? Container(
                        color: const Color(0xFFF1F4F9),
                        child: const Icon(Icons.image_outlined,
                            size: 80, color: Color(0xFFCBD5E1)))
                    : CachedNetworkImage(
                        imageUrl: imgs[i],
                        fit: BoxFit.cover,
                        placeholder: (_, __) =>
                            Container(color: const Color(0xFFF1F4F9))),
              ),
              if (imgs.length > 1)
                Positioned(
                    bottom: 12,
                    left: 0,
                    right: 0,
                    child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                            imgs.length,
                            (i) => Container(
                                margin:
                                    const EdgeInsets.symmetric(horizontal: 3),
                                width: i == _imgIdx ? 16 : 6,
                                height: 6,
                                decoration: BoxDecoration(
                                    color: i == _imgIdx
                                        ? AppTheme.secondary
                                        : Colors.white54,
                                    borderRadius: BorderRadius.circular(3)))))),
              if (p.isFlashDeal)
                Positioned(
                    top: 60,
                    left: 16,
                    child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                            color: AppTheme.secondary,
                            borderRadius: BorderRadius.circular(20)),
                        child: Text(
                            p.discountPct != null
                                ? '-${p.discountPct}% OFF'
                                : '⚡ DEAL',
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.w800)))),
            ]),
          ),
        ),
        SliverToBoxAdapter(
            child: Padding(
          padding: const EdgeInsets.all(20),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (p.categoryName != null)
              Text(p.categoryName!,
                  style:
                      const TextStyle(fontSize: 12, color: AppTheme.textGrey)),
            const SizedBox(height: 4),
            Text(p.name,
                style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textDark)),
            const SizedBox(height: 10),
            Row(children: [
              Text('ETB ${p.price.toStringAsFixed(0)}',
                  style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.secondary)),
              if (p.originalPrice != null) ...[
                const SizedBox(width: 10),
                Text('ETB ${p.originalPrice!.toStringAsFixed(0)}',
                    style: const TextStyle(
                        fontSize: 16,
                        color: AppTheme.textGrey,
                        decoration: TextDecoration.lineThrough)),
              ],
            ]),
            const SizedBox(height: 10),
            Row(children: [
              Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                      color: p.stock > 0
                          ? const Color(0xFFE6F7E6)
                          : const Color(0xFFFEF3F3),
                      borderRadius: BorderRadius.circular(20)),
                  child: Text(
                      p.stock > 0
                          ? '✓ In Stock (${p.stock})'
                          : '✗ Out of Stock',
                      style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: p.stock > 0
                              ? AppTheme.accent
                              : AppTheme.secondary))),
            ]),
            if (p.description != null && p.description!.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text('Description',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              Text(p.description!,
                  style: const TextStyle(
                      fontSize: 14, color: AppTheme.textGrey, height: 1.6)),
            ],
            const SizedBox(height: 20),
            // Qty selector
            Row(children: [
              const Text('Quantity:',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const Spacer(),
              Container(
                decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xFFEEF2F6)),
                    borderRadius: BorderRadius.circular(8)),
                child: Row(children: [
                  IconButton(
                      icon: const Icon(Icons.remove, size: 18),
                      onPressed: () =>
                          setState(() => _qty = (_qty - 1).clamp(1, 99))),
                  Text('$_qty',
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w700)),
                  IconButton(
                      icon: const Icon(Icons.add, size: 18),
                      onPressed: () =>
                          setState(() => _qty = (_qty + 1).clamp(1, 99))),
                ]),
              ),
            ]),
            const SizedBox(height: 80),
          ]),
        )),
      ]),
      bottomNavigationBar: p.stock > 0
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                child: Row(children: [
                  Expanded(
                      child: ElevatedButton.icon(
                    onPressed: () {
                      context.read<CartProvider>().add(p, qty: _qty);
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                          content: Text('Added to cart'),
                          backgroundColor: AppTheme.accent,
                          duration: Duration(seconds: 1)));
                    },
                    icon: const Icon(Icons.shopping_cart_outlined),
                    label: const Text('Add to Cart'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        padding: const EdgeInsets.symmetric(vertical: 14)),
                  )),
                  const SizedBox(width: 12),
                  Expanded(
                      child: ElevatedButton(
                    onPressed: () => Navigator.pushNamed(context, '/cart'),
                    child: const Text('Buy Now'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.secondary,
                        padding: const EdgeInsets.symmetric(vertical: 14)),
                  )),
                ]),
              ),
            )
          : null,
    );
  }
}
