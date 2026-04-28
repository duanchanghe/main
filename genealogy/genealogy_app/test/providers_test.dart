import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:genealogy_app/providers/providers.dart';

void main() {
  group('AuthState', () {
    test('initial state is unauthenticated', () {
      final state = AuthState();
      
      expect(state.isAuthenticated, false);
      expect(state.isLoading, false);
      expect(state.isInitialized, false);
      expect(state.user, isNull);
      expect(state.error, isNull);
    });

    test('copyWith creates new state correctly', () {
      final state = AuthState();
      final newState = state.copyWith(
        isAuthenticated: true,
        isLoading: true,
      );

      expect(newState.isAuthenticated, true);
      expect(newState.isLoading, true);
      expect(newState.isInitialized, false); // unchanged
      expect(newState.user, isNull); // unchanged
    });

    test('copyWith preserves original values', () {
      final state = AuthState(isAuthenticated: true);
      final newState = state.copyWith(isLoading: true);

      expect(newState.isAuthenticated, true);
      expect(newState.isLoading, true);
    });
  });

  group('FamilyState', () {
    test('initial state has empty members', () {
      final state = FamilyState();
      
      expect(state.members, isEmpty);
      expect(state.familyTrees, isEmpty);
      expect(state.isLoading, false);
      expect(state.hasMore, true);
      expect(state.currentPage, 1);
    });

    test('copyWith updates members correctly', () {
      final state = FamilyState();
      final newState = state.copyWith(
        members: [],
        isLoading: true,
        hasMore: false,
      );

      expect(newState.members, isEmpty);
      expect(newState.isLoading, true);
      expect(newState.hasMore, false);
      expect(newState.currentPage, 1); // unchanged
    });
  });
}
