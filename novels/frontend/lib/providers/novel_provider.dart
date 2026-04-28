import 'dart:io';
import 'package:flutter/foundation.dart';
import '../models/novel.dart';
import '../services/novel_service.dart';

class NovelProvider with ChangeNotifier {
  final NovelService _novelService;
  List<Novel> _novels = [];
  Novel? _currentNovel;
  bool _isLoading = false;
  String? _error;

  NovelProvider({required NovelService novelService})
      : _novelService = novelService;

  NovelService get novelService => _novelService;

  List<Novel> get novels => _novels;
  Novel? get currentNovel => _currentNovel;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadNovels() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    _novels = await _novelService.getNovels();

    _isLoading = false;
    notifyListeners();
  }

  Future<bool> uploadNovel({
    required String title,
    required String author,
    required File file,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final novel = await _novelService.uploadNovel(
      title: title,
      author: author,
      file: file,
    );

    if (novel != null) {
      _novels.insert(0, novel);
      _isLoading = false;
      notifyListeners();
      return true;
    }

    _error = '上传失败';
    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> deleteNovel(int id) async {
    final success = await _novelService.deleteNovel(id);
    if (success) {
      _novels.removeWhere((n) => n.id == id);
      notifyListeners();
    }
    return success;
  }

  Future<bool> startAnalysis(int novelId) async {
    return await _novelService.startAnalysis(novelId);
  }

  Future<Audiobook?> startConversion(int novelId, {
    bool multiVoice = true,
    bool bgm = true,
    bool sfx = true,
  }) async {
    return await _novelService.startConversion(
      novelId,
      multiVoice: multiVoice,
      bgm: bgm,
      sfx: sfx,
    );
  }

  Future<Map<String, dynamic>?> getConversionProgress(int novelId) async {
    return await _novelService.getConversionProgress(novelId);
  }

  Future<List<Character>> getCharacters(int novelId) async {
    return await _novelService.getCharacters(novelId);
  }

  Future<List<Scene>> getScenes(int novelId) async {
    return await _novelService.getScenes(novelId);
  }

  String getStreamUrl(int novelId) {
    return _novelService.getStreamUrl(novelId);
  }

  String getAudioUrl(String? filePath) {
    return _novelService.getAudioUrl(filePath);
  }
}
