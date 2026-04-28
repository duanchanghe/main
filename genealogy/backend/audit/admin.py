from django.contrib import admin
from .models import AuditLog, ActivityLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'status', 'timestamp')
    list_filter = ('action', 'resource_type', 'status', 'timestamp')
    search_fields = ('user__username', 'resource_type', 'resource_id', 'ip_address')
    readonly_fields = ('id', 'user', 'tenant', 'action', 'resource_type', 'resource_id', 
                      'ip_address', 'user_agent', 'request_id', 'old_value', 'new_value',
                      'status', 'error_message', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'user', 'tenant', 'timestamp')
    list_filter = ('activity_type', 'timestamp', 'tenant')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('id', 'tenant', 'user', 'activity_type', 'title', 
                      'description', 'member', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
