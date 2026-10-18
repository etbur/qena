import 'constants.dart';

String mediaUrl(String? path) {
  if (path == null || path.isEmpty) return '';
  if (path.startsWith('http')) return path;
  return '${AppConstants.mediaBase}$path';
}

// ── User ─────────────────────────────────────────────────────────────────────
class AppUser {
  final int id;
  final String username, email, firstName, lastName, phone, role;
  final String? avatarUrl;

  AppUser({
    required this.id,
    required this.username,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.phone,
    required this.role,
    this.avatarUrl,
  });

  factory AppUser.fromJson(Map j) => AppUser(
    id: j['id'],
    username: j['username'],
    email: j['email'] ?? '',
    firstName: j['first_name'] ?? '',
    lastName: j['last_name'] ?? '',
    phone: j['phone'] ?? '',
    role: j['role'] ?? 'customer',
    avatarUrl: j['avatar_url'],
  );

  String get fullName => '$firstName $lastName'.trim().isNotEmpty
      ? '$firstName $lastName'.trim()
      : username;
  bool get isVendor => role == 'vendor';
  bool get isAgent => role == 'agent';
  bool get isAdmin => role == 'admin';
}

// ── Category ─────────────────────────────────────────────────────────────────
class Category {
  final int id;
  final String name, slug, icon;
  final String? imageUrl;
  Category({
    required this.id,
    required this.name,
    required this.slug,
    required this.icon,
    this.imageUrl,
  });
  factory Category.fromJson(Map j) => Category(
    id: j['id'],
    name: j['name'],
    slug: j['slug'],
    icon: j['icon'] ?? 'fas fa-tag',
    imageUrl: j['image_url'],
  );
}

// ── Product ──────────────────────────────────────────────────────────────────
class Product {
  final int id;
  final String name, slug, vendorName;
  final double price;
  final double? originalPrice;
  final int? discountPct;
  final String? imageUrl, categoryName;
  final bool isFeatured, isFlashDeal;
  final int stock;
  // Detail only
  final String? description;
  final List<String> images;

  Product({
    required this.id,
    required this.name,
    required this.slug,
    required this.price,
    required this.vendorName,
    this.originalPrice,
    this.discountPct,
    this.imageUrl,
    this.categoryName,
    this.isFeatured = false,
    this.isFlashDeal = false,
    this.stock = 0,
    this.description,
    this.images = const [],
  });

  factory Product.fromJson(Map j) => Product(
    id: j['id'],
    name: j['name'],
    slug: j['slug'] ?? '',
    price: double.tryParse(j['price'].toString()) ?? 0,
    vendorName: j['vendor_name'] ?? '',
    originalPrice: j['original_price'] != null
        ? double.tryParse(j['original_price'].toString())
        : null,
    discountPct: j['discount_pct'],
    imageUrl: j['image_url'],
    categoryName: j['category_name'],
    isFeatured: j['is_featured'] ?? false,
    isFlashDeal: j['is_flash_deal'] ?? false,
    stock: j['stock'] ?? 0,
    description: j['description'],
    images: j['images'] != null ? List<String>.from(j['images']) : [],
  );
}

// ── Vendor ───────────────────────────────────────────────────────────────────
class Vendor {
  final int id;
  final String storeName, slug, tier;
  final String? description, tagline, logoUrl, bannerUrl;
  final String phone, email, city, country;
  final String? whatsapp, instagram, facebook, subdomain, customDomain;
  final int productsCount;

  Vendor({
    required this.id,
    required this.storeName,
    required this.slug,
    required this.tier,
    this.description,
    this.tagline,
    this.logoUrl,
    this.bannerUrl,
    this.phone = '',
    this.email = '',
    this.city = '',
    this.country = '',
    this.whatsapp,
    this.instagram,
    this.facebook,
    this.subdomain,
    this.customDomain,
    this.productsCount = 0,
  });

  factory Vendor.fromJson(Map j) => Vendor(
    id: j['id'],
    storeName: j['store_name'],
    slug: j['slug'],
    tier: j['tier'] ?? 'bronze',
    description: j['description'],
    tagline: j['store_tagline'],
    logoUrl: j['logo_url'],
    bannerUrl: j['banner_url'],
    phone: j['phone'] ?? '',
    email: j['email'] ?? '',
    city: j['city'] ?? '',
    country: j['country'] ?? '',
    whatsapp: j['whatsapp'],
    instagram: j['instagram'],
    facebook: j['facebook'],
    subdomain: j['subdomain'],
    customDomain: j['custom_domain'],
    productsCount: j['products_count'] ?? 0,
  );
}

// ── Cart ─────────────────────────────────────────────────────────────────────
class CartItem {
  final Product product;
  int quantity;
  CartItem({required this.product, this.quantity = 1});
  double get subtotal => product.price * quantity;
}

// ── Order ─────────────────────────────────────────────────────────────────────
class OrderItem {
  final int id;
  final String productName;
  final double price, subtotal;
  final int qty;
  final String? imageUrl;
  OrderItem({
    required this.id,
    required this.productName,
    required this.price,
    required this.subtotal,
    required this.qty,
    this.imageUrl,
  });
  factory OrderItem.fromJson(Map j) => OrderItem(
    id: j['id'],
    productName: j['product_name'],
    price: double.tryParse(j['product_price'].toString()) ?? 0,
    subtotal: double.tryParse(j['subtotal'].toString()) ?? 0,
    qty: j['quantity'] ?? 1,
    imageUrl: j['product_image'],
  );
}

class Order {
  final int id;
  final String orderNumber, status, statusDisplay;
  final double total;
  final String shippingName, paymentMethod, createdAt;
  final List<OrderItem> items;
  Order({
    required this.id,
    required this.orderNumber,
    required this.status,
    required this.statusDisplay,
    required this.total,
    required this.shippingName,
    required this.paymentMethod,
    required this.createdAt,
    this.items = const [],
  });
  factory Order.fromJson(Map j) => Order(
    id: j['id'],
    orderNumber: j['order_number'],
    status: j['status'],
    statusDisplay: j['status_display'] ?? j['status'],
    total: double.tryParse(j['total'].toString()) ?? 0,
    shippingName: j['shipping_name'] ?? '',
    paymentMethod: j['payment_method'] ?? '',
    createdAt: j['created_at'] ?? '',
    items: (j['items'] as List? ?? [])
        .map((e) => OrderItem.fromJson(e))
        .toList(),
  );
}

// ── Live Stream ───────────────────────────────────────────────────────────────
class LiveStream {
  final String id, title, status, statusDisplay, vendorName;
  final String? thumbnailUrl, vendorLogo;
  final int views, likes, messages;
  LiveStream({
    required this.id,
    required this.title,
    required this.status,
    required this.statusDisplay,
    required this.vendorName,
    this.thumbnailUrl,
    this.vendorLogo,
    this.views = 0,
    this.likes = 0,
    this.messages = 0,
  });
  factory LiveStream.fromJson(Map j) => LiveStream(
    id: j['stream_id'].toString(),
    title: j['title'],
    status: j['status'],
    statusDisplay: j['status_display'] ?? j['status'],
    vendorName: j['vendor_name'] ?? '',
    thumbnailUrl: j['thumbnail_url'],
    vendorLogo: j['vendor_logo'],
    views: j['total_views'] ?? 0,
    likes: j['total_likes'] ?? 0,
    messages: j['total_messages'] ?? 0,
  );
  bool get isLive => status == 'live';
}
