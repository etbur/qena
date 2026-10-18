import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _State();
}

class _State extends State<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _user = TextEditingController();
  final _email = TextEditingController();
  final _fname = TextEditingController();
  final _lname = TextEditingController();
  final _phone = TextEditingController();
  final _pass = TextEditingController();
  final _pass2 = TextEditingController();
  String _role = 'customer';
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
          title: const Text('Create Account'),
          backgroundColor: AppTheme.primary),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
            key: _form,
            child: Column(children: [
              Row(children: [
                Expanded(
                    child: _field(_fname, 'First Name', Icons.person_outline)),
                const SizedBox(width: 12),
                Expanded(
                    child: _field(_lname, 'Last Name', Icons.person_outline)),
              ]),
              const SizedBox(height: 14),
              _field(_user, 'Username', Icons.alternate_email),
              const SizedBox(height: 14),
              _field(_email, 'Email', Icons.email_outlined,
                  type: TextInputType.emailAddress),
              const SizedBox(height: 14),
              _field(_phone, 'Phone (+251...)', Icons.phone_outlined,
                  type: TextInputType.phone),
              const SizedBox(height: 14),
              // Role
              DropdownButtonFormField<String>(
                value: _role,
                decoration: const InputDecoration(
                    hintText: 'Account Type',
                    prefixIcon: Icon(Icons.badge_outlined, size: 20)),
                items: const [
                  DropdownMenuItem(value: 'customer', child: Text('Customer')),
                  DropdownMenuItem(
                      value: 'vendor', child: Text('Vendor / Seller')),
                ],
                onChanged: (v) => setState(() => _role = v!),
              ),
              const SizedBox(height: 14),
              TextFormField(
                  controller: _pass,
                  obscureText: _obscure,
                  decoration: InputDecoration(
                      hintText: 'Password (min 6 chars)',
                      prefixIcon: const Icon(Icons.lock_outline, size: 20),
                      suffixIcon: IconButton(
                          icon: Icon(
                              _obscure
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                              size: 20),
                          onPressed: () =>
                              setState(() => _obscure = !_obscure))),
                  validator: (v) =>
                      v != null && v.length >= 6 ? null : 'Min 6 characters'),
              const SizedBox(height: 14),
              TextFormField(
                  controller: _pass2,
                  obscureText: _obscure,
                  decoration: const InputDecoration(
                      hintText: 'Confirm Password',
                      prefixIcon: Icon(Icons.lock_outline, size: 20)),
                  validator: (v) =>
                      v == _pass.text ? null : 'Passwords do not match'),
              const SizedBox(height: 28),
              Consumer<AuthProvider>(builder: (_, auth, __) {
                if (auth.error != null)
                  Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Text(auth.error!,
                          style: const TextStyle(
                              color: AppTheme.secondary, fontSize: 13)));
                return SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: auth.loading ? null : _register,
                      style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.secondary,
                          padding: const EdgeInsets.symmetric(vertical: 16)),
                      child: auth.loading
                          ? const CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2)
                          : const Text('Create Account',
                              style: TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w800)),
                    ));
              }),
              const SizedBox(height: 16),
              TextButton(
                  onPressed: () =>
                      Navigator.pushReplacementNamed(context, '/login'),
                  child: const Text.rich(TextSpan(children: [
                    TextSpan(
                        text: 'Already have an account? ',
                        style: TextStyle(color: AppTheme.textGrey)),
                    TextSpan(
                        text: 'Login',
                        style: TextStyle(
                            color: AppTheme.primary,
                            fontWeight: FontWeight.w700)),
                  ]))),
            ])),
      ),
    );
  }

  Widget _field(TextEditingController c, String hint, IconData icon,
          {TextInputType? type}) =>
      TextFormField(
          controller: c,
          keyboardType: type,
          decoration:
              InputDecoration(hintText: hint, prefixIcon: Icon(icon, size: 20)),
          validator: (v) => v == null || v.isEmpty ? 'Required' : null);

  Future<void> _register() async {
    if (!_form.currentState!.validate()) return;
    final ok = await context.read<AuthProvider>().register({
      'username': _user.text.trim(),
      'email': _email.text.trim(),
      'first_name': _fname.text.trim(),
      'last_name': _lname.text.trim(),
      'phone': _phone.text.trim(),
      'role': _role,
      'password': _pass.text,
      'password2': _pass2.text,
    });
    if (ok && mounted)
      Navigator.pushNamedAndRemoveUntil(context, '/', (r) => false);
  }
}
