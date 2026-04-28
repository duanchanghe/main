from django.contrib import admin
from .models import Tenant, TenantUser, Invitation


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'plan', 'is_active', 'member_count', 'user_count', 'created_at')
    list_filter = ('plan', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'domain')
    readonly_fields = ('id', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

    def member_count(self, obj):
        from family.models import Member
        return Member.objects.filter(tenant=obj).distinct().count()
    member_count.short_description = '成员数'

    def user_count(self, obj):
        return obj.users.filter(is_active=True).count()
    user_count.short_description = '用户数'


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at', 'tenant')
    search_fields = ('user__username', 'user__email', 'tenant__name')
    readonly_fields = ('id', 'joined_at')
    raw_id_fields = ('user', 'invited_by')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'tenant', 'role', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'role', 'created_at', 'tenant')
    search_fields = ('email', 'tenant__name')
    readonly_fields = ('id', 'token', 'created_at')
    date_hierarchy = 'created_at'
    
    actions = ['expire_invitations', 'cancel_invitations']
    
    @admin.action(description='将选中邀请设为已过期')
    def expire_invitations(self, request, queryset):
        queryset.update(status=Invitation.Status.EXPIRED)
    
    @admin.action(description='取消选中邀请')
    def cancel_invitations(self, request, queryset):
        queryset.update(status=Invitation.Status.CANCELLED)
