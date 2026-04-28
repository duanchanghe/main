import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:genealogy_app/screens/login_screen.dart';

void main() {
  group('LoginScreen Widget Tests', () {
    testWidgets('displays login form correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      // 验证表单元素
      expect(find.text('家谱应用'), findsOneWidget);
      expect(find.text('用户名'), findsOneWidget);
      expect(find.text('密码'), findsOneWidget);
      expect(find.text('登录'), findsOneWidget);
      expect(find.text('还没有账号？注册'), findsOneWidget);
    });

    testWidgets('shows validation errors for empty fields', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      // 点击登录按钮而不填写字段
      await tester.tap(find.text('登录'));
      await tester.pump();

      // 验证错误提示
      expect(find.text('请输入用户名'), findsOneWidget);
      expect(find.text('请输入密码'), findsOneWidget);
    });

    testWidgets('can navigate to register screen', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      // 点击注册链接
      await tester.tap(find.text('还没有账号？注册'));
      await tester.pumpAndSettle();

      // 验证跳转到注册页面
      expect(find.byType(LoginScreen), findsNothing);
    });

    testWidgets('password field is obscured by default', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      // 查找密码字段
      final passwordField = find.byType(TextFormField).at(1);
      final TextFormField widget = tester.widget(passwordField);
      
      // 验证密码被隐藏
      expect(widget.obscureText, true);
    });
  });

  group('RegisterScreen Widget Tests', () {
    testWidgets('displays registration form correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: RegisterScreen(),
          ),
        ),
      );

      // 验证表单元素
      expect(find.text('注册'), findsOneWidget);
      expect(find.text('用户名'), findsOneWidget);
      expect(find.text('邮箱 (可选)'), findsOneWidget);
      expect(find.text('确认密码'), findsOneWidget);
      expect(find.text('已有账号？登录'), findsOneWidget);
    });

    testWidgets('validates password length', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: RegisterScreen(),
          ),
        ),
      );

      // 输入短密码
      await tester.enterText(find.byType(TextFormField).at(2), '123');
      await tester.tap(find.text('注册'));
      await tester.pump();

      // 验证错误提示
      expect(find.text('密码至少6个字符'), findsOneWidget);
    });

    testWidgets('validates password confirmation', (WidgetTester tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: RegisterScreen(),
          ),
        ),
      );

      // 输入不同密码
      await tester.enterText(find.byType(TextFormField).at(2), 'password123');
      await tester.enterText(find.byType(TextFormField).at(3), 'differentpassword');
      await tester.tap(find.text('注册'));
      await tester.pump();

      // 验证错误提示
      expect(find.text('两次密码不一致'), findsOneWidget);
    });
  });
}
