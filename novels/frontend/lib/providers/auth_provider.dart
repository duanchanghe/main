import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/auth_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService;
  User? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider({AuthService? authService})
      : _authService = authService ?? AuthService() {
    _loadUser();
  }

  User? get user => _user;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _user != null;
  String? get error => _error;

  Future<void> _loadUser() async {
    await _authService.loadStoredToken();
    if (_authService.isAuthenticated) {
      // User is logged in (token exists)
      _user = User(id: 0, username: 'User');
      notifyListeners();
    }
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final success = await _authService.login(username, password);
    if (success) {
      _user = User(id: 0, username: username);
    } else {
      _error = '登录失败，请检查用户名和密码';
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<bool> register(String username, String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final success = await _authService.register(username, email, password);
    if (success) {
      _user = User(id: 0, username: username, email: email);
    } else {
      _error = '注册失败，请检查输入信息';
    }

    _isLoading = false;
    notifyListeners();
    return success;
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }
}
