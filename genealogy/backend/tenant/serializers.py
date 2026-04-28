from rest_framework import serializers
from .models import Tenant, TenantUser, Invitation


class TenantSerializer(serializers.ModelSerializer):
    is_subscription_valid = serializers.BooleanField(read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    member_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'plan', 'plan_display',
            'max_members', 'max_storage_mb', 'max_users',
            'is_active', 'subscription_start', 'subscription_end',
            'domain', 'is_subscription_valid', 'member_count', 'user_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        from family.models import Member
        return Member.objects.filter(user__tenant_memberships__tenant=obj).distinct().count()
    
    def get_user_count(self, obj):
        return obj.users.filter(is_active=True).count()


class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['name', 'slug']
    
    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError('此URL标识已被使用')
        return value.lower().replace('-', '_')


class TenantUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'tenant', 'user', 'username', 'email',
            'role', 'role_display', 'is_active', 'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']


class InvitationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    invited_by_username = serializers.CharField(source='invited_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'tenant', 'tenant_name', 'email', 'role',
            'token', 'status', 'status_display', 
            'invited_by', 'invited_by_username',
            'expires_at', 'is_expired', 'created_at'
        ]
        read_only_fields = ['id', 'token', 'created_at']


class InvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['email', 'role']
    
    def create(self, validated_data):
        validated_data['tenant'] = self.context['tenant']
        validated_data['invited_by'] = self.context['request'].user
        from datetime import timedelta
        from django.utils import timezone
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        return super().create(validated_data)
