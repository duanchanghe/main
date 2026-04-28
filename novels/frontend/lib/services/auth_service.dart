import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';

class AuthService {
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userKey = 'user';

  final Dio _dio;
  String? _accessToken;

  AuthService({Dio? dio}) : _dio = dio ?? Dio() {
    _dio.options.baseUrl = 'http://localhost:8000/api';
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final refreshed = await refreshToken();
          if (refreshed) {
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $_accessToken';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } catch (e) {
              return handler.reject(error);
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  Future<void> loadStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString(_accessTokenKey);
  }

  Future<bool> login(String username, String password) async {
    try {
      final response = await _dio.post('/auth/login/', data: {
        'username': username,
        'password': password,
      });

      if (response.statusCode == 200) {
        final authResponse = AuthResponse.fromJson(response.data);
        await _saveTokens(authResponse);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<bool> register(String username, String email, String password) async {
    try {
      final response = await _dio.post('/auth/register/', data: {
        'username': username,
        'email': email,
        'password': password,
      });

      if (response.statusCode == 201) {
        final authResponse = AuthResponse.fromJson(response.data);
        await _saveTokens(authResponse);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> _saveTokens(AuthResponse authResponse) async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = authResponse.tokens.access;
    await prefs.setString(_accessTokenKey, authResponse.tokens.access);
    await prefs.setString(_refreshTokenKey, authResponse.tokens.refresh);
  }

  Future<bool> refreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString(_refreshTokenKey);
    if (refreshToken == null) return false;

    try {
      final response = await _dio.post('/auth/refresh/', data: {
        'refresh': refreshToken,
      });

      if (response.statusCode == 200) {
        _accessToken = response.data['access'];
        await prefs.setString(_accessTokenKey, _accessToken!);
        return true;
      }
    } catch (e) {
      // Ignore
    }
    return false;
  }

  bool get isAuthenticated => _accessToken != null;

  String? get accessToken => _accessToken;

  Map<String, String> get authHeaders => {
        'Authorization': 'Bearer $_accessToken',
      };

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
    _accessToken = null;
  }
}
