import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/api_client.dart';
import '../../core/models.dart';
import '../../shared/theme/app_theme.dart';
import '../../shared/widgets/product_card.dart';
import '../products/product_detail_screen.dart';

class VendorScreen extends StatefulWidget {
  final String vendorSlug;
  const VendorScreen({super.key, required this.vendorSlug});

  @override
  State<VendorScreen> createState() => _VendorScreenState();
}

class _VendorScreenState extends State<VendorScreen> {
  Vendor? _vendor;
  List<Product> _products = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadVendorData();
  }

  Future<void> _loadVendorData() async {
    setState(() => _loading = true);
    final vRes = await ApiClient.get('/vendors/${widget.vendorSlug}/');
    final pRes = await ApiClient.get('/vendors/${widget.vendorSlug}/products/');

    if (vRes['ok']) {
      _vendor = Vendor.fromJson(vRes['data']);
    }
    if (pRes['ok']) {
      final list = pRes['data'] is List ? pRes['data'] : (pRes['data']['results'] ?? []);
      _products = (list as List).map((e) => Product.fromJson(e)).toList();
    }

    setState(() => _loading = false);
  }

  Future<void> _openWhatsApp(String phone) async {
    final clean = phone.replaceAll(RegExp(r'[^0-9]'), '');
    final url = Uri.parse('https://wa.me/$clean');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _callPhone(String phone) async {
    final url = Uri.parse('tel:$phone');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_vendor == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Vendor Store')),
        body: const Center(child: Text('Vendor not found')),
      );
    }

    final v = _vendor!;

    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: CustomScrollView(
        slivers: [
          // ── Vendor Header & Banner ───────────────────────────────────────
          SliverAppBar(
            expandedHeight: 180,
            pinned: true,
            backgroundColor: AppTheme.primary,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                v.storeName,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              background: v.bannerUrl != null && v.bannerUrl!.isNotEmpty
                  ? CachedNetworkImage(
                      imageUrl: v.bannerUrl!,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [AppTheme.primary, Color(0xFF1A4B8A)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                      ),
                      child: Center(
                        child: Icon(Icons.storefront, size: 60, color: Colors.white.withOpacity(0.2)),
                      ),
                    ),
            ),
          ),

          // ── Vendor Profile & Action Card ─────────────────────────────────
          SliverToBoxAdapter(
            child: Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFEEF2F6)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 50,
                        height: 50,
                        decoration: BoxDecoration(
                          color: AppTheme.primary,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Center(
                          child: Text(
                            v.storeName.isNotEmpty ? v.storeName[0].toUpperCase() : 'V',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              v.storeName,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.textDark,
                              ),
                            ),
                            if (v.city.isNotEmpty || v.country.isNotEmpty)
                              Text(
                                '${v.city}, ${v.country}',
                                style: const TextStyle(fontSize: 12, color: AppTheme.textGrey),
                              ),
                            if (v.customDomain != null && v.customDomain!.isNotEmpty)
                              Container(
                                margin: const EdgeInsets.only(top: 4),
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFE0F2FE),
                                  borderRadius: BorderRadius.circular(100),
                                ),
                                child: Text(
                                  '🌐 ${v.customDomain}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: Color(0xFF0284C7),
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  if (v.tagline != null && v.tagline!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      v.tagline!,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF475569),
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                  const SizedBox(height: 14),

                  // Quick Action Buttons
                  Row(
                    children: [
                      if (v.phone.isNotEmpty) ...[
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => _callPhone(v.phone),
                            icon: const Icon(Icons.phone, size: 16),
                            label: const Text('Call'),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      if (v.whatsapp != null && v.whatsapp!.isNotEmpty) ...[
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () => _openWhatsApp(v.whatsapp!),
                            icon: const Icon(Icons.chat, size: 16, color: Colors.white),
                            label: const Text('WhatsApp'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF25D366),
                              padding: const EdgeInsets.symmetric(vertical: 8),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),

          // ── Section Title ────────────────────────────────────────────────
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(
                'Products (${_products.length})',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textDark,
                ),
              ),
            ),
          ),

          // ── Products Grid ────────────────────────────────────────────────
          if (_products.isEmpty)
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Center(
                  child: Text('No products available from this vendor yet.'),
                ),
              ),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverGrid(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 0.65,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                ),
                delegate: SliverChildBuilderDelegate(
                  (ctx, i) => ProductCard(
                    product: _products[i],
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ProductDetailScreen(productId: _products[i].id),
                      ),
                    ),
                  ),
                  childCount: _products.length,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
