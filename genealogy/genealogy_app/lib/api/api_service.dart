import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

/// API Service 配置
class ApiConfig {
  /// 根据平台选择正确的 API 地址
  static String get baseUrl {
    if (kDebugMode) {
      // 开发环境：根据平台选择
      return 'http://10.0.2.2:8000/api'; // Android 模拟器
      // return 'http://localhost:8000/api'; // iOS 模拟器
      // return 'http://192.168.1.x:8000/api'; // 真机调试，使用电脑IP
    }
    // 生产环境
    return 'https://api.genealogy.com/api';
  }
  
  /// 连接超时时间
  static const Duration connectTimeout = Duration(seconds: 30);
  
  /// 接收超时时间
  static const Duration receiveTimeout = Duration(seconds: 30);
  
  /// 发送超时时间
  static const Duration sendTimeout = Duration(seconds: 30);
}

class ApiService {
  late final Dio _dio;
  late final Dio _tokenRefreshDio;
  String? _accessToken;
  String? _refreshToken;
  SharedPreferences? _prefs;
  bool _isRefreshing = false;

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      sendTimeout: ApiConfig.sendTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    // 单独的 Dio 实例用于 token 刷新，避免循环
    _tokenRefreshDio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
    ));

    _setupInterceptors();
    _initPrefs();
  }

  Future<void> _initPrefs() async {
    _prefs = await SharedPreferences.getInstance();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // 添加认证 token
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        // 添加请求ID用于追踪
        options.headers['X-Request-ID'] = DateTime.now().millisecondsSinceEpoch.toString();
        return handler.next(options);
      },
      onResponse: (response, handler) {
        // 成功响应处理 - 保存到缓存
        _saveResponseToCache(response);
        return handler.next(response);
      },
      onError: (error, handler) async {
        // 处理 401 错误，尝试刷新 token
        if (error.response?.statusCode == 401) {
          final refreshed = await _refreshTokenSafely();
          if (refreshed) {
            // 重试原请求
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $_accessToken';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } catch (e) {
              return handler.next(error);
            }
          }
        }
        return handler.next(error);
      },
    ));
  }

  /// 安全的刷新 token（防止并发刷新）
  Future<bool> _refreshTokenSafely() async {
    if (_refreshToken == null) return false;
    
    // 如果正在刷新，等待完成
    if (_isRefreshing) {
      await Future.delayed(const Duration(milliseconds: 500));
      return _accessToken != null;
    }
    
    _isRefreshing = true;
    
    try {
      final response = await _tokenRefreshDio.post(
        '/accounts/refresh/',
        data: {'refresh': _refreshToken},
        options: Options(headers: {}),
      );
      
      if (response.statusCode == 200 && response.data != null) {
        _accessToken = response.data['access'] as String?;
        if (_accessToken != null) {
          await saveTokens(_accessToken!, _refreshToken!);
          return true;
        }
      }
      return false;
    } catch (e) {
      // 刷新失败，清除 token
      await clearTokens();
      return false;
    } finally {
      _isRefreshing = false;
    }
  }

  /// 保存响应到缓存
  Future<void> _saveResponseToCache(Response response) async {
    if (response.requestOptions.method != 'GET' || 
        response.statusCode != 200 ||
        _prefs == null) {
      return;
    }
    
    try {
      final key = _cacheKey(
        response.requestOptions.path, 
        response.requestOptions.queryParameters,
      );
      final data = jsonEncode(response.data);
      await _prefs!.setString(key, data);
    } catch (e) {
      debugPrint('Cache save error: $e');
    }
  }

  /// 从缓存读取数据
  Future<Map<String, dynamic>?> _readFromCache(String path, Map<String, dynamic>? params) async {
    if (_prefs == null) return null;
    
    try {
      final key = _cacheKey(path, params);
      final data = _prefs!.getString(key);
      if (data != null) {
        return jsonDecode(data) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint('Cache read error: $e');
    }
    return null;
  }

  String _cacheKey(String path, Map<String, dynamic>? params) {
    final paramStr = params?.entries.map((e) => '${e.key}=${e.value}').join('&') ?? '';
    return 'cache_${path}_$paramStr'.hashCode.toString();
  }

  // ============ Token 管理 ============
  
  Future<void> loadTokens() async {
    _prefs ??= await SharedPreferences.getInstance();
    _accessToken = _prefs!.getString('access_token');
    _refreshToken = _prefs!.getString('refresh_token');
  }

  Future<void> saveTokens(String access, String refresh) async {
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.setString('access_token', access);
    await _prefs!.setString('refresh_token', refresh);
    _accessToken = access;
    _refreshToken = refresh;
  }

  Future<void> clearTokens() async {
    _prefs ??= await SharedPreferences.getInstance();
    await _prefs!.remove('access_token');
    await _prefs!.remove('refresh_token');
    _accessToken = null;
    _refreshToken = null;
  }

  bool get isAuthenticated => _accessToken != null;

  // ============ Auth Endpoints ============
  
  Future<ApiResult<AuthResponse>> register({
    required String username,
    required String password,
    String? email,
    String? phone,
  }) async {
    try {
      final response = await _dio.post('/accounts/register/', data: {
        'username': username,
        'password': password,
        if (email != null) 'email': email,
        if (phone != null) 'phone': phone,
      });
      
      if (response.data == null) {
        return ApiResult.error('注册失败：无响应数据');
      }
      
      final authResponse = AuthResponse.fromJson(response.data);
      await saveTokens(authResponse.tokens.access, authResponse.tokens.refresh);
      return ApiResult.success(authResponse);
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('Register error: $e');
      return ApiResult.error('注册失败: $e');
    }
  }

  Future<ApiResult<AuthResponse>> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await _dio.post('/accounts/login/', data: {
        'username': username,
        'password': password,
      });
      
      if (response.data == null) {
        return ApiResult.error('登录失败：无响应数据');
      }
      
      final authResponse = AuthResponse.fromJson(response.data);
      await saveTokens(authResponse.tokens.access, authResponse.tokens.refresh);
      return ApiResult.success(authResponse);
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('Login error: $e');
      return ApiResult.error('登录失败: $e');
    }
  }

  Future<void> logout() async {
    try {
      if (_refreshToken != null) {
        await _dio.post('/accounts/logout/', data: {
          'refresh': _refreshToken,
        });
      }
    } catch (_) {
      // 忽略登出错误
    } finally {
      await clearTokens();
    }
  }

  Future<ApiResult<User>> getCurrentUser() async {
    try {
      final response = await _dio.get('/accounts/me/');
      
      if (response.data == null) {
        return ApiResult.error('获取用户信息失败：无响应数据');
      }
      
      return ApiResult.success(User.fromJson(response.data));
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('GetUser error: $e');
      return ApiResult.error('获取用户信息失败: $e');
    }
  }

  // ============ Member Endpoints ============
  
  Future<ApiResult<List<Member>>> getMembers({
    int page = 1,
    int pageSize = 20,
    String? search,
    String? gender,
    String? ordering,
  }) async {
    try {
      final response = await _dio.get(
        '/family/members/',
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (search != null && search.isNotEmpty) 'search': search,
          if (gender != null && gender.isNotEmpty) 'gender': gender,
          if (ordering != null && ordering.isNotEmpty) 'ordering': ordering,
        },
      );
      
      if (response.data == null) {
        return ApiResult.error('加载成员失败：无响应数据');
      }
      
      final List<dynamic> results = response.data['results'] ?? response.data;
      final members = results.map((e) => Member.fromJson(e as Map<String, dynamic>)).toList();
      return ApiResult.success(members, hasMore: response.data['next'] != null);
      
    } on DioException catch (e) {
      // 网络错误时尝试从缓存读取
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout) {
        final cached = await _readFromCache('/family/members/', {
          'page': page.toString(),
          'page_size': pageSize.toString(),
        });
        if (cached != null) {
          final List<dynamic> results = cached['results'] ?? cached;
          final members = results.map((e) => Member.fromJson(e as Map<String, dynamic>)).toList();
          return ApiResult.success(members, hasMore: cached['next'] != null);
        }
      }
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('GetMembers error: $e');
      return ApiResult.error('加载成员失败: $e');
    }
  }

  Future<ApiResult<Member>> getMember(String id) async {
    try {
      final response = await _dio.get('/family/members/$id/');
      
      if (response.data == null) {
        return ApiResult.error('获取成员详情失败：无响应数据');
      }
      
      return ApiResult.success(Member.fromJson(response.data));
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('GetMember error: $e');
      return ApiResult.error('获取成员详情失败: $e');
    }
  }

  Future<ApiResult<Member>> createMember(Member member) async {
    try {
      final response = await _dio.post('/family/members/', data: member.toJson());
      
      if (response.data == null) {
        return ApiResult.error('创建成员失败：无响应数据');
      }
      
      return ApiResult.success(Member.fromJson(response.data));
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('CreateMember error: $e');
      return ApiResult.error('创建成员失败: $e');
    }
  }

  Future<ApiResult<Member>> updateMember(String id, Member member) async {
    try {
      final response = await _dio.put('/family/members/$id/', data: member.toJson());
      
      if (response.data == null) {
        return ApiResult.error('更新成员失败：无响应数据');
      }
      
      return ApiResult.success(Member.fromJson(response.data));
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('UpdateMember error: $e');
      return ApiResult.error('更新成员失败: $e');
    }
  }

  Future<ApiResult<void>> deleteMember(String id) async {
    try {
      await _dio.delete('/family/members/$id/');
      return ApiResult.success(null);
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('DeleteMember error: $e');
      return ApiResult.error('删除成员失败: $e');
    }
  }

  Future<ApiResult<List<Member>>> getFamilyTree() async {
    try {
      final response = await _dio.get('/family/members/full_tree/');
      
      if (response.data == null) {
        return ApiResult.error('加载族谱失败：无响应数据');
      }
      
      final List<dynamic> data = response.data is List ? response.data : [];
      final members = data.map((e) => Member.fromJson(e as Map<String, dynamic>)).toList();
      return ApiResult.success(members);
      
    } on DioException catch (e) {
      // 尝试从缓存读取
      final cached = await _readFromCache('/family/members/full_tree/', null);
      if (cached != null) {
        final List<dynamic> data = cached is List ? cached : cached['results'] ?? [];
        final members = data.map((e) => Member.fromJson(e as Map<String, dynamic>)).toList();
        return ApiResult.success(members);
      }
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('GetFamilyTree error: $e');
      return ApiResult.error('加载族谱失败: $e');
    }
  }

  // ============ Tenant Endpoints ============
  
  Future<ApiResult<Map<String, dynamic>>> getTenantUsage() async {
    try {
      final response = await _dio.get('/family/tenants/usage/');
      
      if (response.data == null) {
        return ApiResult.error('获取使用情况失败：无响应数据');
      }
      
      return ApiResult.success(response.data);
      
    } on DioException catch (e) {
      return ApiResult.error(_handleError(e));
    } catch (e) {
      debugPrint('GetTenantUsage error: $e');
      return ApiResult.error('获取使用情况失败: $e');
    }
  }

  // ============ Helper Methods ============
  
  String _handleError(DioException e) {
    if (e.response != null) {
      final data = e.response!.data;
      if (data is Map<String, dynamic>) {
        if (data['error'] != null) {
          if (data['error'] is Map) {
            return (data['error'] as Map)['message'] as String? ?? '请求失败';
          }
          return data['error'] as String? ?? '请求失败';
        }
        if (data['detail'] != null) {
          return data['detail'] as String? ?? '请求失败';
        }
      }
    }
    
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return '网络连接超时，请检查网络';
      case DioExceptionType.connectionError:
        return '无法连接到服务器，请检查网络';
      case DioExceptionType.cancel:
        return '请求已取消';
      default:
        return '请求失败，请稍后重试';
    }
  }
}

// ============ API Result ============

class ApiResult<T> {
  final T? data;
  final String? error;
  final bool hasMore;
  final bool isSuccess;

  ApiResult._({this.data, this.error, this.hasMore = false, required this.isSuccess});

  factory ApiResult.success(T? data, {bool hasMore = false}) {
    return ApiResult._(data: data, hasMore: hasMore, isSuccess: true);
  }

  factory ApiResult.error(String error) {
    return ApiResult._(error: error, isSuccess: false);
  }
}
