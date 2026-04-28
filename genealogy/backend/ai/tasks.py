"""
Celery tasks for AI operations
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_member_bio_task(self, member_id: str, member_data: dict):
    """异步生成成员简介"""
    from .capabilities import MemberBioGenerator
    
    try:
        result = MemberBioGenerator.generate(member_data)
        
        if result.success:
            # 更新成员简介
            from family.models import Member
            Member.objects.filter(id=member_id).update(bio=result.content)
            logger.info(f"Generated bio for member {member_id}")
            return {"success": True, "bio": result.content}
        else:
            logger.error(f"Failed to generate bio for member {member_id}: {result.error}")
            raise self.retry(exc=result.error, countdown=60)
            
    except Exception as e:
        logger.error(f"Error generating bio for member {member_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def recommend_relations_task(self, tenant_id: str):
    """异步推荐家族关系"""
    from .capabilities import RelationRecommender
    from tenant.models import Tenant
    from family.models import Member
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        members = Member.objects.filter(tenant=tenant).values(
            'id', 'name', 'gender', 'birth_date', 'birth_place', 'occupation'
        )
        
        members_list = [dict(m) for m in members]
        result = RelationRecommender.recommend(members_list)
        
        logger.info(f"Generated relation recommendations for tenant {tenant_id}")
        return {"success": True, "recommendations": result}
        
    except Exception as e:
        logger.error(f"Error recommending relations for tenant {tenant_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def analyze_family_task(self, tenant_id: str):
    """异步分析族谱"""
    from .capabilities import FamilyAnalyzer
    from tenant.models import Tenant
    from family.models import Member
    from django.db.models import Count, Avg
    from datetime import date
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        members = Member.objects.filter(tenant=tenant)
        
        # 计算统计
        today = date.today()
        members_data = members.values(
            'id', 'name', 'gender', 'birth_date', 'birth_place', 'occupation', 'education'
        )
        
        total = members.count()
        male_count = members.filter(gender='M').count()
        female_count = members.filter(gender='F').count()
        
        # 计算平均年龄
        total_age = sum(
            (today.year - m.birth_date.year - 
             ((today.month, today.day) < (m.birth_date.month, m.birth_date.day) if m.birth_date else False))
            for m in members.filter(birth_date__isnull=False)
        )
        alive_count = members.filter(birth_date__isnull=False).count()
        avg_age = total_age / alive_count if alive_count > 0 else 0
        
        stats = {
            'total_members': total,
            'male_count': male_count,
            'female_count': female_count,
            'average_age': round(avg_age, 1),
            'generations': 3,  # 需要更复杂的计算
        }
        
        members_list = [dict(m) for m in members_data]
        result = FamilyAnalyzer.analyze(members_list, stats)
        
        logger.info(f"Generated family analysis for tenant {tenant_id}")
        return {"success": True, "analysis": result}
        
    except Exception as e:
        logger.error(f"Error analyzing family for tenant {tenant_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def batch_generate_bios_task(self, tenant_id: str):
    """批量生成成员简介"""
    from .capabilities import MemberBioGenerator
    from tenant.models import Tenant
    from family.models import Member
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        members = Member.objects.filter(tenant=tenant, bio='')
        
        generated = 0
        failed = 0
        
        for member in members:
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
        
        logger.info(f"Batch generated {generated} bios, {failed} failed for tenant {tenant_id}")
        return {"success": True, "generated": generated, "failed": failed}
        
    except Exception as e:
        logger.error(f"Error batch generating bios for tenant {tenant_id}: {e}")
        raise self.retry(exc=e, countdown=60)
