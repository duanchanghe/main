import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/auth_service.dart';
import 'services/novel_service.dart';
import 'services/audio_service.dart';
import 'providers/auth_provider.dart';
import 'providers/novel_provider.dart';
import 'providers/audio_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const Novel2AudioApp());
}

class Novel2AudioApp extends StatelessWidget {
  const Novel2AudioApp({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();
    final novelService = NovelService(authService: authService);
    final audioService = AudioService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AuthProvider(authService: authService),
        ),
        ChangeNotifierProvider(
          create: (_) => NovelProvider(novelService: novelService),
        ),
        ChangeNotifierProvider(
          create: (_) => AudioProvider(audioService: audioService),
        ),
      ],
      child: MaterialApp(
        title: 'Novel2Audio',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: FutureBuilder<bool>(
          future: _checkAuth(authService),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }
            if (snapshot.data == true) {
              return const HomeScreen();
            }
            return const LoginScreen();
          },
        ),
      ),
    );
  }

  Future<bool> _checkAuth(AuthService authService) async {
    await authService.loadStoredToken();
    return authService.isAuthenticated;
  }
}
