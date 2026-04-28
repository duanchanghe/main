from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from tenant.models import Tenant, TenantUser
from family.models import Member

User = get_user_model()


class AuthenticationTests(APITestCase):
    """认证相关测试"""

    def test_user_registration(self):
        """测试用户注册"""
        response = self.client.post('/api/accounts/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_user_login(self):
        """测试用户登录"""
        User.objects.create_user(username='testuser', password='testpass123')
        
        response = self.client.post('/api/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_invalid_login(self):
        """测试无效登录"""
        response = self.client.post('/api/accounts/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_current_user(self):
        """测试获取当前用户"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/accounts/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')


class MemberAPITests(APITestCase):
    """成员管理 API 测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建租户
        self.tenant = Tenant.objects.create(
            name='Test Family',
            slug='test-family'
        )
        TenantUser.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantUser.Role.OWNER
        )

    def test_create_member(self):
        """测试创建成员"""
        response = self.client.post('/api/family/members/', {
            'name': '张三',
            'gender': 'M',
            'birth_date': '1990-01-01',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '张三')

    def test_list_members(self):
        """测试成员列表"""
        Member.objects.create(user=self.user, name='张三', gender='M')
        Member.objects.create(user=self.user, name='李四', gender='F')
        
        response = self.client.get('/api/family/members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_members_by_gender(self):
        """测试按性别筛选成员"""
        Member.objects.create(user=self.user, name='张三', gender='M')
        Member.objects.create(user=self.user, name='李四', gender='F')
        
        response = self.client.get('/api/family/members/', {'gender': 'M'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '张三')

    def test_search_members(self):
        """测试搜索成员"""
        Member.objects.create(user=self.user, name='张三', gender='M')
        Member.objects.create(user=self.user, name='李四', gender='F')
        
        response = self.client.get('/api/family/members/', {'search': '张三'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_member(self):
        """测试更新成员"""
        member = Member.objects.create(user=self.user, name='张三', gender='M')
        
        response = self.client.put(f'/api/family/members/{member.id}/', {
            'name': '张三丰',
            'gender': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '张三丰')

    def test_delete_member(self):
        """测试删除成员"""
        member = Member.objects.create(user=self.user, name='张三', gender='M')
        
        response = self.client.delete(f'/api/family/members/{member.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Member.objects.filter(id=member.id).exists())

    def test_member_relationships(self):
        """测试成员关系"""
        father = Member.objects.create(user=self.user, name='父亲', gender='M')
        child = Member.objects.create(user=self.user, name='儿子', gender='M', father=father)
        
        response = self.client.get(f'/api/family/members/{father.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['father_name'], None)


class TenantAPITests(APITestCase):
    """租户管理 API 测试"""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', 
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member', 
            password='testpass123'
        )
        self.client.force_authenticate(user=self.owner)

    def test_create_tenant(self):
        """测试创建租户"""
        response = self.client.post('/api/tenants/', {
            'name': '王氏家族',
            'slug': 'wang-family',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '王氏家族')
        
        # 验证创建者自动成为所有者
        tenant = Tenant.objects.get(slug='wang-family')
        self.assertTrue(
            TenantUser.objects.filter(tenant=tenant, user=self.owner, role=TenantUser.Role.OWNER).exists()
        )

    def test_list_user_tenants(self):
        """测试列出用户所属租户"""
        tenant1 = Tenant.objects.create(name='家族1', slug='family1')
        Tenant.objects.create(name='家族2', slug='family2')
        TenantUser.objects.create(tenant=tenant1, user=self.owner, role=TenantUser.Role.OWNER)
        
        response = self.client.get('/api/tenants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], '家族1')

    def test_get_tenant_usage(self):
        """测试获取租户使用情况"""
        tenant = Tenant.objects.create(name='Test', slug='test')
        TenantUser.objects.create(tenant=tenant, user=self.owner, role=TenantUser.Role.OWNER)
        
        response = self.client.get(f'/api/tenants/{tenant.slug}/usage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('members', response.data)
        self.assertIn('storage', response.data)
        self.assertIn('users', response.data)


class FamilyTreeAPITests(APITestCase):
    """族谱 API 测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        
        # 创建家族树结构
        self.grandfather = Member.objects.create(
            user=self.user, name='祖父', gender='M', birth_date='1940-01-01'
        )
        self.grandmother = Member.objects.create(
            user=self.user, name='祖母', gender='F', birth_date='1945-01-01'
        )
        self.father = Member.objects.create(
            user=self.user, name='父亲', gender='M', 
            birth_date='1970-01-01', father=self.grandfather, mother=self.grandmother
        )
        self.child = Member.objects.create(
            user=self.user, name='孩子', gender='M',
            birth_date='2000-01-01', father=self.father
        )

    def test_get_family_tree(self):
        """测试获取完整家族树"""
        response = self.client.get('/api/family/members/full_tree/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_member_descendants(self):
        """测试获取成员后代"""
        response = self.client.get(f'/api/family/members/{self.grandfather.id}/descendants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_get_member_ancestors(self):
        """测试获取成员祖先"""
        response = self.client.get(f'/api/family/members/{self.child.id}/ancestors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)


class PermissionTests(APITestCase):
    """权限测试"""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.member = User.objects.create_user(username='member', password='testpass123')
        self.other_user = User.objects.create_user(username='other', password='testpass123')
        
        self.tenant = Tenant.objects.create(name='Test', slug='test')
        TenantUser.objects.create(tenant=self.tenant, user=self.owner, role=TenantUser.Role.OWNER)
        TenantUser.objects.create(tenant=self.tenant, user=self.member, role=TenantUser.Role.MEMBER)
        
        self.member_obj = Member.objects.create(user=self.owner, name='Test', gender='M')

    def test_member_cannot_access_other_member(self):
        """测试成员不能访问其他成员的成员"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.get(f'/api/family/members/{self.member_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_delete_other_member(self):
        """测试成员不能删除其他成员的成员"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(f'/api/family/members/{self.member_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
