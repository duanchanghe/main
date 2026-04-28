from django.db import models
from django.contrib.auth.models import User
from novels.models import Novel


class Audiobook(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    novel = models.OneToOneField(Novel, on_delete=models.CASCADE, related_name='audiobook')
    file_path = models.FileField('音频文件', upload_to='audiobooks/', null=True, blank=True)
    duration = models.IntegerField('时长(秒)', default=0)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField('进度(%)', default=0)
    error_message = models.TextField('错误信息', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '有声书'
        verbose_name_plural = '有声书'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.novel.title} - 有声书"
