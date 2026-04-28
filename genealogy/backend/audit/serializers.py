from rest_framework import serializers
from .models import AuditLog, ActivityLog


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'tenant', 'action', 'action_display',
            'resource_type', 'resource_id', 'ip_address', 'request_id',
            'old_value', 'new_value', 'status', 'error_message', 'timestamp'
        ]
        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True)
    activity_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'tenant', 'user', 'username', 'activity_type',
            'activity_display', 'title', 'description', 'member',
            'member_name', 'timestamp'
        ]
        read_only_fields = fields
