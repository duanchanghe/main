"""
API 序列化器
"""
import os
import chardet
from rest_framework import serializers
from django.contrib.auth.models import User
from django.conf import settings
from novels.models import Novel, Character, Scene, Dialogue, AudioJob


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class NovelUploadSerializer(serializers.Serializer):
    """小说上传序列化器 - 增强验证"""
    title = serializers.CharField(max_length=200, min_length=1)
    author = serializers.CharField(max_length=100, required=False, allow_blank=True)
    file = serializers.FileField(required=False)
    content = serializers.CharField(required=False, allow_blank=True)
    genre = serializers.ChoiceField(
        choices=Novel.GENRE_CHOICES,
        default='other',
        required=False
    )

    # 文件验证
    ALLOWED_EXTENSIONS = ['.txt']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def validate_file(self, value):
        if value is None:
            return value

        # 检查文件扩展名
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"不支持的文件类型: {ext}。仅支持: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # 检查文件大小
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"文件过大: {value.size / 1024 / 1024:.1f}MB。"
                f"最大允许: {self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            )

        return value

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("标题不能为空")
        # 去除首尾空白
        return value.strip()

    def validate_content(self, value):
        if value and len(value) < 100:
            raise serializers.ValidationError("内容过短，至少需要100个字符")
        return value

    def validate(self, attrs):
        file = attrs.get('file')
        content = attrs.get('content', '')

        # 必须提供文件或内容之一
        if not file and not content:
            raise serializers.ValidationError("必须提供文件或文本内容")

        # 如果提供文件，验证编码
        if file:
            try:
                # 检查文件编码
                content = file.read()
                detected = chardet.detect(content)
                if detected['confidence'] < 0.7:
                    attrs['_encoding_hint'] = 'utf-8'
                else:
                    attrs['_encoding_hint'] = detected['encoding']
                file.seek(0)
            except Exception as e:
                raise serializers.ValidationError(f"文件读取失败: {str(e)}")

        return attrs


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'name', 'role_type', 'gender', 'age', 'personality',
                  'speaking_style', 'temperament', 'catchphrase', 'voice_id',
                  'default_emotion', 'importance_score', 'auto_detected']
        read_only_fields = ['id', 'auto_detected']


class DialogueSerializer(serializers.ModelSerializer):
    character_name = serializers.CharField(source='character.name', read_only=True)

    class Meta:
        model = Dialogue
        fields = ['id', 'character', 'character_name', 'text', 'emotion', 'volume',
                  'speed', 'special_effects', 'sfx_timing', 'order', 'audio_path', 'duration_ms']


class SceneSerializer(serializers.ModelSerializer):
    dialogues = DialogueSerializer(many=True, read_only=True)

    class Meta:
        model = Scene
        fields = ['id', 'chapter_number', 'scene_id', 'location', 'time_of_day',
                  'season', 'weather', 'atmosphere', 'mood', 'suggested_bgm',
                  'suggested_sfx', 'bgm_volume', 'sfx_volume', 'dialogues']


class ChapterSerializer(serializers.Serializer):
    """章节摘要"""
    chapter_number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True)
    scenes_count = serializers.IntegerField()
    total_duration = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)


class AudioJobSerializer(serializers.ModelSerializer):
    novel_title = serializers.CharField(source='novel.title', read_only=True)

    class Meta:
        model = AudioJob
        fields = ['id', 'novel', 'novel_title', 'status', 'progress', 'current_step',
                  'use_multi_voice', 'use_bgm', 'use_sfx', 'output_path',
                  'error_message', 'total_scenes', 'completed_scenes',
                  'created_at', 'started_at', 'completed_at']
        read_only_fields = ['id', 'status', 'progress', 'output_path',
                           'error_message', 'completed_scenes', 'created_at',
                           'started_at', 'completed_at']


class ChapterAudioSerializer(serializers.Serializer):
    """章节音频"""
    chapter_number = serializers.IntegerField()
    title = serializers.CharField()
    scenes_count = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    output_path = serializers.CharField(allow_blank=True)
    minio_path = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    error_message = serializers.CharField(allow_blank=True)


class NovelSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    characters_count = serializers.SerializerMethodField()
    scenes_count = serializers.SerializerMethodField()
    chapters_count = serializers.SerializerMethodField()
    analysis_completed = serializers.SerializerMethodField()

    class Meta:
        model = Novel
        fields = ['id', 'title', 'author', 'file_path', 'content', 'uploaded_by', 'uploaded_by_username',
                  'status', 'genre', 'setting', 'characters_count', 'scenes_count',
                  'chapters_count', 'analysis_completed', 'ai_analysis',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_by', 'status', 'ai_analysis', 'created_at', 'updated_at']

    def validate_content(self, value):
        if value and len(value) > 0:
            # 检查内容是否为有效文本
            text = value.strip()
            if len(text) < 50:
                raise serializers.ValidationError("内容过短，至少需要50个字符")
            # 检查是否包含有效字符
            if not any('\u4e00' <= c <= '\u9fff' or c.isalnum() for c in text):
                raise serializers.ValidationError("内容不包含有效文本")
        return value

    def validate_title(self, value):
        if value:
            return value.strip()
        return value

    def get_characters_count(self, obj):
        return obj.characters.count()

    def get_scenes_count(self, obj):
        return obj.scenes.count()

    def get_chapters_count(self, obj):
        return obj.scenes.values('chapter_number').distinct().count()

    def get_analysis_completed(self, obj):
        return obj.status == 'completed' and obj.ai_analysis is not None
