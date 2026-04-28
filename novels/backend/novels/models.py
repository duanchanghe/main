from django.db import models
from django.contrib.auth.models import User


class Novel(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('analyzing', 'AI分析中'),
        ('processing', '音频生成中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    GENRE_CHOICES = [
        ('fantasy', '玄幻'),
        ('urban', '都市'),
        ('xianxia', '仙侠'),
        ('wuxia', '武侠'),
        ('romance', '言情'),
        ('scifi', '科幻'),
        ('mystery', '悬疑'),
        ('historical', '历史'),
        ('other', '其他'),
    ]

    title = models.CharField('标题', max_length=200)
    author = models.CharField('作者', max_length=100, blank=True)
    file_path = models.FileField('文件路径', upload_to='novels/')
    content = models.TextField('文本内容', blank=True)
    genre = models.CharField('类型', max_length=20, choices=GENRE_CHOICES, default='other')
    setting = models.CharField('背景设定', max_length=100, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='novels')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_analysis = models.JSONField('AI分析结果', null=True, blank=True)
    analysis_completed_at = models.DateTimeField('分析完成时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '小说'
        verbose_name_plural = '小说'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Character(models.Model):
    """小说角色模型"""
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('unknown', '未知'),
    ]
    AGE_CHOICES = [
        ('young', '青年'),
        ('middle-aged', '中年'),
        ('elderly', '老年'),
        ('unknown', '未知'),
    ]
    ROLE_TYPE_CHOICES = [
        ('protagonist', '主角'),
        ('supporting', '配角'),
        ('antagonist', '反派'),
        ('minor', '次要人物'),
    ]

    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField('角色名称', max_length=100)
    role_type = models.CharField('角色类型', max_length=20, choices=ROLE_TYPE_CHOICES, default='supporting')
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, default='unknown')
    age = models.CharField('年龄', max_length=20, choices=AGE_CHOICES, default='unknown')
    
    personality = models.CharField('性格特征', max_length=200, blank=True)
    speaking_style = models.CharField('说话风格', max_length=100, blank=True)
    temperament = models.CharField('气质类型', max_length=100, blank=True)
    catchphrase = models.CharField('口头禅', max_length=200, blank=True)
    
    voice_id = models.CharField('音色ID', max_length=100, default='Chinese_Male_Neutral')
    default_emotion = models.CharField('默认情感', max_length=50, default='neutral')
    
    importance_score = models.IntegerField('重要程度', default=50)
    auto_detected = models.BooleanField('AI自动识别', default=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        unique_together = ['novel', 'name']

    def __str__(self):
        return f"{self.novel.title} - {self.name}"


class Scene(models.Model):
    """小说场景模型"""
    MOOD_CHOICES = [
        ('happy', '欢快'),
        ('tense', '紧张'),
        ('sad', '悲伤'),
        ('romantic', '浪漫'),
        ('mysterious', '神秘'),
        ('calm', '平静'),
        ('excited', '激动'),
        ('horror', '恐怖'),
    ]

    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='scenes')
    chapter_number = models.IntegerField('章节号', default=1)
    scene_id = models.IntegerField('场景序号', default=1)
    
    location = models.CharField('场景地点', max_length=200, blank=True)
    time_of_day = models.CharField('时间', max_length=50, blank=True)
    season = models.CharField('季节', max_length=50, blank=True)
    weather = models.CharField('天气', max_length=50, blank=True)
    
    atmosphere = models.TextField('氛围描述', blank=True)
    mood = models.CharField('情绪基调', max_length=50, choices=MOOD_CHOICES, default='calm')
    
    suggested_bgm = models.CharField('推荐BGM描述', max_length=500, blank=True)
    suggested_sfx = models.JSONField('推荐音效', null=True, blank=True)
    bgm_volume = models.FloatField('BGM音量', default=0.3)
    sfx_volume = models.FloatField('音效音量', default=0.5)
    
    narration_text = models.TextField('叙述段落', blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '场景'
        verbose_name_plural = '场景'
        ordering = ['novel', 'chapter_number', 'scene_id']

    def __str__(self):
        return f"{self.novel.title} - 第{self.chapter_number}章场景{self.scene_id}"


class AudioJob(models.Model):
    """音频生成任务模型"""
    STATUS_CHOICES = [
        ('queued', '排队中'),
        ('analyzing', 'AI分析中'),
        ('saving', '保存数据中'),
        ('generating', '音频生成中'),
        ('merging', '合并音频中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='audio_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_jobs')

    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField('进度', default=0)
    current_step = models.CharField('当前步骤', max_length=100, blank=True)

    use_multi_voice = models.BooleanField('多角色配音', default=True)
    use_bgm = models.BooleanField('背景音乐', default=True)
    use_sfx = models.BooleanField('音效', default=True)

    output_path = models.CharField('输出路径', max_length=500, blank=True)
    error_message = models.TextField('错误信息', blank=True)

    total_scenes = models.IntegerField('总场景数', default=0)
    completed_scenes = models.IntegerField('已完成场景', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        verbose_name = '音频任务'
        verbose_name_plural = '音频任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.novel.title} - {self.get_status_display()}"


class AudioSegment(models.Model):
    """音频片段模型"""
    job = models.ForeignKey(AudioJob, on_delete=models.CASCADE, related_name='segments')
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='audio_segments')

    output_path = models.CharField('音频路径', max_length=500)
    duration_ms = models.IntegerField('时长(毫秒)', default=0)

    sfx_applied = models.JSONField('应用的音效', null=True, blank=True)
    bgm_applied = models.CharField('应用的BGM', max_length=200, blank=True)

    status = models.CharField('状态', max_length=20, choices=[
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ], default='pending')

    error_message = models.TextField('错误信息', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '音频片段'
        verbose_name_plural = '音频片段'

    def __str__(self):
        return f"场景{self.scene.scene_id} - {self.get_status_display()}"


class Dialogue(models.Model):
    """对话片段模型"""
    EMOTION_CHOICES = [
        ('neutral', '中性'),
        ('happy', '开心'),
        ('sad', '悲伤'),
        ('angry', '愤怒'),
        ('fearful', '恐惧'),
        ('surprised', '惊讶'),
        ('tense', '紧张'),
        ('excited', '激动'),
        ('romantic', '浪漫'),
        ('mysterious', '神秘'),
    ]
    VOLUME_CHOICES = [
        ('normal', '正常'),
        ('loud', '大声'),
        ('whisper', '低声'),
        ('calling', '喊叫'),
    ]
    SPEED_CHOICES = [
        ('slow', '慢速'),
        ('normal', '正常'),
        ('fast', '快速'),
    ]

    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='dialogues')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='dialogues')

    text = models.TextField('对话内容')
    emotion = models.CharField('情感', max_length=20, choices=EMOTION_CHOICES, default='neutral')
    volume = models.CharField('音量', max_length=20, choices=VOLUME_CHOICES, default='normal')
    speed = models.CharField('语速', max_length=20, choices=SPEED_CHOICES, default='normal')

    special_effects = models.CharField('特殊效果', max_length=500, blank=True)

    sfx_timing = models.JSONField('音效时机', null=True, blank=True)
    order = models.IntegerField('顺序', default=0)

    audio_path = models.CharField('音频路径', max_length=500, blank=True)
    duration_ms = models.IntegerField('时长(毫秒)', default=0, help_text='语音实际时长')

    class Meta:
        verbose_name = '对话'
        verbose_name_plural = '对话'
        ordering = ['order']

    def __str__(self):
        return f"{self.character.name}: {self.text[:30]}..."
