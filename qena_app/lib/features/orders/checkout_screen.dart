import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key});
  @override
  State<CheckoutScreen> createState() => _State();
}

class _State extends State<CheckoutScreen> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _address = TextEditingController();
  String _payment = 'telebirr';
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    final user = context.read<AuthProvider>().user;
    if (user != null) {
      _name.text = user.fullName;
      _phone.text = user.phone;
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();
    return Scaffold(
      appBar: AppBar(title: const Text('Checkout')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
            key: _form,
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _section('📦 Order Summary'),
              ...cart.items.map((i) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(children: [
                      Expanded(
                          child: Text('${i.product.name} × ${i.quantity}',
                              style: const TextStyle(fontSize: 14))),
                      Text('ETB ${i.subtotal.toStringAsFixed(0)}',
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                    ]),
                  )),
              const Divider(height: 24),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                const Text('Total',
                    style:
                        TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                Text('ETB ${cart.total.toStringAsFixed(0)}',
                    style: const TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 20,
                        color: AppTheme.secondary)),
              ]),
              const SizedBox(height: 24),
              _section('📍 Shipping Details'),
              _field(_name, 'Full Name', Icons.person_outline),
              const SizedBox(height: 12),
              _field(_phone, 'Phone Number', Icons.phone_outlined),
              const SizedBox(height: 12),
              _field(_address, 'Delivery Address', Icons.location_on_outlined,
                  lines: 2),
              const SizedBox(height: 24),
              _section('💳 Payment Method'),
              ...['telebirr', 'cbe_birr', 'amole', 'cash']
                  .map((m) => RadioListTile<String>(
                        value: m,
                        groupValue: _payment,
                        title: Text(_payLabel(m),
                            style: const TextStyle(
                                fontSize: 14, fontWeight: FontWeight.w600)),
                        onChanged: (v) => setState(() => _payment = v!),
                        activeColor: AppTheme.primary,
                        contentPadding: EdgeInsets.zero,
                      )),
              const SizedBox(height: 24),
              SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _placeOrder,
                    style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.secondary,
                        padding: const EdgeInsets.symmetric(vertical: 16)),
                    child: _loading
                        ? const CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2)
                        : const Text('Place Order · ዕዳ ጀምር',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.w800)),
                  )),
            ])),
      ),
    );
  }

  Widget _section(String t) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(t,
          style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: AppTheme.textDark)));

  Widget _field(TextEditingController c, String hint, IconData icon,
          {int lines = 1}) =>
      TextFormField(
          controller: c,
          maxLines: lines,
          decoration: InputDecoration(
              hintText: hint,
              prefixIcon: Icon(icon, size: 20, color: AppTheme.textGrey)),
          validator: (v) => v == null || v.isEmpty ? 'Required' : null);

  String _payLabel(String m) =>
      {
        'telebirr': '📱 TeleBirr',
        'cbe_birr': '🏦 CBE Birr',
        'amole': '💳 Amole',
        'cash': '💵 Cash on Delivery'
      }[m] ??
      m;

  Future<void> _placeOrder() async {
    if (!_form.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    if (!auth.isLoggedIn) {
      Navigator.pushNamed(context, '/login');
      return;
    }
    setState(() => _loading = true);
    final cart = context.read<CartProvider>();
    final orders = context.read<OrdersProvider>();
    final data = {
      'shipping_name': _name.text.trim(),
      'shipping_phone': _phone.text.trim(),
      'shipping_address': _address.text.trim(),
      'payment_method': _payment,
      'items': cart.items
          .map((i) => {'product_id': i.product.id, 'quantity': i.quantity})
          .toList(),
    };
    final order = await orders.placeOrder(data);
    setState(() => _loading = false);
    if (order != null) {
      cart.clear();
      if (mounted)
        Navigator.pushNamedAndRemoveUntil(context, '/orders', (r) => r.isFirst);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Order #${order.orderNumber} placed!'),
          backgroundColor: AppTheme.accent));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Order failed. Try again.'),
          backgroundColor: AppTheme.secondary));
    }
  }
}
