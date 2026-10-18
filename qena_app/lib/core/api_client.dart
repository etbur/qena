import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'constants.dart';

class ApiClient {
  static const _storage = FlutterSecureStorage();
  static const String _accessKey = 'access_token';
  static const String _refreshKey = 'refresh_token';

  // ── Token management ──────────────────────────────────────────────────────
  static Future<void> saveTokens(String access, String refresh) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  static Future<String?> getAccessToken() => _storage.read(key: _accessKey);
  static Future<String?> getRefreshToken() => _storage.read(key: _refreshKey);

  static Future<void> clearTokens() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  static Future<bool> refreshAccessToken() async {
    final refresh = await getRefreshToken();
    if (refresh == null) return false;
    try {
      final res = await http.post(
        Uri.parse('${AppConstants.apiBase}/auth/refresh/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refresh}),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await _storage.write(key: _accessKey, value: data['access']);
        return true;
      }
    } catch (_) {}
    return false;
  }

  // ── Headers ───────────────────────────────────────────────────────────────
  static Future<Map<String, String>> _headers({bool auth = false}) async {
    final h = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (auth) {
      final token = await getAccessToken();
      if (token != null) h['Authorization'] = 'Bearer $token';
    }
    return h;
  }

  // ── HTTP Methods ──────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> get(
    String path, {
    bool auth = false,
    Map<String, String>? params,
  }) async {
    var uri = Uri.parse('${AppConstants.apiBase}$path');
    if (params != null) uri = uri.replace(queryParameters: params);
    final res = await http.get(uri, headers: await _headers(auth: auth));
    return _handle(res);
  }

  static Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body, {
    bool auth = false,
  }) async {
    final res = await http.post(
      Uri.parse('${AppConstants.apiBase}$path'),
      headers: await _headers(auth: auth),
      body: jsonEncode(body),
    );
    return _handle(res);
  }

  static Future<Map<String, dynamic>> patch(
    String path,
    Map<String, dynamic> body, {
    bool auth = true,
  }) async {
    final res = await http.patch(
      Uri.parse('${AppConstants.apiBase}$path'),
      headers: await _headers(auth: auth),
      body: jsonEncode(body),
    );
    return _handle(res);
  }

  static Map<String, dynamic> _handle(http.Response res) {
    final body = utf8.decode(res.bodyBytes);
    try {
      final data = jsonDecode(body);
      if (res.statusCode >= 200 && res.statusCode < 300) {
        return {'ok': true, 'data': data, 'status': res.statusCode};
      }
      return {'ok': false, 'error': data, 'status': res.statusCode};
    } catch (e) {
      return {'ok': false, 'error': body, 'status': res.statusCode};
    }
  }
}
