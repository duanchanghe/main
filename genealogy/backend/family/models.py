import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Member(models.Model):
    """家庭成员模型 - 支持多租户"""
    
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 多租户支持
    tenant = models.ForeignKey('tenant.Tenant', on_delete=models.CASCADE, 
                               related_name='members', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='members')
    
    # 基本信息
    name = models.CharField(max_length=100, verbose_name='姓名', db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='性别')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    death_date = models.DateField(null=True, blank=True, verbose_name='逝世日期')
    birth_place = models.CharField(max_length=200, blank=True, verbose_name='出生地')
    
    # 照片和简介
    photo = models.ImageField(upload_to='photos/', null=True, blank=True, verbose_name='照片')
    bio = models.TextField(blank=True, verbose_name='个人简介')
    
    # 家族关系
    father = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='children_as_father', verbose_name='父亲')
    mother = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='children_as_mother', verbose_name='母亲')
    
    # 联系方式
    email = models.EmailField(blank=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    address = models.TextField(blank=True, verbose_name='地址')
    
    # 职业信息
    occupation = models.CharField(max_length=100, blank=True, verbose_name='职业')
    education = models.CharField(max_length=100, blank=True, verbose_name='学历')
    
    # 扩展数据 (JSON)
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展数据')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'members'
        verbose_name = '家庭成员'
        verbose_name_plural = '家庭成员'
        ordering = ['-birth_date']
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'birth_date']),
            models.Index(fields=['father']),
            models.Index(fields=['mother']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_alive(self):
        return self.death_date is None
    
    @property
    def age(self):
        if not self.birth_date:
            return None
        today = self.death_date or __import__('datetime').date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def children(self):
        return Member.objects.filter(
            models.Q(father=self) | models.Q(mother=self)
        ).exclude(id=self.id).distinct()
    
    @property
    def siblings(self):
        if not self.father and not self.mother:
            return Member.objects.none()
        return Member.objects.filter(
            models.Q(father=self.father) | models.Q(mother=self.mother)
        ).exclude(id=self.id).exclude(id=self.id).distinct()


class Relation(models.Model):
    """家庭关系模型 - 支持多租户"""
    
    RELATION_TYPES = [
        ('father', '父亲'),
        ('mother', '母亲'),
        ('spouse', '配偶'),
        ('child', '子女'),
        ('sibling', '兄弟姐妹'),
        ('grandfather', '祖父'),
        ('grandmother', '祖母'),
        ('grandchild', '孙子女'),
        ('uncle', '叔伯'),
        ('aunt', '姑姨'),
        ('cousin', '堂/表兄弟姐妹'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 多租户支持
    tenant = models.ForeignKey('tenant.Tenant', on_delete=models.CASCADE,
                               related_name='relations', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='relations')
    
    from_member = models.ForeignKey(Member, on_delete=models.CASCADE,
                                     related_name='relations_from')
    to_member = models.ForeignKey(Member, on_delete=models.CASCADE,
                                  related_name='relations_to')
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPES,
                                      verbose_name='关系类型')
    
    # 额外信息
    description = models.TextField(blank=True, verbose_name='关系描述')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'relations'
        verbose_name = '家庭关系'
        verbose_name_plural = '家庭关系'
        unique_together = ['from_member', 'to_member', 'relation_type']
        indexes = [
            models.Index(fields=['tenant', 'from_member']),
            models.Index(fields=['tenant', 'relation_type']),
        ]

    def __str__(self):
        return f'{self.from_member.name} - {self.get_relation_type_display()} - {self.to_member.name}'


class FamilyTree(models.Model):
    """族谱配置"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenant.Tenant', on_delete=models.CASCADE,
                               related_name='family_trees')
    
    name = models.CharField(max_length=200, verbose_name='族谱名称')
    description = models.TextField(blank=True, verbose_name='描述')
    root_member = models.ForeignKey(Member, on_delete=models.SET_NULL,
                                    null=True, related_name='as_root_of')
    
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    share_token = models.CharField(max_length=100, blank=True, verbose_name='分享Token')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'family_trees'
        verbose_name = '族谱'
        verbose_name_plural = '族谱'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            import secrets
            self.share_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
