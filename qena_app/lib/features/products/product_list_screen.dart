import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/product_card.dart';
import 'product_detail_screen.dart';

class ProductListScreen extends StatefulWidget {
  final String? categorySlug, title, searchQuery, vendorSlug;
  final bool featuredOnly, flashOnly;
  const ProductListScreen({
    super.key,
    this.categorySlug,
    this.title,
    this.searchQuery,
    this.vendorSlug,
    this.featuredOnly = false,
    this.flashOnly = false,
  });
  @override
  State<ProductListScreen> createState() => _State();
}

class _State extends State<ProductListScreen> {
  List<Product> _products = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final p = context.read<ProductsProvider>();
    final list = await p.getProducts(
      category: widget.categorySlug,
      vendor: widget.vendorSlug,
      featured: widget.featuredOnly ? true : null,
      flash: widget.flashOnly ? true : null,
      search: widget.searchQuery,
    );
    setState(() {
      _products = list;
      _loading = false;
    });
  }

  void _sortProducts(String sort) {
    setState(() {
      if (sort == 'price') {
        _products.sort((a, b) => a.price.compareTo(b.price));
      } else if (sort == '-price') {
        _products.sort((a, b) => b.price.compareTo(a.price));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final String title = widget.title ??
        (widget.searchQuery != null
            ? 'Results for "${widget.searchQuery}"'
            : widget.flashOnly
                ? '⚡ Flash Deals'
                : widget.featuredOnly
                    ? '⭐ Featured'
                    : 'All Products');

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort, color: Colors.white),
            onSelected: _sortProducts,
            itemBuilder: (_) => const [
              PopupMenuItem(value: '-created_at', child: Text('Newest First')),
              PopupMenuItem(value: 'price', child: Text('Price: Low to High')),
              PopupMenuItem(value: '-price', child: Text('Price: High to Low')),
            ],
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _products.isEmpty
          ? const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.search_off, size: 64, color: AppTheme.textGrey),
                  SizedBox(height: 12),
                  Text(
                    'No products found',
                    style: TextStyle(color: AppTheme.textGrey, fontSize: 16),
                  ),
                ],
              ),
            )
          : GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 0.65,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: _products.length,
              itemBuilder: (_, i) => ProductCard(
                product: _products[i],
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        ProductDetailScreen(productId: _products[i].id),
                  ),
                ),
              ),
            ),
    );
  }
}
