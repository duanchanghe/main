import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(familyProvider.notifier).loadMembers();
    });
  }

  @override
  Widget build(BuildContext context) {
    final familyState = ref.watch(familyProvider);
    final authState = ref.watch(authStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('家谱'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showSearchDialog(context),
            tooltip: '搜索成员',
          ),
          IconButton(
            icon: const Icon(Icons.account_circle),
            onPressed: () => _showProfileDialog(context),
            tooltip: '用户信息',
          ),
        ],
      ),
      drawer: _buildDrawer(context, authState),
      body: _buildBody(familyState),
      floatingActionButton: _buildFAB(context),
    );
  }

  Widget _buildFAB(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 快速操作按钮
        FloatingActionButton.small(
          heroTag: 'scan',
          onPressed: () => context.push('/scan'),
          backgroundColor: Colors.orange,
          tooltip: '扫描族谱',
          child: const Icon(Icons.document_scanner),
        ),
        const SizedBox(height: 8),
        FloatingActionButton.small(
          heroTag: 'ai',
          onPressed: () => context.push('/ai'),
          backgroundColor: Colors.purple,
          tooltip: 'AI助手',
          child: const Icon(Icons.smart_toy),
        ),
        const SizedBox(height: 8),
        FloatingActionButton.extended(
          heroTag: 'add',
          onPressed: () => context.push('/member/add'),
          icon: const Icon(Icons.person_add),
          label: const Text('添加成员'),
        ),
      ],
    );
  }

  Widget _buildDrawer(BuildContext context, AuthState authState) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          UserAccountsDrawerHeader(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.blue[600]!, Colors.blue[400]!],
              ),
            ),
            accountName: Text(authState.user?.username ?? ''),
            accountEmail: Text(authState.user?.email ?? ''),
            currentAccountPicture: CircleAvatar(
              backgroundColor: Colors.white,
              child: Text(
                authState.user?.username?.isNotEmpty == true 
                    ? authState.user!.username[0].toUpperCase() 
                    : 'U',
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.home),
            title: const Text('首页'),
            selected: true,
            onTap: () => Navigator.pop(context),
          ),
          ListTile(
            leading: const Icon(Icons.account_tree),
            title: const Text('族谱树'),
            onTap: () {
              Navigator.pop(context);
              context.push('/tree');
            },
          ),
          ListTile(
            leading: const Icon(Icons.people),
            title: const Text('成员列表'),
            onTap: () => Navigator.pop(context),
          ),
          ListTile(
            leading: const Icon(Icons.smart_toy),
            title: const Text('AI助手'),
            onTap: () {
              Navigator.pop(context);
              context.push('/ai');
            },
          ),
          ListTile(
            leading: const Icon(Icons.document_scanner),
            title: const Text('扫描族谱'),
            onTap: () {
              Navigator.pop(context);
              context.push('/scan');
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('设置'),
            onTap: () {
              Navigator.pop(context);
              _showSettingsDialog(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('退出登录'),
            onTap: () {
              Navigator.pop(context);
              ref.read(authStateProvider.notifier).logout();
              context.go('/login');
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBody(FamilyState state) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
            const SizedBox(height: 16),
            Text(state.error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => ref.read(familyProvider.notifier).loadMembers(),
              icon: const Icon(Icons.refresh),
              label: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (state.members.isEmpty) {
      return _buildEmptyState(context);
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(familyProvider.notifier).loadMembers(),
      child: Column(
        children: [
          // 统计卡片
          _buildStatsCard(state),
          // 成员列表
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: state.members.length,
              itemBuilder: (context, index) {
                final member = state.members[index];
                return _MemberCard(member: member);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.family_restroom, size: 100, color: Colors.blue[200]),
            const SizedBox(height: 24),
            Text(
              '欢迎使用家谱应用',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '开始记录您的家族历史',
              style: TextStyle(fontSize: 16, color: Colors.grey[500]),
            ),
            const SizedBox(height: 32),
            // 快速操作
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const Text(
                      '开始使用',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _buildQuickAction(
                          context,
                          icon: Icons.person_add,
                          label: '手动添加',
                          color: Colors.blue,
                          onTap: () => context.push('/member/add'),
                        ),
                        _buildQuickAction(
                          context,
                          icon: Icons.document_scanner,
                          label: '扫描族谱',
                          color: Colors.orange,
                          onTap: () => context.push('/scan'),
                        ),
                        _buildQuickAction(
                          context,
                          icon: Icons.smart_toy,
                          label: 'AI助手',
                          color: Colors.purple,
                          onTap: () => context.push('/ai'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // 使用提示
            Card(
              color: Colors.blue[50],
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.lightbulb, color: Colors.amber[700]),
                        const SizedBox(width: 8),
                        const Text(
                          '使用提示',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text('• 点击右下角按钮添加家族成员'),
                    const Text('• 使用扫描功能快速导入族谱'),
                    const Text('• AI助手可以帮您生成成员简介'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickAction(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(height: 8),
            Text(label, style: TextStyle(color: Colors.grey[700])),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsCard(FamilyState state) {
    final total = state.members.length;
    final male = state.members.where((m) => m.gender == 'M').length;
    final female = total - male;

    return Card(
      margin: const EdgeInsets.all(8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildStatItem('总人数', '$total', Icons.people, Colors.blue),
            _buildStatItem('男性', '$male', Icons.man, Colors.blue[700]!),
            _buildStatItem('女性', '$female', Icons.woman, Colors.pink[400]!),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey[600], fontSize: 12),
        ),
      ],
    );
  }

  void _showSearchDialog(BuildContext context) {
    showSearch(
      context: context,
      delegate: _MemberSearchDelegate(ref.read(familyProvider).members),
    );
  }

  void _showProfileDialog(BuildContext context) {
    final authState = ref.read(authStateProvider);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            CircleAvatar(
              backgroundColor: Colors.blue[100],
              child: Text(
                authState.user?.username?.isNotEmpty == true
                    ? authState.user!.username[0].toUpperCase()
                    : 'U',
              ),
            ),
            const SizedBox(width: 12),
            Text(authState.user?.username ?? '用户'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildInfoRow('用户名', authState.user?.username ?? '-'),
            _buildInfoRow('邮箱', authState.user?.email ?? '-'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 60,
            child: Text(
              '$label:',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  void _showSettingsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('设置'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.person),
              title: const Text('账户设置'),
              onTap: () {
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.palette),
              title: const Text('主题设置'),
              onTap: () {
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.notifications),
              title: const Text('通知设置'),
              onTap: () {
                Navigator.pop(context);
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }
}

class _MemberCard extends StatelessWidget {
  final Member member;

  const _MemberCard({required this.member});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: member.gender == 'M' ? Colors.blue[100] : Colors.pink[100],
          child: Icon(
            member.gender == 'M' ? Icons.man : Icons.woman,
            color: member.gender == 'M' ? Colors.blue : Colors.pink,
          ),
        ),
        title: Text(
          member.name,
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Text(
          _buildSubtitle(),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (member.birthDate != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _formatBirthYear(),
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ),
            const SizedBox(width: 8),
            Icon(
              member.isAlive == true ? Icons.favorite : Icons.favorite_border,
              color: member.isAlive == true ? Colors.red : Colors.grey,
              size: 20,
            ),
          ],
        ),
        onTap: () => context.push('/member/${member.id}'),
      ),
    );
  }

  String _buildSubtitle() {
    final parts = <String>[];
    if (member.fatherName != null) {
      parts.add('父: ${member.fatherName}');
    }
    if (member.occupation != null) {
      parts.add(member.occupation!);
    }
    return parts.isEmpty ? '' : parts.join(' • ');
  }

  String _formatBirthYear() {
    if (member.birthDate == null) return '';
    return member.birthDate!.year.toString();
  }
}

class _MemberSearchDelegate extends SearchDelegate<Member?> {
  final List<Member> members;

  _MemberSearchDelegate(this.members);

  @override
  List<Widget> buildActions(BuildContext context) {
    return [
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () => query = '',
      ),
    ];
  }

  @override
  Widget buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () => close(context, null),
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _buildSearchResults();
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    return _buildSearchResults();
  }

  Widget _buildSearchResults() {
    final results = members.where((m) {
      final queryLower = query.toLowerCase();
      return m.name.toLowerCase().contains(queryLower) ||
          (m.fatherName?.toLowerCase().contains(queryLower) ?? false) ||
          (m.occupation?.toLowerCase().contains(queryLower) ?? false);
    }).toList();

    if (results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('未找到 "$query" 相关成员'),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: results.length,
      itemBuilder: (context, index) {
        final member = results[index];
        return ListTile(
          leading: CircleAvatar(
            backgroundColor: member.gender == 'M' ? Colors.blue[100] : Colors.pink[100],
            child: Icon(
              member.gender == 'M' ? Icons.man : Icons.woman,
              color: member.gender == 'M' ? Colors.blue : Colors.pink,
            ),
          ),
          title: Text(member.name),
          subtitle: Text(member.fatherName != null ? '父亲: ${member.fatherName}' : ''),
          onTap: () {
            close(context, member);
            context.push('/member/${member.id}');
          },
        );
      },
    );
  }
}
