import 'package:flutter/material.dart';
import 'api_client.dart';
import 'models.dart';

// ── Auth Provider ─────────────────────────────────────────────────────────────
class AuthProvider extends ChangeNotifier {
  AppUser? _user;
  bool _loading = false;
  String? _error;

  AppUser? get user => _user;
  bool get loading => _loading;
  String? get error => _error;
  bool get isLoggedIn => _user != null;

  Future<void> init() async {
    final token = await ApiClient.getAccessToken();
    if (token == null) return;
    await loadProfile();
  }

  Future<bool> login(String username, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();
    final res = await ApiClient.post('/auth/login/', {
      'username': username,
      'password': password,
    });
    _loading = false;
    if (res['ok']) {
      await ApiClient.saveTokens(
        res['data']['tokens']['access'],
        res['data']['tokens']['refresh'],
      );
      _user = AppUser.fromJson(res['data']['user']);
      notifyListeners();
      return true;
    }
    _error = _parseError(res['error']);
    notifyListeners();
    return false;
  }

  Future<bool> register(Map<String, dynamic> data) async {
    _loading = true;
    _error = null;
    notifyListeners();
    final res = await ApiClient.post('/auth/register/', data);
    _loading = false;
    if (res['ok']) {
      await ApiClient.saveTokens(
        res['data']['tokens']['access'],
        res['data']['tokens']['refresh'],
      );
      _user = AppUser.fromJson(res['data']['user']);
      notifyListeners();
      return true;
    }
    _error = _parseError(res['error']);
    notifyListeners();
    return false;
  }

  Future<void> loadProfile() async {
    final res = await ApiClient.get('/auth/profile/', auth: true);
    if (res['ok']) {
      _user = AppUser.fromJson(res['data']);
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await ApiClient.clearTokens();
    _user = null;
    notifyListeners();
  }

  String _parseError(dynamic e) {
    if (e is Map) return e.values.join(', ');
    return e.toString();
  }
}

// ── Cart Provider ─────────────────────────────────────────────────────────────
class CartProvider extends ChangeNotifier {
  final List<CartItem> _items = [];

  List<CartItem> get items => _items;
  int get count => _items.fold(0, (s, i) => s + i.quantity);
  double get total => _items.fold(0.0, (s, i) => s + i.subtotal);

  void add(Product p, {int qty = 1}) {
    final idx = _items.indexWhere((i) => i.product.id == p.id);
    if (idx >= 0) {
      _items[idx].quantity += qty;
    } else {
      _items.add(CartItem(product: p, quantity: qty));
    }
    notifyListeners();
  }

  void remove(int productId) {
    _items.removeWhere((i) => i.product.id == productId);
    notifyListeners();
  }

  void updateQty(int productId, int qty) {
    final idx = _items.indexWhere((i) => i.product.id == productId);
    if (idx >= 0) {
      if (qty <= 0) {
        _items.removeAt(idx);
      } else {
        _items[idx].quantity = qty;
      }
      notifyListeners();
    }
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }
}

// ── Products Provider ─────────────────────────────────────────────────────────
class ProductsProvider extends ChangeNotifier {
  List<Product> _featured = [];
  List<Product> _flash = [];
  List<Product> _newArr = [];
  List<Category> _cats = [];
  List<LiveStream> _live = [];
  List<Vendor> _vendors = [];
  bool _loading = false;
  String? _error;

  List<Product> get featured => _featured;
  List<Product> get flash => _flash;
  List<Product> get newArr => _newArr;
  List<Category> get categories => _cats;
  List<LiveStream> get liveNow => _live;
  List<Vendor> get vendors => _vendors;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> loadHome() async {
    _loading = true;
    notifyListeners();
    final res = await ApiClient.get('/home/');
    _loading = false;
    if (res['ok']) {
      final d = res['data'];
      _featured = _parseProducts(d['featured']);
      _flash = _parseProducts(d['flash_deals']);
      _newArr = _parseProducts(d['new_arrivals']);
      _cats = (d['categories'] as List? ?? [])
          .map((e) => Category.fromJson(e))
          .toList();
      _live = (d['live_now'] as List? ?? [])
          .map((e) => LiveStream.fromJson(e))
          .toList();
      _vendors = (d['vendors'] as List? ?? [])
          .map((e) => Vendor.fromJson(e))
          .toList();
    } else {
      _error = res['error'].toString();
    }
    notifyListeners();
  }

  List<Product> _parseProducts(dynamic list) =>
      (list as List? ?? []).map((e) => Product.fromJson(e)).toList();

  Future<List<Product>> searchProducts(String q) async {
    final res = await ApiClient.get('/search/', params: {'q': q});
    if (res['ok']) return _parseProducts(res['data']['products']);
    return [];
  }

  Future<List<Product>> getProducts({
    String? category,
    String? vendor,
    bool? featured,
    bool? flash,
    String? search,
  }) async {
    final params = <String, String>{};
    if (category != null) params['category'] = category;
    if (vendor != null) params['vendor'] = vendor;
    if (featured == true) params['featured'] = '1';
    if (flash == true) params['flash'] = '1';
    if (search != null) params['search'] = search;
    final res = await ApiClient.get('/products/', params: params);
    if (res['ok']) {
      final d = res['data'];
      final list = d is List ? d : (d['results'] ?? []);
      return _parseProducts(list);
    }
    return [];
  }

  Future<Product?> getProduct(int id) async {
    final res = await ApiClient.get('/products/$id/');
    if (res['ok']) return Product.fromJson(res['data']);
    return null;
  }
}

// ── Orders Provider ───────────────────────────────────────────────────────────
class OrdersProvider extends ChangeNotifier {
  List<Order> _orders = [];
  bool _loading = false;

  List<Order> get orders => _orders;
  bool get loading => _loading;

  Future<void> loadOrders() async {
    _loading = true;
    notifyListeners();
    final res = await ApiClient.get('/orders/', auth: true);
    _loading = false;
    if (res['ok']) {
      final d = res['data'];
      final list = d is List ? d : (d['results'] ?? []);
      _orders = (list as List).map((e) => Order.fromJson(e)).toList();
    }
    notifyListeners();
  }

  Future<Order?> placeOrder(Map<String, dynamic> data) async {
    final res = await ApiClient.post('/orders/place/', data, auth: true);
    if (res['ok']) {
      final o = Order.fromJson(res['data']);
      _orders.insert(0, o);
      notifyListeners();
      return o;
    }
    return null;
  }
}
