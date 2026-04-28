import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_service.dart';
import '../models/models.dart';
import 'auth_provider.dart';

final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

final familyProvider = StateNotifierProvider<FamilyNotifier, FamilyState>((ref) {
  return FamilyNotifier(ref.watch(apiServiceProvider));
});

class FamilyState {
  final List<Member> members;
  final List<Member> familyTrees;
  final bool isLoading;
  final bool hasMore;
  final int currentPage;
  final String? error;
  final String? searchQuery;

  FamilyState({
    this.members = const [],
    this.familyTrees = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.currentPage = 1,
    this.error,
    this.searchQuery,
  });

  FamilyState copyWith({
    List<Member>? members,
    List<Member>? familyTrees,
    bool? isLoading,
    bool? hasMore,
    int? currentPage,
    String? error,
    String? searchQuery,
  }) {
    return FamilyState(
      members: members ?? this.members,
      familyTrees: familyTrees ?? this.familyTrees,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      currentPage: currentPage ?? this.currentPage,
      error: error,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class FamilyNotifier extends StateNotifier<FamilyState> {
  final ApiService _api;

  FamilyNotifier(this._api) : super(FamilyState());

  Future<void> loadMembers({bool refresh = false}) async {
    if (state.isLoading) return;
    
    final page = refresh ? 1 : state.currentPage;
    
    if (refresh) {
      state = state.copyWith(isLoading: true, error: null);
    } else if (page > 1 && !state.hasMore) {
      return;
    }
    
    final result = await _api.getMembers(
      page: page,
      search: state.searchQuery,
    );

    if (result.isSuccess) {
      final newMembers = refresh 
          ? (result.data ?? [])
          : [...state.members, ...(result.data ?? [])];
      
      state = state.copyWith(
        members: newMembers,
        isLoading: false,
        hasMore: result.hasMore,
        currentPage: page + 1,
        error: null,
      );
    } else {
      state = state.copyWith(
        isLoading: false,
        error: result.error,
      );
    }
  }

  Future<void> refreshMembers() async {
    await loadMembers(refresh: true);
  }

  Future<void> search(String query) async {
    state = state.copyWith(
      searchQuery: query.isEmpty ? null : query,
      currentPage: 1,
      members: [],
      hasMore: true,
    );
    await loadMembers(refresh: true);
  }

  Future<void> loadFamilyTree() async {
    state = state.copyWith(isLoading: true, error: null);
    
    final result = await _api.getFamilyTree();

    if (result.isSuccess) {
      state = state.copyWith(
        familyTrees: result.data ?? [],
        isLoading: false,
        error: null,
      );
    } else {
      state = state.copyWith(
        isLoading: false,
        error: result.error,
      );
    }
  }

  Future<bool> createMember(Member member) async {
    final result = await _api.createMember(member);
    
    if (result.isSuccess && result.data != null) {
      state = state.copyWith(
        members: [result.data!, ...state.members],
      );
      return true;
    }
    
    state = state.copyWith(error: result.error);
    return false;
  }

  Future<bool> updateMember(String id, Member member) async {
    final result = await _api.updateMember(id, member);
    
    if (result.isSuccess && result.data != null) {
      final members = state.members.map((m) {
        return m.id?.toString() == id ? result.data! : m;
      }).toList();
      
      state = state.copyWith(members: members);
      return true;
    }
    
    state = state.copyWith(error: result.error);
    return false;
  }

  Future<bool> deleteMember(String id) async {
    final result = await _api.deleteMember(id);
    
    if (result.isSuccess) {
      final members = state.members.where((m) => m.id?.toString() != id).toList();
      state = state.copyWith(members: members);
      return true;
    }
    
    state = state.copyWith(error: result.error);
    return false;
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}
