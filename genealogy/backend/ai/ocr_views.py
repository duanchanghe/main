"""
OCR API Views - 族谱扫描识别
"""
import os
import base64
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.base import ContentFile

from .ocr_service import get_ocr_service, parse_genealogy_text, GoogleVisionOCR, OpenAIVisionOCR

logger = logging.getLogger(__name__)


class OCRScanView(APIView):
    """族谱扫描 OCR 识别"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        """
        扫描族谱图片并识别成员信息
        
        支持两种上传方式:
        1. multipart/form-data: 上传图片文件
        2. application/json: 发送 base64 编码的图片
        """
        image_file = request.FILES.get('image')
        image_base64 = request.data.get('image_base64')
        
        if not image_file and not image_base64:
            return Response(
                {'error': '请上传图片或提供 base64 图片数据'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ocr_service = get_ocr_service()
            
            if image_file:
                # 从文件上传识别
                result = ocr_service.extract_text(image_file.temporary_file_path())
            else:
                # 从 base64 识别
                # 移除 data URL 前缀
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                result = ocr_service.extract_text_base64(image_base64)
            
            if not result.success:
                return Response(
                    {'success': False, 'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 如果有结构化数据，直接返回
            if result.structured_data:
                return Response({
                    'success': True,
                    'ocr_text': result.text,
                    'members': result.structured_data,
                    'confidence': result.confidence,
                })
            
            # 如果只有文本，使用 AI 解析
            if result.text:
                parsed = parse_genealogy_text(result.text)
                
                # 保存原始图片
                image_data = None
                if image_file:
                    image_data = image_file.read()
                elif image_base64:
                    if ',' in image_base64:
                        image_base64 = image_base64.split(',')[1]
                    image_data = base64.b64decode(image_base64)
                
                return Response({
                    'success': True,
                    'ocr_text': result.text,
                    'members': parsed.get('members', []),
                    'family_info': {
                        'family_name': parsed.get('family_name'),
                        'origin_place': parsed.get('origin_place'),
                        'notes': parsed.get('notes'),
                    },
                    'confidence': result.confidence,
                    'image_saved': image_data is not None,
                })
            
            return Response({
                'success': False,
                'error': '未能识别到文本内容',
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"OCR scan error: {e}")
            return Response(
                {'success': False, 'error': f'扫描失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OCRPreviewView(APIView):
    """OCR 预览 - 不保存数据，只识别"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """预览 OCR 识别结果，不保存到数据库"""
        return OCRScanView().post(request)


class OCRServiceStatusView(APIView):
    """OCR 服务状态"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取 OCR 服务配置状态"""
        ocr_provider = os.environ.get('OCR_PROVIDER', 'mock')
        
        status_info = {
            'provider': ocr_provider,
            'configured': ocr_provider != 'mock',
            'features': {
                'basic_text_extraction': True,
                'structured_data': ocr_provider in ['openai_vision'],
                'handwriting_recognition': ocr_provider == 'google_vision',
            }
        }
        
        if ocr_provider == 'google_vision':
            status_info['api_key_configured'] = bool(os.environ.get('GOOGLE_VISION_API_KEY'))
        elif ocr_provider == 'openai_vision':
            status_info['api_key_configured'] = bool(
                os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY')
            )
        
        return Response(status_info)


class OCRImportView(APIView):
    """批量导入族谱数据"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        从 OCR 识别的数据批量创建家族成员
        
        请求体:
        {
            "members": [
                {"name": "张三", "gender": "M", "birth_date": "1990-01-01", ...},
                ...
            ],
            "options": {
                "update_existing": true,  // 是否更新已存在的成员
                "generate_bios": true,     // 是否用 AI 生成简介
            }
        }
        """
        members_data = request.data.get('members', [])
        options = request.data.get('options', {})
        update_existing = options.get('update_existing', False)
        generate_bios = options.get('generate_bios', False)
        
        if not members_data:
            return Response(
                {'error': '请提供要导入的成员数据'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from family.models import Member
        from tenant.models import TenantUser
        
        created = 0
        updated = 0
        skipped = 0
        errors = []
        
        # 获取用户的租户
        try:
            membership = TenantUser.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('tenant').first()
            tenant = membership.tenant if membership else None
        except Exception:
            tenant = None
        
        for i, member_data in enumerate(members_data):
            try:
                name = member_data.get('name', '').strip()
                if not name:
                    errors.append(f"第{i+1}条: 姓名为空")
                    skipped += 1
                    continue
                
                # 检查是否已存在
                existing = Member.objects.filter(
                    user=request.user,
                    name=name,
                    birth_date=member_data.get('birth_date') or None
                ).first()
                
                if existing:
                    if update_existing:
                        # 更新现有成员
                        for key, value in member_data.items():
                            if key not in ['id', 'user', 'tenant'] and hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                    continue
                
                # 创建新成员
                member = Member.objects.create(
                    user=request.user,
                    tenant=tenant,
                    name=name,
                    gender=member_data.get('gender', 'M'),
                    birth_date=member_data.get('birth_date') or None,
                    birth_place=member_data.get('birth_place'),
                    occupation=member_data.get('occupation'),
                    bio=member_data.get('notes', ''),
                )
                
                # 处理父子关系
                father_name = member_data.get('father')
                if father_name:
                    father = Member.objects.filter(user=request.user, name=father_name).first()
                    if father:
                        member.father = father
                        member.save(update_fields=['father'])
                
                created += 1
                
            except Exception as e:
                logger.error(f"Failed to import member: {e}")
                errors.append(f"第{i+1}条: {str(e)}")
                skipped += 1
        
        # 如果需要生成简介
        if generate_bios and created > 0:
            from .tasks import batch_generate_bios_task
            # 异步生成简介
            if tenant:
                batch_generate_bios_task.delay(str(tenant.id))
        
        return Response({
            'success': True,
            'summary': {
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'total': len(members_data),
            },
            'errors': errors if errors else None,
        })
