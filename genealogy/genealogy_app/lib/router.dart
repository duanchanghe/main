import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'providers/providers.dart';
import 'screens/screens.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation == '/login' || state.matchedLocation == '/register';

      if (!isAuthenticated && !isAuthRoute) {
        return '/login';
      }
      if (isAuthenticated && isAuthRoute) {
        return '/';
      }
      return null;
    },
    routes: [
      // 认证页面
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      
      // 首页
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      
      // 族谱浏览
      GoRoute(
        path: '/tree',
        builder: (context, state) => const FamilyTreeScreen(),
      ),
      
      // 成员管理
      GoRoute(
        path: '/member/add',
        builder: (context, state) => const MemberFormScreen(),
      ),
      GoRoute(
        path: '/member/:id',
        builder: (context, state) {
          final id = int.parse(state.pathParameters['id']!);
          return MemberFormScreen(memberId: id);
        },
      ),
      
      // AI 助手
      GoRoute(
        path: '/ai',
        builder: (context, state) => const AIAssistantScreen(),
      ),
      
      // 扫描族谱
      GoRoute(
        path: '/scan',
        builder: (context, state) => const GenealogyScanScreen(),
      ),
    ],
  );
});
