import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/novel.dart';
import '../providers/audio_provider.dart';
import '../theme.dart';

class PlayerScreen extends StatefulWidget {
  final Novel? novel;
  final String? audioUrl;
  final int? jobId;

  const PlayerScreen({
    super.key,
    this.novel,
    this.audioUrl,
    this.jobId,
  });

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  bool _isLiked = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );

    if (widget.novel != null && widget.audioUrl != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.read<AudioProvider>().loadAndPlay(widget.novel!, widget.audioUrl!);
      });
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('播放器'),
        actions: [
          IconButton(
            icon: Icon(
              _isLiked ? Icons.favorite : Icons.favorite_border,
              color: _isLiked ? Colors.red : null,
            ),
            onPressed: () {
              setState(() => _isLiked = !_isLiked);
            },
          ),
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('分享功能开发中')),
              );
            },
          ),
        ],
      ),
      body: Consumer<AudioProvider>(
        builder: (context, audioProvider, child) {
          final novel = audioProvider.currentNovel;

          if (novel == null) {
            return _buildEmptyState();
          }

          return Column(
            children: [
              Expanded(
                child: _buildAlbumCover(audioProvider),
              ),
              _buildPlayerControls(audioProvider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.headphones,
            size: 80,
            color: Colors.grey[600],
          ),
          const SizedBox(height: 16),
          Text(
            '暂无播放内容',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '请先从书库选择小说进行播放',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAlbumCover(AudioProvider audioProvider) {
    final novel = audioProvider.currentNovel!;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedBuilder(
            animation: _animationController,
            builder: (context, child) {
              return Transform.scale(
                scale: audioProvider.isPlaying ? 1.0 : 0.95,
                child: Container(
                  width: 280,
                  height: 280,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.primaryColor.withOpacity(0.3),
                        blurRadius: audioProvider.isPlaying ? 40 : 20,
                        spreadRadius: audioProvider.isPlaying ? 10 : 0,
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(24),
                    child: Container(
                      color: AppTheme.primaryColor.withOpacity(0.2),
                      child: Center(
                        child: Icon(
                          Icons.menu_book,
                          size: 100,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 40),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              children: [
                Text(
                  novel.title,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (novel.author.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    novel.author,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildInfoChip(Icons.auto_stories, '有声书'),
                    const SizedBox(width: 12),
                    _buildInfoChip(
                      Icons.graphic_eq,
                      _getGenreLabel(novel.genre),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.accentColor.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppTheme.accentColor),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              color: AppTheme.accentColor,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayerControls(AudioProvider audioProvider) {
    final duration = audioProvider.duration ?? Duration.zero;
    final position = audioProvider.position;
    final progress = duration.inMilliseconds > 0
        ? position.inMilliseconds / duration.inMilliseconds
        : 0.0;

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 40),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Theme.of(context).colorScheme.surface,
            Theme.of(context).colorScheme.surface.withOpacity(0.8),
          ],
        ),
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(32),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Progress bar
          Column(
            children: [
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  trackHeight: 4,
                  thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                  overlayShape: const RoundSliderOverlayShape(overlayRadius: 16),
                  activeTrackColor: AppTheme.primaryColor,
                  inactiveTrackColor: Colors.grey[300],
                  thumbColor: AppTheme.primaryColor,
                ),
                child: Slider(
                  value: progress.clamp(0.0, 1.0),
                  onChanged: (value) {
                    final newPosition = Duration(
                      milliseconds: (duration.inMilliseconds * value).toInt(),
                    );
                    audioProvider.seek(newPosition);
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatDuration(position),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      _formatDuration(duration),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Play controls
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                icon: Icon(
                  audioProvider.isShuffle ? Icons.shuffle_on : Icons.shuffle,
                  color: audioProvider.isShuffle ? AppTheme.primaryColor : Colors.grey[600],
                ),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('随机播放')),
                  );
                },
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: const Icon(Icons.replay_10),
                iconSize: 36,
                color: Colors.grey[700],
                onPressed: () {
                  audioProvider.seek(position - const Duration(seconds: 10));
                },
              ),
              const SizedBox(width: 16),
              _buildPlayButton(audioProvider),
              const SizedBox(width: 16),
              IconButton(
                icon: const Icon(Icons.forward_30),
                iconSize: 36,
                color: Colors.grey[700],
                onPressed: () {
                  audioProvider.seek(position + const Duration(seconds: 30));
                },
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: Icon(
                  audioProvider.isRepeat ? Icons.repeat_one : Icons.repeat,
                  color: audioProvider.isRepeat ? AppTheme.primaryColor : Colors.grey[600],
                ),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('单曲循环')),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Additional controls
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildSpeedSelector(audioProvider),
              _buildVolumeControl(audioProvider),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPlayButton(AudioProvider audioProvider) {
    return GestureDetector(
      onTap: () {
        if (audioProvider.isPlaying) {
          audioProvider.pause();
        } else {
          audioProvider.play();
        }
      },
      child: Container(
        width: 72,
        height: 72,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppTheme.primaryColor, AppTheme.primaryColorLight],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: AppTheme.primaryColor.withOpacity(0.4),
              blurRadius: 16,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Icon(
          audioProvider.isPlaying ? Icons.pause : Icons.play_arrow,
          iconSize: 40,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildSpeedSelector(AudioProvider audioProvider) {
    return PopupMenuButton<double>(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.speed, size: 18, color: Colors.grey700),
            const SizedBox(width: 4),
            Text(
              '${audioProvider.speed}x',
              style: const TextStyle(
                fontSize: 13,
                color: Colors.grey700,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
      itemBuilder: (context) => [
        const PopupMenuItem(value: 0.5, child: Text('0.5x')),
        const PopupMenuItem(value: 0.75, child: Text('0.75x')),
        const PopupMenuItem(value: 1.0, child: Text('1.0x')),
        const PopupMenuItem(value: 1.25, child: Text('1.25x')),
        const PopupMenuItem(value: 1.5, child: Text('1.5x')),
        const PopupMenuItem(value: 2.0, child: Text('2.0x')),
      ],
      onSelected: (value) {
        audioProvider.setSpeed(value);
      },
    );
  }

  Widget _buildVolumeControl(AudioProvider audioProvider) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          audioProvider.volume > 0 ? Icons.volume_up : Icons.volume_off,
          size: 20,
          color: Colors.grey[700],
        ),
        SizedBox(
          width: 100,
          child: SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 3,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 5),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 12),
            ),
            child: Slider(
              value: audioProvider.volume,
              onChanged: (value) {
                audioProvider.setVolume(value);
              },
            ),
          ),
        ),
      ],
    );
  }

  String _formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    final seconds = duration.inSeconds.remainder(60);

    if (hours > 0) {
      return '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    }
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  String _getGenreLabel(String? genre) {
    final labels = {
      'fantasy': '玄幻',
      'urban': '都市',
      'xianxia': '仙侠',
      'wuxia': '武侠',
      'romance': '言情',
      'scifi': '科幻',
      'mystery': '悬疑',
      'historical': '历史',
    };
    return labels[genre] ?? '其他';
  }
}
