import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shimmer/shimmer.dart';
import '../../core/models.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/product_card.dart';
import '../products/product_detail_screen.dart';
import '../products/product_list_screen.dart';
import '../live/live_home_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ProductsProvider>().loadHome();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: CustomScrollView(
        slivers: [
          // ── App bar ────────────────────────────────────────────────────
          SliverAppBar(
            floating: true,
            pinned: true,
            backgroundColor: AppTheme.primary,
            title: const Row(
              children: [
                Text(
                  '🇪🇹',
                  style: TextStyle(fontSize: 22),
                ),
                SizedBox(width: 8),
                Text(
                  'Qenagebeya',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            actions: [
              Consumer<CartProvider>(
                builder: (_, cart, __) => Stack(
                  children: [
                    IconButton(
                      icon: const Icon(
                        Icons.shopping_cart_outlined,
                        color: Colors.white,
                      ),
                      onPressed: () =>
                          Navigator.pushNamed(context, '/cart'),
                    ),
                    if (cart.count > 0)
                      Positioned(
                        right: 6,
                        top: 6,
                        child: Container(
                          width: 16,
                          height: 16,
                          decoration: const BoxDecoration(
                            color: AppTheme.secondary,
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              '${cart.count}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(56),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                child: TextField(
                  controller: _search,
                  onSubmitted: (q) => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ProductListScreen(searchQuery: q),
                    ),
                  ),
                  decoration: InputDecoration(
                    hintText: 'Search products, vendors…',
                    hintStyle: const TextStyle(
                      color: Color(0x99FFFFFF),
                      fontSize: 13,
                    ),
                    prefixIcon: const Icon(
                      Icons.search,
                      color: Colors.white60,
                      size: 20,
                    ),
                    filled: true,
                    fillColor: Colors.white.withOpacity(0.12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(60),
                      borderSide: BorderSide.none,
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(60),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                  ),
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                ),
              ),
            ),
          ),

          // ── Content ────────────────────────────────────────────────────
          SliverToBoxAdapter(
            child: Consumer<ProductsProvider>(
              builder: (_, p, __) {
                if (p.loading) return _buildShimmer();
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Live banner
                    if (p.liveNow.isNotEmpty)
                      _buildLiveBanner(context, p.liveNow.first),
                    // Categories
                    _sectionHeader(
                      context,
                      '🗂 Categories',
                      () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const ProductListScreen(),
                        ),
                      ),
                    ),
                    _buildCategories(context, p.categories),
                    // Flash deals
                    if (p.flash.isNotEmpty) ...[
                      _sectionHeader(
                        context,
                        '⚡ Flash Deals',
                        () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                const ProductListScreen(flashOnly: true),
                          ),
                        ),
                      ),
                      _buildProductSlider(context, p.flash),
                    ],
                    // Featured
                    if (p.featured.isNotEmpty) ...[
                      _sectionHeader(
                        context,
                        '⭐ Featured',
                        () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                const ProductListScreen(featuredOnly: true),
                          ),
                        ),
                      ),
                      _buildProductGrid(context, p.featured.take(6).toList()),
                    ],
                    // New arrivals
                    _sectionHeader(
                      context,
                      '🆕 New Arrivals',
                      () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const ProductListScreen(),
                        ),
                      ),
                    ),
                    _buildProductGrid(context, p.newArr.take(8).toList()),
                    const SizedBox(height: 24),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveBanner(BuildContext context, LiveStream s) =>
      GestureDetector(
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const LiveHomeScreen()),
        ),
        child: Container(
          margin: const EdgeInsets.all(16),
          height: 100,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.primary, AppTheme.secondary],
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            children: [
              const SizedBox(width: 16),
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              const Text(
                'LIVE',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      s.vendorName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        fontSize: 14,
                      ),
                    ),
                    Text(
                      'Watch now · ${s.views} viewers',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.play_circle_fill, color: Colors.white, size: 36),
              const SizedBox(width: 16),
            ],
          ),
        ),
      );

  Widget _sectionHeader(
    BuildContext context,
    String title,
    VoidCallback onMore,
  ) => Padding(
    padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
    child: Row(
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w800,
            color: AppTheme.textDark,
          ),
        ),
        const Spacer(),
        GestureDetector(
          onTap: onMore,
          child: const Text(
            'View all',
            style: TextStyle(
              fontSize: 13,
              color: AppTheme.secondary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    ),
  );

  Widget _buildCategories(BuildContext ctx, List<Category> cats) => SizedBox(
    height: 80,
    child: ListView.separated(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: cats.length,
      separatorBuilder: (_, __) => const SizedBox(width: 12),
      itemBuilder: (_, i) {
        final c = cats[i];
        return GestureDetector(
          onTap: () => Navigator.push(
            ctx,
            MaterialPageRoute(
              builder: (_) =>
                  ProductListScreen(categorySlug: c.slug, title: c.name),
            ),
          ),
          child: Column(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFEEF2F6)),
                ),
                child: c.imageUrl != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(13),
                        child: CachedNetworkImage(
                          imageUrl: c.imageUrl!,
                          fit: BoxFit.cover,
                        ),
                      )
                    : const Icon(
                        Icons.category_outlined,
                        color: AppTheme.primary,
                        size: 24,
                      ),
              ),
              const SizedBox(height: 4),
              Text(
                c.name,
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textDark,
                ),
              ),
            ],
          ),
        );
      },
    ),
  );

  Widget _buildProductSlider(BuildContext ctx, List<Product> products) =>
      SizedBox(
        height: 280,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 10),
          itemCount: products.length,
          itemBuilder: (ctx, i) {
            final p = products[i];
            return Container(
              width: 175,
              margin: const EdgeInsets.symmetric(horizontal: 6),
              child: ProductCard(
                product: p,
                onTap: () => Navigator.push(
                  ctx,
                  MaterialPageRoute(
                    builder: (_) => ProductDetailScreen(productId: p.id),
                  ),
                ),
              ),
            );
          },
        ),
      );

  Widget _buildProductGrid(BuildContext ctx, List<Product> products) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 16),
    child: GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.65,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: products.length,
      itemBuilder: (_, i) => ProductCard(
        product: products[i],
        onTap: () => Navigator.push(
          ctx,
          MaterialPageRoute(
            builder: (_) => ProductDetailScreen(productId: products[i].id),
          ),
        ),
      ),
    ),
  );

  Widget _buildShimmer() => Shimmer.fromColors(
    baseColor: Colors.grey[300]!,
    highlightColor: Colors.grey[100]!,
    child: Column(
      children: [
        Container(
          margin: const EdgeInsets.all(16),
          height: 100,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 0.65,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
            ),
            itemCount: 6,
            itemBuilder: (_, __) => Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
              ),
            ),
          ),
        ),
      ],
    ),
  );
}
