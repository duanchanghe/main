import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';
import '../models/models.dart';

class FamilyTreeScreen extends ConsumerStatefulWidget {
  const FamilyTreeScreen({super.key});

  @override
  ConsumerState<FamilyTreeScreen> createState() => _FamilyTreeScreenState();
}

class _FamilyTreeScreenState extends ConsumerState<FamilyTreeScreen> {
  final TransformationController _transformationController = TransformationController();
  double _currentScale = 1.0;
  
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(familyProvider.notifier).loadFamilyTree();
    });
  }

  @override
  void dispose() {
    _transformationController.dispose();
    super.dispose();
  }

  void _resetZoom() {
    _transformationController.value = Matrix4.identity();
    setState(() => _currentScale = 1.0);
  }

  void _zoomIn() {
    final currentScale = _transformationController.value.getMaxScaleOnAxis();
    final newScale = (currentScale * 1.2).clamp(0.5, 3.0);
    _transformationController.value = Matrix4.identity()..scale(newScale);
    setState(() => _currentScale = newScale);
  }

  void _zoomOut() {
    final currentScale = _transformationController.value.getMaxScaleOnAxis();
    final newScale = (currentScale / 1.2).clamp(0.5, 3.0);
    _transformationController.value = Matrix4.identity()..scale(newScale);
    setState(() => _currentScale = newScale);
  }

  @override
  Widget build(BuildContext context) {
    final familyState = ref.watch(familyProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('族谱树'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(familyProvider.notifier).loadFamilyTree(),
            tooltip: '刷新',
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) {
              switch (value) {
                case 'zoom_in':
                  _zoomIn();
                  break;
                case 'zoom_out':
                  _zoomOut();
                  break;
                case 'reset':
                  _resetZoom();
                  break;
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'zoom_in',
                child: ListTile(
                  leading: Icon(Icons.zoom_in),
                  title: Text('放大'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'zoom_out',
                child: ListTile(
                  leading: Icon(Icons.zoom_out),
                  title: Text('缩小'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'reset',
                child: ListTile(
                  leading: Icon(Icons.fit_screen),
                  title: Text('重置'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // 缩放指示器
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.grey[100],
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.remove),
                  onPressed: _zoomOut,
                  iconSize: 20,
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${(_currentScale * 100).toInt()}%',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: _zoomIn,
                  iconSize: 20,
                ),
              ],
            ),
          ),
          // 族谱视图
          Expanded(
            child: _buildBody(familyState),
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
              onPressed: () => ref.read(familyProvider.notifier).loadFamilyTree(),
              icon: const Icon(Icons.refresh),
              label: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (state.familyTrees.isEmpty) {
      return Center(
        child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.account_tree, size: 100, color: Colors.grey[300]),
              const SizedBox(height: 24),
              Text(
                '暂无族谱数据',
                style: TextStyle(fontSize: 20, color: Colors.grey[600]),
              ),
              const SizedBox(height: 8),
              Text(
                '请先添加家庭成员',
                style: TextStyle(color: Colors.grey[500]),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () => context.go('/'),
                icon: const Icon(Icons.person_add),
                label: const Text('添加成员'),
              ),
            ],
          ),
        ),
      );
    }

    return InteractiveViewer(
      transformationController: _transformationController,
      boundaryMargin: const EdgeInsets.all(200),
      minScale: 0.3,
      maxScale: 3.0,
      onInteractionUpdate: (details) {
        setState(() {
          _currentScale = _transformationController.value.getMaxScaleOnAxis();
        });
      },
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(48),
            child: Column(
              children: state.familyTrees.map((tree) => _buildTree(tree)).toList(),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTree(Member root) {
    return _TreeNode(member: root, depth: 0);
  }
}

class _TreeNode extends StatelessWidget {
  final Member member;
  final int depth;

  const _TreeNode({required this.member, required this.depth});

  @override
  Widget build(BuildContext context) {
    final children = member.children ?? [];

    return Column(
      children: [
        _MemberNode(member: member, depth: depth),
        if (children.isNotEmpty) ...[
          // 连接线
          CustomPaint(
            size: const Size(2, 30),
            painter: _LinePainter(),
          ),
          // 子节点
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: children.asMap().entries.map((entry) {
              final index = entry.key;
              final child = entry.value;
              final isFirst = index == 0;
              final isLast = index == children.length - 1;
              final total = children.length;
              final horizontalLineWidth = (total - 1) * 80.0;

              return Column(
                children: [
                  // 水平连接线
                  if (total > 1)
                    SizedBox(
                      height: 2,
                      width: horizontalLineWidth,
                      child: CustomPaint(
                        painter: _HorizontalLinePainter(
                          isFirst: isFirst,
                          isLast: isLast,
                          total: total,
                          index: index,
                        ),
                      ),
                    ),
                  // 垂直连接线
                  if (total > 1)
                    CustomPaint(
                      size: const Size(2, 15),
                      painter: _LinePainter(),
                    ),
                  _TreeNode(member: child, depth: depth + 1),
                ],
              );
            }).toList(),
          ),
        ],
      ],
    );
  }
}

class _LinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    canvas.drawLine(
      Offset(size.width / 2, 0),
      Offset(size.width / 2, size.height),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _HorizontalLinePainter extends CustomPainter {
  final bool isFirst;
  final bool isLast;
  final int total;
  final int index;

  _HorizontalLinePainter({
    required this.isFirst,
    required this.isLast,
    required this.total,
    required this.index,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey[400]!
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    // 画水平线
    canvas.drawLine(
      const Offset(0, 0),
      Offset(size.width, 0),
      paint,
    );

    // 画到每个子节点的垂直线
    if (!isFirst && !isLast) {
      // 中间的节点画两边
      canvas.drawLine(
        Offset(index * 80.0, 0),
        Offset(index * 80.0, 15),
        paint,
      );
    } else if (isFirst) {
      // 第一个画到右边的垂直线
      if (total > 1) {
        canvas.drawLine(
          Offset(0, 0),
          Offset(0, 15),
          paint,
        );
      }
    } else if (isLast) {
      // 最后一个画到左边的垂直线
      if (total > 1) {
        canvas.drawLine(
          Offset(size.width, 0),
          Offset(size.width, 15),
          paint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _MemberNode extends StatelessWidget {
  final Member member;
  final int depth;

  const _MemberNode({required this.member, required this.depth});

  @override
  Widget build(BuildContext context) {
    final isMale = member.gender == 'M';
    final primaryColor = isMale ? Colors.blue : Colors.pink;
    final bgColor = isMale ? Colors.blue[50] : Colors.pink[50];

    return GestureDetector(
      onTap: () => _showMemberDetail(context),
      child: Container(
        width: 130,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: primaryColor!, width: 2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 6,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: primaryColor.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                isMale ? Icons.man : Icons.woman,
                size: 28,
                color: primaryColor,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              member.name,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                member.birthDate != null
                    ? '${member.birthDate!.year}年'
                    : '未知',
                style: TextStyle(fontSize: 11, color: primaryColor),
              ),
            ),
            if (depth > 0) ...[
              const SizedBox(height: 4),
              Text(
                '第${depth + 1}代',
                style: TextStyle(fontSize: 10, color: Colors.grey[500]),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showMemberDetail(BuildContext context) {
    final isMale = member.gender == 'M';
    final primaryColor = isMale ? Colors.blue : Colors.pink;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.8,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 拖动指示器
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // 头像和基本信息
                Row(
                  children: [
                    CircleAvatar(
                      radius: 40,
                      backgroundColor: primaryColor?.withOpacity(0.2),
                      child: Icon(
                        isMale ? Icons.man : Icons.woman,
                        size: 40,
                        color: primaryColor,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            member.name,
                            style: const TextStyle(
                              fontSize: 28,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Row(
                            children: [
                              Icon(
                                isMale ? Icons.man : Icons.woman,
                                size: 16,
                                color: Colors.grey[600],
                              ),
                              const SizedBox(width: 4),
                              Text(
                                isMale ? '男' : '女',
                                style: TextStyle(color: Colors.grey[600]),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.edit),
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/member/${member.id}');
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Divider(),
                const SizedBox(height: 16),
                // 详细信息
                _DetailSection(
                  title: '基本信息',
                  icon: Icons.info,
                  children: [
                    if (member.birthDate != null)
                      _DetailRow(
                        icon: Icons.cake,
                        label: '出生日期',
                        value: '${member.birthDate!.year}年${member.birthDate!.month}月${member.birthDate!.day}日',
                      ),
                    if (member.deathDate != null)
                      _DetailRow(
                        icon: Icons.event,
                        label: '逝世日期',
                        value: '${member.deathDate!.year}年${member.deathDate!.month}月${member.deathDate!.day}日',
                      ),
                    if (member.birthPlace != null)
                      _DetailRow(
                        icon: Icons.location_on,
                        label: '籍贯',
                        value: member.birthPlace!,
                      ),
                    if (member.occupation != null)
                      _DetailRow(
                        icon: Icons.work,
                        label: '职业',
                        value: member.occupation!,
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                _DetailSection(
                  title: '家族关系',
                  icon: Icons.family_restroom,
                  children: [
                    if (member.fatherName != null)
                      _DetailRow(
                        icon: Icons.man,
                        label: '父亲',
                        value: member.fatherName!,
                      ),
                    if (member.motherName != null)
                      _DetailRow(
                        icon: Icons.woman,
                        label: '母亲',
                        value: member.motherName!,
                      ),
                    if (member.children?.isNotEmpty == true)
                      _DetailRow(
                        icon: Icons.child_care,
                        label: '子女',
                        value: member.children!.map((c) => c.name).join('、'),
                      ),
                  ],
                ),
                if (member.bio?.isNotEmpty == true) ...[
                  const SizedBox(height: 16),
                  _DetailSection(
                    title: '简介',
                    icon: Icons.description,
                    children: [
                      Text(
                        member.bio!,
                        style: TextStyle(color: Colors.grey[700], height: 1.5),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<Widget> children;

  const _DetailSection({
    required this.title,
    required this.icon,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 20, color: Colors.grey[600]),
            const SizedBox(width: 8),
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ...children,
      ],
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.grey[500]),
          const SizedBox(width: 12),
          SizedBox(
            width: 70,
            child: Text(
              label,
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}
