class Novel {
  final int id;
  final String title;
  final String author;
  final String? filePath;
  final int uploadedBy;
  final String uploadedByUsername;
  final String status;
  final String? genre;
  final String? setting;
  final int? charactersCount;
  final int? scenesCount;
  final int? chaptersCount;
  final Audiobook? audiobook;
  final DateTime createdAt;

  Novel({
    required this.id,
    required this.title,
    this.author = '',
    this.filePath,
    required this.uploadedBy,
    required this.uploadedByUsername,
    required this.status,
    this.genre,
    this.setting,
    this.charactersCount,
    this.scenesCount,
    this.chaptersCount,
    this.audiobook,
    required this.createdAt,
  });

  factory Novel.fromJson(Map<String, dynamic> json) {
    return Novel(
      id: json['id'],
      title: json['title'],
      author: json['author'] ?? '',
      filePath: json['file_path'],
      uploadedBy: json['uploaded_by'],
      uploadedByUsername: json['uploaded_by_username'] ?? '',
      status: json['status'],
      genre: json['genre'],
      setting: json['setting'],
      charactersCount: json['characters_count'],
      scenesCount: json['scenes_count'],
      chaptersCount: json['chapters_count'],
      audiobook: json['audiobook'] != null
          ? Audiobook.fromJson(json['audiobook'])
          : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  bool get isAnalyzing => status == 'analyzing';
  bool get isProcessing => status == 'processing';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';
}

class ChapterInfo {
  final int chapterNumber;
  final int scenesCount;

  ChapterInfo({
    required this.chapterNumber,
    required this.scenesCount,
  });

  factory ChapterInfo.fromJson(Map<String, dynamic> json) {
    return ChapterInfo(
      chapterNumber: json['chapter_number'],
      scenesCount: json['scenes_count'],
    );
  }
}

class AudioJob {
  final int id;
  final int novelId;
  final String? novelTitle;
  final String status;
  final int progress;
  final String? currentStep;
  final String? outputPath;
  final String? errorMessage;
  final DateTime createdAt;
  final DateTime? completedAt;

  AudioJob({
    required this.id,
    required this.novelId,
    this.novelTitle,
    required this.status,
    this.progress = 0,
    this.currentStep,
    this.outputPath,
    this.errorMessage,
    required this.createdAt,
    this.completedAt,
  });

  factory AudioJob.fromJson(Map<String, dynamic> json) {
    return AudioJob(
      id: json['id'],
      novelId: json['novel_id'],
      novelTitle: json['novel_title'],
      status: json['status'],
      progress: json['progress'] ?? 0,
      currentStep: json['current_step'],
      outputPath: json['output_path'],
      errorMessage: json['error_message'],
      createdAt: DateTime.parse(json['created_at']),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : null,
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isProcessing => status == 'generating' || status == 'queued';
  bool get isFailed => status == 'failed';
  bool get isCancelled => status == 'cancelled';

  String get statusLabel {
    final labels = {
      'queued': '排队中',
      'analyzing': 'AI分析中',
      'saving': '保存数据中',
      'generating': '音频生成中',
      'merging': '合并音频中',
      'completed': '已完成',
      'failed': '失败',
      'cancelled': '已取消',
    };
    return labels[status] ?? status;
  }
}

class Audiobook {
  final int id;
  final int novelId;
  final String? filePath;
  final int duration;
  final String status;
  final int progress;
  final String? errorMessage;

  Audiobook({
    required this.id,
    required this.novelId,
    this.filePath,
    this.duration = 0,
    required this.status,
    this.progress = 0,
    this.errorMessage,
  });

  factory Audiobook.fromJson(Map<String, dynamic> json) {
    return Audiobook(
      id: json['id'],
      novelId: json['novel'],
      filePath: json['file_path'],
      duration: json['duration'] ?? 0,
      status: json['status'],
      progress: json['progress'] ?? 0,
      errorMessage: json['error_message'],
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isProcessing => status == 'processing';
  bool get isPending => status == 'pending';
  bool get isFailed => status == 'failed';
}

class Audiobook {
  final int id;
  final int novelId;
  final String? filePath;
  final int duration;
  final String status;
  final int progress;
  final String? errorMessage;

  Audiobook({
    required this.id,
    required this.novelId,
    this.filePath,
    this.duration = 0,
    required this.status,
    this.progress = 0,
    this.errorMessage,
  });

  factory Audiobook.fromJson(Map<String, dynamic> json) {
    return Audiobook(
      id: json['id'],
      novelId: json['novel'],
      filePath: json['file_path'],
      duration: json['duration'] ?? 0,
      status: json['status'],
      progress: json['progress'] ?? 0,
      errorMessage: json['error_message'],
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isProcessing => status == 'processing';
  bool get isPending => status == 'pending';
  bool get isFailed => status == 'failed';
}

class Character {
  final int id;
  final String name;
  final String roleType;
  final String gender;
  final String? age;
  final String? personality;
  final String? speakingStyle;
  final String? temperament;
  final String? catchphrase;
  final String voiceId;
  final String defaultEmotion;
  final int importanceScore;
  final bool autoDetected;

  Character({
    required this.id,
    required this.name,
    required this.roleType,
    required this.gender,
    this.age,
    this.personality,
    this.speakingStyle,
    this.temperament,
    this.catchphrase,
    required this.voiceId,
    this.defaultEmotion = 'neutral',
    this.importanceScore = 50,
    this.autoDetected = true,
  });

  factory Character.fromJson(Map<String, dynamic> json) {
    return Character(
      id: json['id'],
      name: json['name'],
      roleType: json['role_type'] ?? 'supporting',
      gender: json['gender'] ?? 'unknown',
      age: json['age'],
      personality: json['personality'],
      speakingStyle: json['speaking_style'],
      temperament: json['temperament'],
      catchphrase: json['catchphrase'],
      voiceId: json['voice_id'] ?? 'Chinese_Male_Neutral',
      defaultEmotion: json['default_emotion'] ?? 'neutral',
      importanceScore: json['importance_score'] ?? 50,
      autoDetected: json['auto_detected'] ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'role_type': roleType,
    'gender': gender,
    'age': age,
    'personality': personality,
    'speaking_style': speakingStyle,
    'temperament': temperament,
    'catchphrase': catchphrase,
    'voice_id': voiceId,
    'default_emotion': defaultEmotion,
    'importance_score': importanceScore,
  };

  String get roleTypeLabel {
    switch (roleType) {
      case 'protagonist':
        return '主角';
      case 'antagonist':
        return '反派';
      case 'supporting':
        return '配角';
      default:
        return '次要';
    }
  }

  String get genderLabel => gender == 'male' ? '男' : gender == 'female' ? '女' : '未知';
}

class Scene {
  final int id;
  final int chapterNumber;
  final int sceneId;
  final String location;
  final String timeOfDay;
  final String mood;
  final String suggestedBgm;
  final int dialoguesCount;
  final List<Dialogue> dialogues;

  Scene({
    required this.id,
    required this.chapterNumber,
    required this.sceneId,
    this.location = '',
    this.timeOfDay = '',
    this.mood = 'calm',
    this.suggestedBgm = '',
    this.dialoguesCount = 0,
    this.dialogues = const [],
  });

  factory Scene.fromJson(Map<String, dynamic> json) {
    return Scene(
      id: json['id'],
      chapterNumber: json['chapter_number'] ?? 1,
      sceneId: json['scene_id'] ?? 1,
      location: json['location'] ?? '',
      timeOfDay: json['time_of_day'] ?? '',
      mood: json['mood'] ?? 'calm',
      suggestedBgm: json['suggested_bgm'] ?? '',
      dialoguesCount: json['dialogues_count'] ?? 0,
      dialogues: json['dialogues'] != null
          ? (json['dialogues'] as List).map((d) => Dialogue.fromJson(d)).toList()
          : [],
    );
  }

  String get moodLabel {
    final moods = {
      'happy': '欢快',
      'tense': '紧张',
      'sad': '悲伤',
      'romantic': '浪漫',
      'mysterious': '神秘',
      'calm': '平静',
      'excited': '激动',
      'horror': '恐怖',
    };
    return moods[mood] ?? mood;
  }
}

class Dialogue {
  final int id;
  final int characterId;
  final String characterName;
  final String text;
  final String emotion;
  final String volume;
  final String speed;
  final String? specialEffects;
  final int order;
  final String? audioPath;

  Dialogue({
    required this.id,
    required this.characterId,
    required this.characterName,
    required this.text,
    this.emotion = 'neutral',
    this.volume = 'normal',
    this.speed = 'normal',
    this.specialEffects,
    this.order = 0,
    this.audioPath,
  });

  factory Dialogue.fromJson(Map<String, dynamic> json) {
    return Dialogue(
      id: json['id'],
      characterId: json['character'],
      characterName: json['character_name'] ?? '',
      text: json['text'] ?? '',
      emotion: json['emotion'] ?? 'neutral',
      volume: json['volume'] ?? 'normal',
      speed: json['speed'] ?? 'normal',
      specialEffects: json['special_effects'],
      order: json['order'] ?? 0,
      audioPath: json['audio_path'],
    );
  }
}
