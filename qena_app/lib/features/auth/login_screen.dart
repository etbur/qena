import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _State();
}

class _State extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _user = TextEditingController();
  final _pass = TextEditingController();
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
          child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const SizedBox(height: 40),
          // Logo
          Row(children: [
            Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                    color: AppTheme.primary,
                    borderRadius: BorderRadius.circular(12)),
                child: const Center(
                    child: Text('🇪🇹', style: TextStyle(fontSize: 24)))),
            const SizedBox(width: 12),
            const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Qenagebeya',
                      style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.primary)),
                  Text('Ethiopia\'s #1 Marketplace',
                      style: TextStyle(fontSize: 12, color: AppTheme.textGrey)),
                ]),
          ]),
          const SizedBox(height: 40),
          const Text('Welcome back',
              style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.textDark)),
          const Text('Sign in to your account',
              style: TextStyle(fontSize: 14, color: AppTheme.textGrey)),
          const SizedBox(height: 32),
          Form(
              key: _form,
              child: Column(children: [
                TextFormField(
                    controller: _user,
                    decoration: const InputDecoration(
                        hintText: 'Username',
                        prefixIcon: Icon(Icons.person_outline, size: 20)),
                    validator: (v) =>
                        v == null || v.isEmpty ? 'Required' : null),
                const SizedBox(height: 16),
                TextFormField(
                    controller: _pass,
                    obscureText: _obscure,
                    decoration: InputDecoration(
                        hintText: 'Password',
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
                        v == null || v.isEmpty ? 'Required' : null),
              ])),
          const SizedBox(height: 28),
          Consumer<AuthProvider>(builder: (_, auth, __) {
            if (auth.error != null)
              Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(auth.error!,
                      style: const TextStyle(
                          color: AppTheme.secondary, fontSize: 13)));
            return SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: auth.loading
                      ? null
                      : () async {
                          if (!_form.currentState!.validate()) return;
                          final ok =
                              await auth.login(_user.text.trim(), _pass.text);
                          if (ok && mounted) Navigator.pop(context);
                        },
                  style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primary,
                      padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: auth.loading
                      ? const CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2)
                      : const Text('Login',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.w800)),
                ));
          }),
          const SizedBox(height: 20),
          Center(
              child: TextButton(
            onPressed: () =>
                Navigator.pushReplacementNamed(context, '/register'),
            child: const Text.rich(TextSpan(children: [
              TextSpan(
                  text: "Don't have an account? ",
                  style: TextStyle(color: AppTheme.textGrey)),
              TextSpan(
                  text: 'Register',
                  style: TextStyle(
                      color: AppTheme.primary, fontWeight: FontWeight.w700)),
            ])),
          )),
        ]),
      )),
    );
  }
}
