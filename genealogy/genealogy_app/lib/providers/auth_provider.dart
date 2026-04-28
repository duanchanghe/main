import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_service.dart';
import '../models/models.dart';

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

final authStateProvider = StateNotifierProvider<AuthStateNotifier, AuthState>((ref) {
  return AuthStateNotifier(ref.watch(apiServiceProvider));
});

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final bool isInitialized;
  final User? user;
  final String? error;

  AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.isInitialized = false,
    this.user,
    this.error,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    bool? isInitialized,
    User? user,
    String? error,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      isInitialized: isInitialized ?? this.isInitialized,
      user: user ?? this.user,
      error: error,
    );
  }
}

class AuthStateNotifier extends StateNotifier<AuthState> {
  final ApiService _api;

  AuthStateNotifier(this._api) : super(AuthState()) {
    _initialize();
  }

  Future<void> _initialize() async {
    state = state.copyWith(isLoading: true);
    
    await _api.loadTokens();
    
    if (_api.isAuthenticated) {
      final result = await _api.getCurrentUser();
      if (result.isSuccess && result.data != null) {
        state = AuthState(
          isAuthenticated: true,
          isInitialized: true,
          user: result.data,
        );
        return;
      }
    }
    
    state = state.copyWith(isLoading: false, isInitialized: true);
  }

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    final result = await _api.login(username: username, password: password);
    
    if (result.isSuccess) {
      state = AuthState(
        isAuthenticated: true,
        isInitialized: true,
        user: result.data?.user,
      );
      return true;
    }
    
    state = state.copyWith(
      isLoading: false,
      error: result.error ?? '登录失败',
    );
    return false;
  }

  Future<bool> register({
    required String username,
    required String password,
    String? email,
    String? phone,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    
    final result = await _api.register(
      username: username,
      password: password,
      email: email,
      phone: phone,
    );
    
    if (result.isSuccess) {
      state = AuthState(
        isAuthenticated: true,
        isInitialized: true,
        user: result.data?.user,
      );
      return true;
    }
    
    state = state.copyWith(
      isLoading: false,
      error: result.error ?? '注册失败',
    );
    return false;
  }

  Future<void> logout() async {
    await _api.logout();
    state = AuthState(isAuthenticated: false, isInitialized: true);
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}
