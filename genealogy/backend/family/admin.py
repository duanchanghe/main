from django.contrib import admin
from .models import Member, Relation, FamilyTree


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'birth_date', 'death_date', 'tenant', 'created_at')
    list_filter = ('gender', 'created_at', 'tenant')
    search_fields = ('name', 'bio', 'birth_place', 'occupation')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'birth_date'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'gender', 'birth_date', 'death_date', 'birth_place')
        }),
        ('家族关系', {
            'fields': ('father', 'mother', 'tenant')
        }),
        ('详细信息', {
            'fields': ('photo', 'bio', 'email', 'phone', 'address', 'occupation', 'education')
        }),
        ('元数据', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'relation_type', 'tenant', 'created_at')
    list_filter = ('relation_type', 'created_at', 'tenant')
    search_fields = ('from_member__name', 'to_member__name')
    readonly_fields = ('id', 'created_at')


@admin.register(FamilyTree)
class FamilyTreeAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'is_public', 'created_at', 'updated_at')
    list_filter = ('is_public', 'created_at', 'tenant')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'share_token', 'created_at', 'updated_at')
