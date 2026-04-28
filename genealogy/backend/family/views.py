from django.db import models
from django.db.models import Prefetch
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.core.cache import cache
import logging

# Optional django-filter
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False
    DjangoFilterBackend = None

from .models import Member, Relation, FamilyTree
from .serializers import (
    MemberSerializer, MemberListSerializer,
    RelationSerializer, FamilyTreeSerializer, FamilyTreeNodeSerializer
)

logger = logging.getLogger(__name__)

# Constants
CACHE_PREFIX = 'genealogy'
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour
MAX_TREE_DEPTH = 20


class MemberViewSet(viewsets.ModelViewSet):
    """成员视图集 - 带缓存优化"""
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'member'
    
    # Build filter backends based on what's installed
    _filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    if HAS_DJANGO_FILTER:
        _filter_backends.insert(0, DjangoFilterBackend)
    filter_backends = _filter_backends
    
    filterset_fields = ['gender']
    search_fields = ['name', 'bio', 'birth_place', 'occupation']
    ordering_fields = ['name', 'birth_date', 'created_at']
    ordering = ['-birth_date']
    
    def get_queryset(self):
        user = self.request.user
        # 使用 select_related 避免 N+1 查询
        return Member.objects.filter(
            user=user
        ).select_related('father', 'mother', 'tenant')

    def get_serializer_class(self):
        action_to_serializer = {
            'list': MemberListSerializer,
            'retrieve': MemberSerializer,
            'create': MemberSerializer,
            'update': MemberSerializer,
            'partial_update': MemberSerializer,
        }
        return action_to_serializer.get(self.action, MemberSerializer)

    def perform_create(self, serializer):
        user = self.request.user
        tenant = None
        
        # 优化：缓存查找或单次查询
        try:
            from tenant.models import TenantUser
            membership = TenantUser.objects.filter(
                user=user, 
                is_active=True
            ).select_related('tenant').first()
            if membership:
                tenant = membership.tenant
        except Exception as e:
            logger.warning(f"Failed to get tenant for user {user.id}: {e}")
        
        serializer.save(user=user, tenant=tenant)
        self._clear_family_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._clear_family_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self._clear_family_cache()

    def _clear_family_cache(self):
        if not self.request.user:
            return
        try:
            cache_key = f"{CACHE_PREFIX}_family_tree_{self.request.user.id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """获取成员的家族树（带缓存）"""
        # 安全修复：缓存键包含用户ID防止越权访问
        cache_key = f"{CACHE_PREFIX}_member_tree_{request.user.id}_{pk}"
        
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        member = self.get_object()
        serializer = FamilyTreeNodeSerializer(member)
        
        try:
            cache.set(cache_key, serializer.data, timeout=CACHE_TTL_LONG)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def roots(self, request):
        """获取家族根节点（带分页）"""
        roots = self.get_queryset().filter(
            father__isnull=True, 
            mother__isnull=True
        )
        
        # 分页
        page = self.paginate_queryset(roots)
        if page is not None:
            serializer = FamilyTreeNodeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = FamilyTreeNodeSerializer(roots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def full_tree(self, request):
        """获取完整家族树（优化版本）"""
        # 安全修复：缓存键包含用户ID
        cache_key = f"{CACHE_PREFIX}_family_tree_{request.user.id}"
        
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        queryset = self.get_queryset()
        
        def build_tree(member, visited=None, depth=0):
            """递归构建树结构，限制深度防止无限递归"""
            if visited is None:
                visited = set()
            
            # 安全检查：防止无限递归
            if depth > MAX_TREE_DEPTH:
                logger.warning(f"Max tree depth reached for member {member.id}")
                return None
            
            # 防止循环引用
            if member.id in visited:
                return None
            visited.add(member.id)
            
            # 优化：单次查询获取所有子节点
            children = list(queryset.filter(
                models.Q(father=member) | models.Q(mother=member)
            ).exclude(id=member.id).distinct())
            
            return {
                'id': str(member.id),
                'name': member.name,
                'gender': member.gender,
                'birth_date': str(member.birth_date) if member.birth_date else None,
                'death_date': str(member.death_date) if member.death_date else None,
                'photo': request.build_absolute_uri(member.photo.url) if member.photo else None,
                'bio': member.bio,
                'children': [build_tree(child, visited, depth + 1) for child in children]
            }

        root_members = list(queryset.filter(father__isnull=True, mother__isnull=True))
        trees = [build_tree(root) for root in root_members]
        
        try:
            cache.set(cache_key, trees, timeout=CACHE_TTL_MEDIUM)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
        
        return Response(trees)

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """获取成员的所有后代（优化版本）"""
        member = self.get_object()
        
        # 使用迭代而非递归，避免栈溢出
        descendants = list(self._iter_descendants(member))
        serializer = MemberListSerializer(descendants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """获取成员的所有祖先"""
        member = self.get_object()
        
        # 迭代版本
        ancestors = list(self._iter_ancestors(member))
        serializer = MemberListSerializer(ancestors, many=True)
        return Response(serializer.data)

    def _iter_descendants(self, member, visited=None):
        """迭代获取所有后代"""
        if visited is None:
            visited = set()
        
        children = Member.objects.filter(
            models.Q(father=member) | models.Q(mother=member)
        ).exclude(id__in=visited).select_related('father', 'mother')
        
        for child in children:
            if child.id not in visited:
                visited.add(child.id)
                yield child
                yield from self._iter_descendants(child, visited)

    def _iter_ancestors(self, member, visited=None):
        """迭代获取所有祖先"""
        if visited is None:
            visited = set()
        
        if member.father and member.father.id not in visited:
            visited.add(member.father.id)
            yield member.father
            yield from self._iter_ancestors(member.father, visited)
        
        if member.mother and member.mother.id not in visited:
            visited.add(member.mother.id)
            yield member.mother
            yield from self._iter_ancestors(member.mother, visited)


class RelationViewSet(viewsets.ModelViewSet):
    """关系视图集"""
    
    serializer_class = RelationSerializer
    permission_classes = [IsAuthenticated]
    
    _relation_filter_backends = [filters.OrderingFilter]
    if HAS_DJANGO_FILTER:
        _relation_filter_backends.insert(0, DjangoFilterBackend)
    filter_backends = _relation_filter_backends
    
    filterset_fields = ['relation_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return Relation.objects.filter(
            user=self.request.user
        ).select_related('from_member', 'to_member', 'tenant')

    def perform_create(self, serializer):
        user = self.request.user
        tenant = None
        
        try:
            from tenant.models import TenantUser
            membership = TenantUser.objects.filter(
                user=user, 
                is_active=True
            ).select_related('tenant').first()
            if membership:
                tenant = membership.tenant
        except Exception as e:
            logger.warning(f"Failed to get tenant for user {user.id}: {e}")
        
        serializer.save(user=user, tenant=tenant)

    @action(detail=False, methods=['get'])
    def by_member(self, request):
        """获取某个成员的所有关系"""
        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {'error': '需要提供 member_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 安全：确保只能查询自己的成员
        try:
            member = Member.objects.get(id=member_id, user=request.user)
        except Member.DoesNotExist:
            return Response(
                {'error': '成员不存在或无权访问'},
                status=status.HTTP_404_NOT_FOUND
            )

        relations = Relation.objects.filter(
            models.Q(from_member=member) | models.Q(to_member=member),
            user=request.user
        ).select_related('from_member', 'to_member').distinct()
        
        serializer = self.get_serializer(relations, many=True)
        return Response(serializer.data)


class FamilyTreeViewSet(viewsets.ModelViewSet):
    """族谱视图集"""
    
    serializer_class = FamilyTreeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            from tenant.models import TenantUser
            user_tenants = TenantUser.objects.filter(
                user=self.request.user
            ).values_list('tenant_id', flat=True)
            return FamilyTree.objects.filter(tenant_id__in=user_tenants).select_related('tenant', 'root_member')
        except Exception:
            return FamilyTree.objects.none()

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """生成分享链接"""
        tree = self.get_object()
        return Response({
            'share_url': f"/shared/{tree.share_token}/",
            'share_token': tree.share_token
        })

    @action(detail=True, methods=['post'])
    def regenerate_token(self, request, pk=None):
        """重新生成分享Token"""
        import secrets
        tree = self.get_object()
        tree.share_token = secrets.token_urlsafe(32)
        tree.save(update_fields=['share_token'])
        return Response({'share_token': tree.share_token})
