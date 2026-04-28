from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

from .health import health_check, health_detailed, readiness_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health checks
    path('health/', health_check, name='health_check'),
    path('health/detailed/', health_detailed, name='health_detailed'),
    path('ready/', readiness_check, name='readiness_check'),
    
    # Auth
    path('api/accounts/', include('accounts.urls')),
    
    # Multi-tenancy
    path('api/tenants/', include('tenant.urls')),
    
    # Family
    path('api/family/', include('family.urls')),
    
    # Audit
    path('api/audit/', include('audit.urls')),
    
    # AI
    path('api/ai/', include('ai.urls')),
]

# API Documentation (optional - requires drf-spectacular)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]
except ImportError:
    pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
