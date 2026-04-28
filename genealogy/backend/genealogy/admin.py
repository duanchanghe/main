from django.contrib import admin
from django.contrib.auth.models import Group, User

# 自定义 Admin 站点
admin.site.site_header = '家谱管理系统'
admin.site.site_title = '家谱管理'
admin.site.index_title = '管理后台'

# 移除不需要的默认模型
# admin.site.unregister(Group)
