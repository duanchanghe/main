import 'package:flutter/material.dart';
import '../models/novel.dart';
import '../services/novel_service.dart';

class SceneScreen extends StatefulWidget {
  final int novelId;
  final NovelService novelService;

  const SceneScreen({
    super.key,
    required this.novelId,
    required this.novelService,
  });

  @override
  State<SceneScreen> createState() => _SceneScreenState();
}

class _SceneScreenState extends State<SceneScreen> {
  List<Scene> _scenes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadScenes();
  }

  Future<void> _loadScenes() async {
    setState(() => _isLoading = true);
    final scenes = await widget.novelService.getScenes(widget.novelId);
    setState(() {
      _scenes = scenes;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('场景管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadScenes,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _scenes.isEmpty
              ? _buildEmptyState()
              : _buildSceneList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.movie_outlined,
            size: 80,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            '暂无场景信息',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '请先使用 AI 分析小说',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSceneList() {
    final groupedScenes = <int, List<Scene>>{};
    for (final scene in _scenes) {
      groupedScenes.putIfAbsent(scene.chapterNumber, () => []).add(scene);
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: groupedScenes.length,
      itemBuilder: (context, index) {
        final chapterNum = groupedScenes.keys.elementAt(index);
        final scenes = groupedScenes[chapterNum]!;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.blue[700],
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      '第 $chapterNum 章',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${scenes.length} 个场景',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            ...scenes.map((scene) => _SceneCard(scene: scene)),
          ],
        );
      },
    );
  }
}

class _SceneCard extends StatelessWidget {
  final Scene scene;

  const _SceneCard({required this.scene});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getMoodIcon(scene.mood),
                  color: _getMoodColor(scene.mood),
                  size: 28,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        scene.location.isNotEmpty ? scene.location : '未知地点',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          if (scene.timeOfDay.isNotEmpty) ...[
                            Icon(Icons.schedule, size: 14, color: Colors.grey[500]),
                            const SizedBox(width: 4),
                            Text(
                              scene.timeOfDay,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                            const SizedBox(width: 12),
                          ],
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: _getMoodColor(scene.mood).withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              scene.moodLabel,
                              style: TextStyle(
                                fontSize: 12,
                                color: _getMoodColor(scene.mood),
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Column(
                  children: [
                    Icon(Icons.chat_bubble_outline, size: 16, color: Colors.grey[400]),
                    Text(
                      '${scene.dialoguesCount}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            if (scene.suggestedBgm.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange[200]!),
                ),
                child: Row(
                  children: [
                    Icon(Icons.music_note, size: 20, color: Colors.orange[700]),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '推荐BGM',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.orange[700],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            scene.suggestedBgm,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.orange[900],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getMoodIcon(String mood) {
    switch (mood) {
      case 'happy':
        return Icons.sentiment_very_satisfied;
      case 'tense':
        return Icons.warning_amber;
      case 'sad':
        return Icons.sentiment_dissatisfied;
      case 'romantic':
        return Icons.favorite;
      case 'mysterious':
        return Icons.help_outline;
      case 'excited':
        return Icons.celebration;
      case 'horror':
        return Icons.psychology_alt;
      default:
        return Icons.emoji_neutral;
    }
  }

  Color _getMoodColor(String mood) {
    switch (mood) {
      case 'happy':
        return Colors.amber;
      case 'tense':
        return Colors.orange;
      case 'sad':
        return Colors.blue;
      case 'romantic':
        return Colors.pink;
      case 'mysterious':
        return Colors.purple;
      case 'excited':
        return Colors.red;
      case 'horror':
        return Colors.brown;
      default:
        return Colors.grey;
    }
  }
}
