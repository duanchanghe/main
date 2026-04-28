from django.urls import path
from . import views
from .ocr_views import OCRScanView, OCRPreviewView, OCRImportView, OCRServiceStatusView

urlpatterns = [
    # AI 功能
    path('bio/generate/', views.AIBioGenerateView.as_view(), name='ai-bio-generate'),
    path('bio/batch/', views.AIBatchBioView.as_view(), name='ai-bio-batch'),
    path('relations/recommend/', views.AIRelationRecommendView.as_view(), name='ai-relation-recommend'),
    path('family/analyze/', views.AIFamilyAnalysisView.as_view(), name='ai-family-analyze'),
    path('name/analyze/', views.AINameAnalysisView.as_view(), name='ai-name-analyze'),
    path('chat/', views.AIChatView.as_view(), name='ai-chat'),
    path('status/', views.AIServiceStatusView.as_view(), name='ai-status'),
    
    # OCR 扫描功能
    path('ocr/scan/', OCRScanView.as_view(), name='ocr-scan'),
    path('ocr/preview/', OCRPreviewView.as_view(), name='ocr-preview'),
    path('ocr/import/', OCRImportView.as_view(), name='ocr-import'),
    path('ocr/status/', OCRServiceStatusView.as_view(), name='ocr-status'),
]
