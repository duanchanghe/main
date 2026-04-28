"""
AI API Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from .capabilities import (
    MemberBioGenerator,
    RelationRecommender,
    FamilyAnalyzer,
    NameMeaningAnalyzer,
    SearchAssistant,
)
from .services import get_default_ai_service

logger = logging.getLogger(__name__)


class AIBioGenerateView(APIView):
    """AI生成成员简介"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """生成单个成员的简介"""
        member_id = request.data.get('member_id')
        member_data = request.data.get('member_data', {})
        
        if not member_data:
            return Response(
                {'error': '需要提供成员数据'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 如果有 member_id，从数据库获取最新数据
        if member_id:
            from family.models import Member
            try:
                member = Member.objects.get(id=member_id, user=request.user)
                member_data = {
                    'name': member.name,
                    'gender': member.gender,
                    'birth_date': str(member.birth_date) if member.birth_date else None,
                    'birth_place': member.birth_place,
                    'occupation': member.occupation,
                    'education': member.education,
                    'father_name': member.father.name if member.father else None,
                    'mother_name': member.mother.name if member.mother else None,
                }
            except Member.DoesNotExist:
                return Response(
                    {'error': '成员不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        result = MemberBioGenerator.generate(member_data)
        
        if result.success:
            return Response({
                'success': True,
                'bio': result.content,
                'model': result.model,
                'usage': result.usage,
            })
        
        return Response({
            'success': False,
            'error': result.error,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIRelationRecommendView(APIView):
    """AI关系推荐"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """推荐家族关系"""
        from family.models import Member
        
        # 获取用户的所有成员
        members = Member.objects.filter(user=request.user).values(
            'id', 'name', 'gender', 'birth_date', 'birth_place', 'occupation'
        )
        
        if members.count() < 2:
            return Response({
                'error': '需要至少2个成员才能进行关系推荐'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        members_list = [dict(m) for m in members]
        result = RelationRecommender.recommend(members_list)
        
        return Response({
            'success': True,
            'recommendations': result.get('recommendations', []),
            'raw_suggestion': result.get('raw_suggestion'),
        })


class AIFamilyAnalysisView(APIView):
    """AI族谱分析"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """分析家族数据"""
        from family.models import Member
        from datetime import date
        
        # 获取用户的所有成员
        members = Member.objects.filter(user=request.user).select_related('father', 'mother')
        
        if members.count() < 3:
            return Response({
                'error': '需要至少3个成员才能进行分析'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 计算统计
        today = date.today()
        total = members.count()
        male_count = members.filter(gender='M').count()
        female_count = members.filter(gender='F').count()
        
        # 计算平均年龄
        total_age = 0
        alive_count = 0
        for m in members.filter(birth_date__isnull=False):
            age = today.year - m.birth_date.year
            if (m.birth_date.month, m.birth_date.day) > (today.month, today.day):
                age -= 1
            total_age += age
            alive_count += 1
        
        avg_age = round(total_age / alive_count, 1) if alive_count > 0 else 0
        
        # 计算世代
        oldest = members.filter(birth_date__isnull=False).order_by('birth_date').first()
        youngest = members.filter(birth_date__isnull=False).order_by('-birth_date').first()
        generations = 1
        if oldest and youngest and oldest.birth_date and youngest.birth_date:
            years_diff = youngest.birth_date.year - oldest.birth_date.year
            generations = max(1, years_diff // 25 + 1)
        
        stats = {
            'total_members': total,
            'male_count': male_count,
            'female_count': female_count,
            'average_age': avg_age,
            'generations': generations,
        }
        
        members_data = []
        for m in members[:50]:
            members_data.append({
                'id': str(m.id),
                'name': m.name,
                'gender': m.gender,
                'birth_date': str(m.birth_date) if m.birth_date else None,
                'birth_place': m.birth_place,
                'occupation': m.occupation,
                'education': m.education,
            })
        
        result = FamilyAnalyzer.analyze(members_data, stats)
        
        return Response({
            'success': True,
            'stats': stats,
            'analysis': result,
        })


class AINameAnalysisView(APIView):
    """AI姓名分析"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """分析姓名寓意"""
        name = request.data.get('name')
        gender = request.data.get('gender')
        
        if not name:
            return Response(
                {'error': '需要提供姓名'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = NameMeaningAnalyzer.analyze(name, gender)
        
        if result.success:
            return Response({
                'success': True,
                'analysis': result.content,
                'model': result.model,
            })
        
        return Response({
            'success': False,
            'error': result.error,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIChatView(APIView):
    """AI对话助手"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """回答关于家族的问题"""
        question = request.data.get('question')
        
        if not question:
            return Response(
                {'error': '需要提供问题'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 构建家族上下文
        from family.models import Member
        from datetime import date
        
        members = Member.objects.filter(user=request.user).select_related('father', 'mother')[:100]
        
        family_context = {
            'total_members': members.count(),
            'members': []
        }
        
        for m in members:
            family_context['members'].append({
                'name': m.name,
                'gender': '男' if m.gender == 'M' else '女',
                'birth_date': str(m.birth_date) if m.birth_date else None,
                'birth_place': m.birth_place,
                'occupation': m.occupation,
                'father': m.father.name if m.father else None,
                'mother': m.mother.name if m.mother else None,
            })
        
        result = SearchAssistant.answer(question, family_context)
        
        if result.success:
            return Response({
                'success': True,
                'answer': result.content,
                'model': result.model,
            })
        
        return Response({
            'success': False,
            'error': result.error,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIBatchBioView(APIView):
    """批量生成简介"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """批量为没有简介的成员生成简介"""
        from family.models import Member
        from .tasks import generate_member_bio_task
        
        # 获取没有简介的成员
        members_without_bio = Member.objects.filter(
            user=request.user,
            bio=''
        )[:20]
        
        if not members_without_bio:
            return Response({
                'success': True,
                'message': '所有成员都已有名简介',
                'generated': 0,
            })
        
        # 尝试同步生成（如果AI服务可用）
        ai_service = get_default_ai_service()
        generated = 0
        failed = 0
        
        for member in members_without_bio:
            member_data = {
                'name': member.name,
                'gender': member.gender,
                'birth_date': str(member.birth_date) if member.birth_date else None,
                'birth_place': member.birth_place,
                'occupation': member.occupation,
                'education': member.education,
                'father_name': member.father.name if member.father else None,
                'mother_name': member.mother.name if member.mother else None,
            }
            
            result = MemberBioGenerator.generate(member_data)
            
            if result.success and result.content:
                member.bio = result.content
                member.save(update_fields=['bio'])
                generated += 1
            else:
                failed += 1
        
        return Response({
            'success': True,
            'generated': generated,
            'failed': failed,
            'remaining': Member.objects.filter(user=request.user, bio='').count(),
        })


class AIServiceStatusView(APIView):
    """AI服务状态"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取AI服务状态"""
        ai_service = get_default_ai_service()
        
        return Response({
            'success': True,
            'provider': type(ai_service).__name__,
            'model': ai_service.model,
            'is_mock': isinstance(ai_service, type(get_default_ai_service).__bases__[0].__subclasses__()[2]),  # MockAIService
        })
