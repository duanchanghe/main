import 'package:flutter/material.dart';
import '../models/novel.dart';
import '../services/novel_service.dart';

class CharacterScreen extends StatefulWidget {
  final int novelId;
  final NovelService novelService;

  const CharacterScreen({
    super.key,
    required this.novelId,
    required this.novelService,
  });

  @override
  State<CharacterScreen> createState() => _CharacterScreenState();
}

class _CharacterScreenState extends State<CharacterScreen> {
  List<Character> _characters = [];
  Map<String, String> _availableVoices = {};
  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    final characters = await widget.novelService.getCharacters(widget.novelId);
    final voices = await widget.novelService.getAvailableVoices();

    setState(() {
      _characters = characters;
      _availableVoices = voices;
      _isLoading = false;
    });
  }

  Future<void> _updateCharacter(Character character, String voiceId, String? emotion) async {
    setState(() => _isSaving = true);

    final success = await widget.novelService.updateCharacter(
      widget.novelId,
      character.id,
      voiceId,
      emotion,
    );

    if (success) {
      await _loadData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('角色配置已更新')),
        );
      }
    }

    setState(() => _isSaving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('角色管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _characters.isEmpty
              ? _buildEmptyState()
              : _buildCharacterList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.people_outline,
            size: 80,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            '暂无角色信息',
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
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () async {
              final success = await widget.novelService.startAnalysis(widget.novelId);
              if (success && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('AI 分析已启动')),
                );
              }
            },
            icon: const Icon(Icons.auto_fix_high),
            label: const Text('启动 AI 分析'),
          ),
        ],
      ),
    );
  }

  Widget _buildCharacterList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _characters.length,
      itemBuilder: (context, index) {
        final character = _characters[index];
        return _CharacterCard(
          character: character,
          availableVoices: _availableVoices,
          isSaving: _isSaving,
          onUpdate: (voiceId, emotion) => _updateCharacter(character, voiceId, emotion),
        );
      },
    );
  }
}

class _CharacterCard extends StatelessWidget {
  final Character character;
  final Map<String, String> availableVoices;
  final bool isSaving;
  final Function(String voiceId, String? emotion) onUpdate;

  const _CharacterCard({
    required this.character,
    required this.availableVoices,
    required this.isSaving,
    required this.onUpdate,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
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
                CircleAvatar(
                  radius: 24,
                  backgroundColor: _getRoleColor(character.roleType),
                  child: Text(
                    character.name[0],
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            character.name,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 8),
                          _buildRoleChip(character.roleType),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${character.genderLabel} | ${character.age ?? "未知"} | 重要度: ${character.importanceScore}%',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                if (character.autoDetected)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.blue[100],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      'AI',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue[800],
                      ),
                    ),
                  ),
              ],
            ),
            if (character.personality != null && character.personality!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                '性格: ${character.personality}',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[700],
                ),
              ),
            ],
            if (character.speakingStyle != null && character.speakingStyle!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                '说话风格: ${character.speakingStyle}',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[700],
                ),
              ),
            ],
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
            const Text(
              '音色配置',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            _VoiceDropdown(
              character: character,
              availableVoices: availableVoices,
              isSaving: isSaving,
              onUpdate: onUpdate,
            ),
          ],
        ),
      ),
    );
  }

  Color _getRoleColor(String roleType) {
    switch (roleType) {
      case 'protagonist':
        return Colors.blue;
      case 'antagonist':
        return Colors.red;
      case 'supporting':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Widget _buildRoleChip(String roleType) {
    String label;
    Color color;

    switch (roleType) {
      case 'protagonist':
        label = '主角';
        color = Colors.blue;
        break;
      case 'antagonist':
        label = '反派';
        color = Colors.red;
        break;
      case 'supporting':
        label = '配角';
        color = Colors.green;
        break;
      default:
        label = '次要';
        color = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}

class _VoiceDropdown extends StatefulWidget {
  final Character character;
  final Map<String, String> availableVoices;
  final bool isSaving;
  final Function(String voiceId, String? emotion) onUpdate;

  const _VoiceDropdown({
    required this.character,
    required this.availableVoices,
    required this.isSaving,
    required this.onUpdate,
  });

  @override
  State<_VoiceDropdown> createState() => _VoiceDropdownState();
}

class _VoiceDropdownState extends State<_VoiceDropdown> {
  late String _selectedVoiceId;
  late String _selectedEmotion;

  final List<Map<String, String>> _emotions = [
    {'value': 'neutral', 'label': '中性'},
    {'value': 'happy', 'label': '开心'},
    {'value': 'sad', 'label': '悲伤'},
    {'value': 'angry', 'label': '愤怒'},
    {'value': 'fearful', 'label': '恐惧'},
    {'value': 'surprised', 'label': '惊讶'},
  ];

  @override
  void initState() {
    super.initState();
    _selectedVoiceId = widget.character.voiceId;
    _selectedEmotion = widget.character.defaultEmotion;
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: DropdownButtonFormField<String>(
            value: _selectedVoiceId,
            decoration: InputDecoration(
              labelText: '音色',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            items: widget.availableVoices.entries.map((entry) {
              return DropdownMenuItem(
                value: entry.key,
                child: Text(
                  entry.value,
                  overflow: TextOverflow.ellipsis,
                ),
              );
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _selectedVoiceId = value);
              }
            },
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: DropdownButtonFormField<String>(
            value: _selectedEmotion,
            decoration: InputDecoration(
              labelText: '默认情感',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            items: _emotions.map((e) {
              return DropdownMenuItem(
                value: e['value'],
                child: Text(e['label']!),
              );
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _selectedEmotion = value);
              }
            },
          ),
        ),
        const SizedBox(width: 12),
        ElevatedButton(
          onPressed: widget.isSaving
              ? null
              : () => widget.onUpdate(_selectedVoiceId, _selectedEmotion),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          ),
          child: widget.isSaving
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('保存'),
        ),
      ],
    );
  }
}
