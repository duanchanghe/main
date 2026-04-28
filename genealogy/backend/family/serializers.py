from rest_framework import serializers
from .models import Member, Relation, FamilyTree


class MemberSerializer(serializers.ModelSerializer):
    """成员详情序列化器"""
    father_name = serializers.CharField(source='father.name', read_only=True, allow_null=True)
    mother_name = serializers.CharField(source='mother.name', read_only=True, allow_null=True)
    is_alive = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'tenant', 'name', 'gender', 'birth_date', 'death_date',
            'birth_place', 'photo', 'bio', 'father', 'mother',
            'father_name', 'mother_name', 'email', 'phone', 'address',
            'occupation', 'education', 'metadata', 'is_alive', 'age',
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
    
    def get_is_alive(self, obj):
        return obj.is_alive
    
    def get_age(self, obj):
        return obj.age
    
    def get_children_count(self, obj):
        return obj.children.count()


class MemberListSerializer(serializers.ModelSerializer):
    """简化版本，用于列表展示"""
    is_alive = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'name', 'gender', 'birth_date', 'death_date',
            'photo', 'is_alive', 'age'
        ]
    
    def get_is_alive(self, obj):
        return obj.is_alive
    
    def get_age(self, obj):
        return obj.age


class MemberCreateUpdateSerializer(serializers.ModelSerializer):
    """成员创建/更新序列化器"""
    
    class Meta:
        model = Member
        fields = [
            'name', 'gender', 'birth_date', 'death_date',
            'birth_place', 'photo', 'bio', 'father', 'mother',
            'email', 'phone', 'address', 'occupation', 'education', 'metadata'
        ]
    
    def validate(self, data):
        # 防止循环引用
        if 'father' in data and data['father']:
            father = data['father']
            if 'mother' in data and data['mother']:
                if father == data['mother']:
                    raise serializers.ValidationError('父亲和母亲不能是同一人')
        return data


class RelationSerializer(serializers.ModelSerializer):
    """关系序列化器"""
    from_member_name = serializers.CharField(source='from_member.name', read_only=True)
    to_member_name = serializers.CharField(source='to_member.name', read_only=True)
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    
    class Meta:
        model = Relation
        fields = [
            'id', 'tenant', 'from_member', 'to_member', 'relation_type',
            'relation_type_display', 'from_member_name', 'to_member_name',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class FamilyTreeSerializer(serializers.ModelSerializer):
    """族谱序列化器"""
    member_count = serializers.SerializerMethodField()
    root_member_name = serializers.CharField(source='root_member.name', read_only=True, allow_null=True)
    
    class Meta:
        model = FamilyTree
        fields = [
            'id', 'tenant', 'name', 'description', 'root_member',
            'root_member_name', 'is_public', 'share_token',
            'member_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'share_token', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return Member.objects.filter(tenant=obj.tenant).count()


class FamilyTreeNodeSerializer(serializers.ModelSerializer):
    """族谱树节点序列化器 - 递归结构"""
    children = serializers.SerializerMethodField()
    is_alive = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'name', 'gender', 'birth_date', 'death_date',
            'photo', 'bio', 'is_alive', 'children'
        ]
    
    def get_children(self, obj):
        from django.db.models import Q
        children = Member.objects.filter(
            Q(father=obj) | Q(mother=obj)
        ).exclude(id=obj.id).distinct()
        return FamilyTreeNodeSerializer(children, many=True).data
    
    def get_is_alive(self, obj):
        return obj.is_alive
