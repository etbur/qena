import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/providers.dart';
import '../../shared/theme/app_theme.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(builder: (_, auth, __) {
      if (!auth.isLoggedIn)
        return Scaffold(
          appBar: AppBar(title: const Text('Profile')),
          body: Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.account_circle_outlined,
                size: 80, color: AppTheme.textGrey),
            const SizedBox(height: 16),
            const Text('You\'re not logged in',
                style: TextStyle(fontSize: 16, color: AppTheme.textGrey)),
            const SizedBox(height: 20),
            ElevatedButton(
                onPressed: () => Navigator.pushNamed(context, '/login'),
                child: const Text('Login')),
            const SizedBox(height: 10),
            OutlinedButton(
                onPressed: () => Navigator.pushNamed(context, '/register'),
                child: const Text('Register')),
          ])),
        );

      final u = auth.user!;
      return Scaffold(
        appBar: AppBar(title: const Text('My Profile')),
        body: ListView(children: [
          // Header
          Container(
            padding: const EdgeInsets.all(28),
            color: AppTheme.primary,
            child: Column(children: [
              CircleAvatar(
                  radius: 40,
                  backgroundColor: AppTheme.secondary,
                  child: u.avatarUrl != null
                      ? null
                      : Text(
                          u.fullName.isNotEmpty
                              ? u.fullName[0].toUpperCase()
                              : 'U',
                          style: const TextStyle(
                              fontSize: 28,
                              color: Colors.white,
                              fontWeight: FontWeight.w800))),
              const SizedBox(height: 12),
              Text(u.fullName,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w800)),
              Text('@${u.username}',
                  style: const TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 6),
              Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                  decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20)),
                  child: Text(u.role.toUpperCase(),
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w700))),
            ]),
          ),
          // Info cards
          _tile(Icons.email_outlined, 'Email', u.email),
          _tile(Icons.phone_outlined, 'Phone',
              u.phone.isNotEmpty ? u.phone : 'Not set'),
          _tile(Icons.location_city_outlined, 'City',
              u.city.isNotEmpty ? u.city : 'Not set'),
          const Divider(height: 1),
          // Actions
          _action(context, Icons.shopping_bag_outlined, 'My Orders',
              () => Navigator.pushNamed(context, '/orders')),
          if (u.isVendor)
            _action(context, Icons.store_outlined, 'Vendor Dashboard', () {}),
          _action(context, Icons.settings_outlined, 'Settings', () {}),
          const Divider(height: 1),
          Padding(
              padding: const EdgeInsets.all(20),
              child: ElevatedButton.icon(
                onPressed: () async {
                  await auth.logout();
                },
                icon: const Icon(Icons.logout),
                label: const Text('Logout'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.secondary,
                    padding: const EdgeInsets.symmetric(vertical: 14)),
              )),
        ]),
      );
    });
  }

  Widget _tile(IconData icon, String label, String value) => ListTile(
        leading: Icon(icon, color: AppTheme.primary),
        title: Text(label,
            style: const TextStyle(fontSize: 12, color: AppTheme.textGrey)),
        subtitle: Text(value,
            style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: AppTheme.textDark)),
      );

  Widget _action(
          BuildContext ctx, IconData icon, String label, VoidCallback onTap) =>
      ListTile(
          leading: Icon(icon, color: AppTheme.primary),
          title: Text(label),
          trailing: const Icon(Icons.chevron_right, color: AppTheme.textGrey),
          onTap: onTap);
}
