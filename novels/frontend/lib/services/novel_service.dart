import 'dart:io';
import 'package:dio/dio.dart';
import 'auth_service.dart';
import '../models/novel.dart';

class NovelService {
  final Dio _dio;
  final AuthService _authService;

  NovelService({required AuthService authService, Dio? dio})
      : _authService = authService,
        _dio = dio ?? Dio() {
    _dio.options.baseUrl = 'http://localhost:8000/api';
  }

  Map<String, String> get _headers => _authService.authHeaders;

  Future<List<Novel>> getNovels() async {
    try {
      final response = await _dio.get(
        '/novels/',
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => Novel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<Novel?> getNovel(int id) async {
    try {
      final response = await _dio.get(
        '/novels/$id/',
        options: Options(headers: _headers),
      );
      return Novel.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  Future<Novel?> uploadNovel({
    required String title,
    required String author,
    required File file,
  }) async {
    try {
      final formData = FormData.fromMap({
        'title': title,
        'author': author,
        'file_path': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
      });

      final response = await _dio.post(
        '/novels/',
        data: formData,
        options: Options(headers: {
          ..._headers,
          'Content-Type': 'multipart/form-data',
        }),
      );

      return Novel.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  Future<bool> deleteNovel(int id) async {
    try {
      await _dio.delete(
        '/novels/$id/',
        options: Options(headers: _headers),
      );
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> startAnalysis(int novelId) async {
    try {
      final response = await _dio.post(
        '/novels/$novelId/analyze/',
        options: Options(headers: _headers),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>?> getAnalysisResult(int novelId) async {
    try {
      final response = await _dio.get(
        '/novels/$novelId/analysis_result/',
        options: Options(headers: _headers),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<List<Character>> getCharacters(int novelId) async {
    try {
      final response = await _dio.get(
        '/novels/$novelId/characters/',
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => Character.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<bool> updateCharacter(
    int novelId,
    int characterId,
    String voiceId,
    String? defaultEmotion,
  ) async {
    try {
      final response = await _dio.put(
        '/novels/$novelId/update_character/',
        data: {
          'character_id': characterId,
          'voice_id': voiceId,
          if (defaultEmotion != null) 'default_emotion': defaultEmotion,
        },
        options: Options(headers: _headers),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<List<Scene>> getScenes(int novelId, {int? chapterNumber}) async {
    try {
      final path = chapterNumber != null
          ? '/novels/$novelId/scenes/?chapter=$chapterNumber'
          : '/novels/$novelId/scenes/';
      final response = await _dio.get(
        path,
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => Scene.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<ChapterInfo>> getChapters(int novelId) async {
    try {
      final response = await _dio.get(
        '/novels/$novelId/chapters/',
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => ChapterInfo.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<int?> generateChapter(
    int novelId,
    int chapterNumber, {
    bool multiVoice = true,
    bool bgm = true,
    bool sfx = true,
  }) async {
    try {
      final response = await _dio.post(
        '/novels/$novelId/generate_chapter/',
        data: {
          'chapter_number': chapterNumber,
          'multi_voice': multiVoice,
          'bgm': bgm,
          'sfx': sfx,
        },
        options: Options(headers: _headers),
      );
      return response.data['job_id'];
    } catch (e) {
      return null;
    }
  }

  Future<int?> generateAll(
    int novelId, {
    bool multiVoice = true,
    bool bgm = true,
    bool sfx = true,
  }) async {
    try {
      final response = await _dio.post(
        '/novels/$novelId/generate_all/',
        data: {
          'multi_voice': multiVoice,
          'bgm': bgm,
          'sfx': sfx,
        },
        options: Options(headers: _headers),
      );
      return response.data['job_id'];
    } catch (e) {
      return null;
    }
  }

  Future<List<AudioJob>> getJobs(int novelId) async {
    try {
      final response = await _dio.get(
        '/novels/$novelId/jobs/',
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => AudioJob.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<AudioJob>> getMyJobs() async {
    try {
      final response = await _dio.get(
        '/jobs/',
        options: Options(headers: _headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => AudioJob.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<AudioJob?> getJobStatus(int jobId) async {
    try {
      final response = await _dio.get(
        '/jobs/$jobId/',
        options: Options(headers: _headers),
      );
      return AudioJob.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  Future<bool> cancelJob(int jobId) async {
    try {
      await _dio.post(
        '/jobs/$jobId/cancel/',
        options: Options(headers: _headers),
      );
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<String?> getAudioUrl(int jobId) async {
    try {
      final response = await _dio.get(
        '/jobs/$jobId/audio/',
        options: Options(headers: _headers),
      );
      return response.data['url'];
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> getConversionProgress(int novelId) async {
    try {
      final response = await _dio.get(
        '/novels/$novelId/progress/',
        options: Options(headers: _headers),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, String>> getAvailableVoices() async {
    try {
      final response = await _dio.get(
        '/voices/',
        options: Options(headers: _headers),
      );
      return Map<String, String>.from(response.data);
    } catch (e) {
      return {};
    }
  }

  String getStreamUrl(int jobId) {
    return 'http://localhost:8000/api/jobs/$jobId/stream/';
  }

  String getAudioUrlFromPath(String? filePath) {
    if (filePath == null) return '';
    return 'http://localhost:8000/media/$filePath';
  }
}
