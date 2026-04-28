import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/novel.dart';
import '../providers/novel_provider.dart';
import '../services/novel_service.dart';
import '../theme.dart';
import 'character_screen.dart';
import 'scene_screen.dart';
import 'player_screen.dart';

class NovelListScreen extends StatelessWidget {
  const NovelListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('我的书库'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<NovelProvider>().loadNovels();
            },
          ),
        ],
      ),
      body: Consumer<NovelProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.novels.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.novels.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.library_books_outlined,
                    size: 80,
                    color: Colors.grey[600],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '暂无小说',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '点击底部上传按钮添加小说',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[500],
                    ),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.loadNovels(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.novels.length,
              itemBuilder: (context, index) {
                return NovelCard(novel: provider.novels[index]);
              },
            ),
          );
        },
      ),
    );
  }
}

class NovelCard extends StatelessWidget {
  final Novel novel;

  const NovelCard({super.key, required this.novel});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 60,
                  height: 80,
                  decoration: BoxDecoration(
                    color: AppTheme.primaryColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.menu_book,
                    color: AppTheme.primaryColor,
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        novel.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (novel.author.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          '作者: ${novel.author}',
                          style: TextStyle(
                            color: Colors.grey[400],
                            fontSize: 14,
                          ),
                        ),
                      ],
                      const SizedBox(height: 8),
                      _buildStatusBadge(),
                    ],
                  ),
                ),
                PopupMenuButton<String>(
                  onSelected: (value) => _handleMenuAction(context, value),
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, color: Colors.red),
                          SizedBox(width: 8),
                          Text('删除'),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            if (novel.charactersCount != null || novel.scenesCount != null) ...[
              const SizedBox(height: 12),
              _buildAiInfo(),
            ],
            const SizedBox(height: 16),
            _buildActionButtons(context),
          ],
        ),
      ),
    );
  }

  Widget _buildAiInfo() {
    return Row(
      children: [
        if (novel.charactersCount != null) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.blue[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.blue[200]!),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.people, size: 14, color: Colors.blue[700]),
                const SizedBox(width: 4),
                Text(
                  '${novel.charactersCount} 角色',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.blue[700],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
        ],
        if (novel.scenesCount != null) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.purple[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.purple[200]!),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.movie, size: 14, color: Colors.purple[700]),
                const SizedBox(width: 4),
                Text(
                  '${novel.scenesCount} 场景',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.purple[700],
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildStatusBadge() {
    Color color;
    String text;
    IconData icon;

    switch (novel.status) {
      case 'pending':
        color = Colors.orange;
        text = '待处理';
        icon = Icons.hourglass_empty;
        break;
      case 'analyzing':
        color = Colors.purple;
        text = 'AI分析中';
        icon = Icons.auto_fix_high;
        break;
      case 'processing':
        color = Colors.blue;
        text = '生成中';
        icon = Icons.sync;
        break;
      case 'completed':
        color = AppTheme.accentColor;
        text = '已完成';
        icon = Icons.check_circle;
        break;
      case 'failed':
        color = Colors.red;
        text = '失败';
        icon = Icons.error;
        break;
      default:
        color = Colors.grey;
        text = novel.status;
        icon = Icons.info;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(color: color, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    final novelService = context.read<NovelProvider>().novelService;

    return Column(
      children: [
        if (novel.status == 'pending' || novel.status == 'failed') ...[
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _startAnalysis(context, novelService),
              icon: const Icon(Icons.auto_fix_high),
              label: const Text('AI 分析小说'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        ],
        if (novel.charactersCount != null && novel.charactersCount! > 0) ...[
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _openCharacterScreen(context, novelService),
                  icon: const Icon(Icons.people),
                  label: const Text('角色管理'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _openSceneScreen(context, novelService),
                  icon: const Icon(Icons.movie),
                  label: const Text('场景管理'),
                ),
              ),
            ],
          ),
        ],
        if (novel.audiobook != null) ...[
          const SizedBox(height: 8),
          _buildAudiobookSection(context, novelService),
        ],
      ],
    );
  }

  Widget _buildAudiobookSection(BuildContext context, NovelService novelService) {
    final audiobook = novel.audiobook!;

    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () => _startConversion(context, novelService),
            icon: const Icon(Icons.audiotrack),
            label: Text(audiobook.isCompleted ? '重新生成' : '生成有声书'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryColor,
              foregroundColor: Colors.white,
            ),
          ),
        ),
        if (audiobook.isCompleted) ...[
          const SizedBox(width: 8),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PlayerScreen(
                    novel: novel,
                    audioUrl: context.read<NovelProvider>().getAudioUrl(audiobook.filePath),
                  ),
                ),
              );
            },
            icon: const Icon(Icons.play_arrow),
            label: const Text('播放'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.accentColor,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ],
    );
  }

  void _handleMenuAction(BuildContext context, String action) {
    if (action == 'delete') {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('确认删除'),
          content: Text('确定要删除《${novel.title}》吗？'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () {
                context.read<NovelProvider>().deleteNovel(novel.id);
                Navigator.pop(context);
              },
              child: const Text('删除', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );
    }
  }

  void _startAnalysis(BuildContext context, NovelService novelService) async {
    final success = await novelService.startAnalysis(novel.id);

    if (success && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('AI 分析已启动，请稍候...'),
          duration: Duration(seconds: 2),
        ),
      );

      await Future.delayed(const Duration(seconds: 2));
      context.read<NovelProvider>().loadNovels();
    }
  }

  void _openCharacterScreen(BuildContext context, NovelService novelService) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CharacterScreen(
          novelId: novel.id,
          novelService: novelService,
        ),
      ),
    );
  }

  void _openSceneScreen(BuildContext context, NovelService novelService) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SceneScreen(
          novelId: novel.id,
          novelService: novelService,
        ),
      ),
    );
  }

  void _startConversion(BuildContext context, NovelService novelService) async {
    final audiobook = await novelService.startConversion(novel.id);

    if (audiobook != null && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('开始生成有声书，请稍候...'),
          duration: Duration(seconds: 2),
        ),
      );

      await Future.delayed(const Duration(seconds: 2));
      context.read<NovelProvider>().loadNovels();
    }
  }
}
