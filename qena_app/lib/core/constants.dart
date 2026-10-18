class AppConstants {
  // Change to your server IP when testing on a real device
  // For emulator: http://10.0.2.2:8000
  // For physical device on same WiFi: http://192.168.x.x:8000
  static const String baseUrl   = 'http://localhost:8000';
  static const String apiBase   = '$baseUrl/api/v1';
  static const String mediaBase = baseUrl;

  // App info
  static const String appName    = 'Qenagebeya';
  static const String appTagline = "Ethiopia's #1 Multi-Vendor Marketplace";
  static const String currency   = 'ETB';

  // Colors (matches web brand)
  static const int primaryColor   = 0xFF0B2B4A;
  static const int secondaryColor = 0xFFD42E2E;
  static const int accentColor    = 0xFF078930;

  // Pagination
  static const int pageSize = 20;
}
