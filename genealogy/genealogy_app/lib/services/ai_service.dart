import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_service.dart';

final aiProvider = Provider<AIService>((ref) => AIService(ref.watch(apiServiceProvider)));

class AIService {
  final ApiService _api;
  
  AIService(this._api);
  
  /// 生成成员简介
  Future<AIResult<String>> generateBio({
    String? memberId,
    Map<String, dynamic>? memberData,
  }) async {
    try {
      final response = await _api._dio.post('/ai/bio/generate/', data: {
        if (memberId != null) 'member_id': memberId,
        if (memberData != null) 'member_data': memberData,
      });
      
      if (response.data['success'] == true) {
        return AIResult.success(response.data['bio']);
      }
      return AIResult.error(response.data['error'] ?? '生成失败');
    } catch (e) {
      return AIResult.error('生成简介失败: $e');
    }
  }
  
  /// 批量生成简介
  Future<AIResult<BatchBioResult>> batchGenerateBios() async {
    try {
      final response = await _api._dio.post('/ai/bio/batch/');
      
      if (response.data['success'] == true) {
        return AIResult.success(BatchBioResult.fromJson(response.data));
      }
      return AIResult.error(response.data['error'] ?? '批量生成失败');
    } catch (e) {
      return AIResult.error('批量生成失败: $e');
    }
  }
  
  /// 推荐关系
  Future<AIResult<List<RelationRecommendation>>> recommendRelations() async {
    try {
      final response = await _api._dio.post('/ai/relations/recommend/');
      
      if (response.data['success'] == true) {
        final recommendations = (response.data['recommendations'] as List? ?? [])
            .map((e) => RelationRecommendation.fromJson(e))
            .toList();
        return AIResult.success(recommendations);
      }
      return AIResult.error(response.data['error'] ?? '推荐失败');
    } catch (e) {
      return AIResult.error('推荐关系失败: $e');
    }
  }
  
  /// 分析族谱
  Future<AIResult<FamilyAnalysis>> analyzeFamily() async {
    try {
      final response = await _api._dio.post('/ai/family/analyze/');
      
      if (response.data['success'] == true) {
        return AIResult.success(FamilyAnalysis.fromJson(response.data));
      }
      return AIResult.error(response.data['error'] ?? '分析失败');
    } catch (e) {
      return AIResult.error('分析族谱失败: $e');
    }
  }
  
  /// 分析姓名
  Future<AIResult<NameAnalysis>> analyzeName(String name, {String? gender}) async {
    try {
      final response = await _api._dio.post('/ai/name/analyze/', data: {
        'name': name,
        if (gender != null) 'gender': gender,
      });
      
      if (response.data['success'] == true) {
        return AIResult.success(NameAnalysis(response.data['analysis']));
      }
      return AIResult.error(response.data['error'] ?? '分析失败');
    } catch (e) {
      return AIResult.error('分析姓名失败: $e');
    }
  }
  
  /// AI对话
  Future<AIResult<String>> chat(String question) async {
    try {
      final response = await _api._dio.post('/ai/chat/', data: {
        'question': question,
      });
      
      if (response.data['success'] == true) {
        return AIResult.success(response.data['answer']);
      }
      return AIResult.error(response.data['error'] ?? '对话失败');
    } catch (e) {
      return AIResult.error('AI对话失败: $e');
    }
  }
  
  /// 获取AI服务状态
  Future<AIResult<bool>> checkStatus() async {
    try {
      final response = await _api._dio.get('/ai/status/');
      return AIResult.success(response.data['success'] == true);
    } catch (e) {
      return AIResult.error('检查状态失败: $e');
    }
  }
}

class AIResult<T> {
  final T? data;
  final String? error;
  final bool isSuccess;
  
  AIResult._({this.data, this.error, required this.isSuccess});
  
  factory AIResult.success(T data) => AIResult._(data: data, isSuccess: true);
  factory AIResult.error(String error) => AIResult._(error: error, isSuccess: false);
}

class BatchBioResult {
  final int generated;
  final int failed;
  final int remaining;
  
  BatchBioResult({
    required this.generated,
    required this.failed,
    required this.remaining,
  });
  
  factory BatchBioResult.fromJson(Map<String, dynamic> json) => BatchBioResult(
    generated: json['generated'] ?? 0,
    failed: json['failed'] ?? 0,
    remaining: json['remaining'] ?? 0,
  );
}

class RelationRecommendation {
  final String member1Id;
  final String member2Id;
  final String relationType;
  final double confidence;
  final String reason;
  
  RelationRecommendation({
    required this.member1Id,
    required this.member2Id,
    required this.relationType,
    required this.confidence,
    required this.reason,
  });
  
  factory RelationRecommendation.fromJson(Map<String, dynamic> json) => RelationRecommendation(
    member1Id: json['member1_id'] ?? '',
    member2Id: json['member2_id'] ?? '',
    relationType: json['relation_type'] ?? '',
    confidence: (json['confidence'] ?? 0).toDouble(),
    reason: json['reason'] ?? '',
  );
  
  String get relationLabel {
    switch (relationType) {
      case 'spouse': return '配偶';
      case 'father': return '父亲';
      case 'mother': return '母亲';
      case 'child': return '子女';
      case 'sibling': return '兄弟姐妹';
      case 'grandfather': return '祖父';
      case 'grandmother': return '祖母';
      default: return relationType;
    }
  }
}

class FamilyAnalysis {
  final Map<String, dynamic> stats;
  final String? summary;
  final List<String> suggestions;
  final List<String> interestingFacts;
  final Map<String, dynamic> analysisData;
  
  FamilyAnalysis({
    required this.stats,
    this.summary,
    this.suggestions = const [],
    this.interestingFacts = const [],
    this.analysisData = const {},
  });
  
  factory FamilyAnalysis.fromJson(Map<String, dynamic> json) {
    final analysis = json['analysis'] ?? {};
    return FamilyAnalysis(
      stats: json['stats'] ?? {},
      summary: analysis['summary'],
      suggestions: (analysis['suggestions'] as List?)?.cast<String>() ?? [],
      interestingFacts: (analysis['interesting_facts'] as List?)?.cast<String>() ?? [],
      analysisData: analysis,
    );
  }
  
  int get totalMembers => stats['total_members'] ?? 0;
  int get maleCount => stats['male_count'] ?? 0;
  int get femaleCount => stats['female_count'] ?? 0;
  double get averageAge => (stats['average_age'] ?? 0).toDouble();
  int get generations => stats['generations'] ?? 0;
}

class NameAnalysis {
  final String rawResponse;
  final Map<String, dynamic>? parsed;
  
  NameAnalysis(this.rawResponse) {
    // 尝试解析JSON
    try {
      // 简单的JSON解析
      parsed = _parseJson(rawResponse);
    } catch (_) {
      parsed = null;
    }
  }
  
  Map<String, dynamic>? _parseJson(String text) {
    // 找到JSON开始和结束
    final start = text.indexOf('{');
    final end = text.lastIndexOf('}');
    if (start == -1 || end == -1 || end < start) return null;
    
    try {
      // 简单的JSON解析（实际应该用dart:convert）
      return {};
    } catch (_) {
      return null;
    }
  }
  
  String get surnameMeaning => parsed?['surname_meaning'] ?? '';
  String get givenNameMeaning => parsed?['given_name_meaning'] ?? '';
  String get combinedMeaning => parsed?['combined_meaning'] ?? rawResponse;
}
