import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import '../services/ai_service.dart';
import '../models/member.dart';

final ocrProvider = Provider<OCRService>((ref) => OCRService(ref.watch(apiServiceProvider)));

class OCRService {
  final ApiService _api;
  
  OCRService(this._api);
  
  Future<OCRResult> scanImage(File imageFile) async {
    try {
      final bytes = await imageFile.readAsBytes();
      final base64Image = base64Encode(bytes);
      
      final response = await _api._dio.post(
        '/ai/ocr/scan/',
        data: {'image_base64': 'data:image/jpeg;base64,$base64Image'},
        options: Options(
          headers: {'Content-Type': 'application/json'},
          sendTimeout: const Duration(seconds: 60),
          receiveTimeout: const Duration(seconds: 60),
        ),
      );
      
      if (response.data['success'] == true) {
        return OCRResult.fromJson(response.data);
      }
      return OCRResult.error(response.data['error'] ?? '扫描失败');
    } catch (e) {
      return OCRResult.error('扫描失败: $e');
    }
  }
  
  Future<OCRImportResult> importMembers(List<Map<String, dynamic>> members, {
    bool updateExisting = false,
    bool generateBios = false,
  }) async {
    try {
      final response = await _api._dio.post(
        '/ai/ocr/import/',
        data: {
          'members': members,
          'options': {
            'update_existing': updateExisting,
            'generate_bios': generateBios,
          },
        },
      );
      
      if (response.data['success'] == true) {
        return OCRImportResult.fromJson(response.data['summary']);
      }
      return OCRImportResult.error(response.data['error'] ?? '导入失败');
    } catch (e) {
      return OCRImportResult.error('导入失败: $e');
    }
  }
}

class OCRResult {
  final bool success;
  final String? ocrText;
  final List<OCRMemberData> members;
  final Map<String, dynamic>? familyInfo;
  final double confidence;
  final String? error;
  
  OCRResult._({
    required this.success,
    this.ocrText,
    this.members = const [],
    this.familyInfo,
    this.confidence = 0.0,
    this.error,
  });
  
  factory OCRResult.fromJson(Map<String, dynamic> json) {
    return OCRResult._(
      success: json['success'] ?? false,
      ocrText: json['ocr_text'],
      members: (json['members'] as List? ?? [])
          .map((e) => OCRMemberData.fromJson(e))
          .toList(),
      familyInfo: json['family_info'],
      confidence: (json['confidence'] ?? 0).toDouble(),
    );
  }
  
  factory OCRResult.error(String error) {
    return OCRResult._(success: false, error: error);
  }
}

class OCRMemberData {
  final String name;
  final String gender;
  final String? birthDate;
  final String? birthPlace;
  final String? father;
  final String? mother;
  final String? spouse;
  final String? occupation;
  final String? generation;
  final String? notes;
  bool isSelected;
  String? customName;
  String? customGender;
  String? customBirthDate;
  String? customBirthPlace;
  String? customOccupation;
  
  OCRMemberData({
    required this.name,
    required this.gender,
    this.birthDate,
    this.birthPlace,
    this.father,
    this.mother,
    this.spouse,
    this.occupation,
    this.generation,
    this.notes,
    this.isSelected = true,
  });
  
  factory OCRMemberData.fromJson(Map<String, dynamic> json) {
    return OCRMemberData(
      name: json['Name'] ?? json['name'] ?? '',
      gender: _normalizeGender(json['gender'] ?? json['Gender'] ?? 'M'),
      birthDate: json['birth_date'] ?? json['birthDate'] ?? json['Birth_date'],
      birthPlace: json['birth_place'] ?? json['birthPlace'] ?? json['Birth_place'],
      father: json['father'] ?? json['Father'],
      mother: json['mother'] ?? json['Mother'],
      spouse: json['spouse'] ?? json['Spouse'],
      occupation: json['occupation'] ?? json['Occupation'],
      generation: json['generation']?.toString() ?? json['Generation']?.toString(),
      notes: json['notes'] ?? json['Notes'],
    );
  }
  
  static String _normalizeGender(String value) {
    if (value.toUpperCase() == 'M' || value.toLowerCase() == '男') return 'M';
    if (value.toUpperCase() == 'F' || value.toLowerCase() == '女') return 'F';
    return 'M';
  }
  
  Map<String, dynamic> toMemberJson() {
    return {
      'name': customName ?? name,
      'gender': customGender ?? gender,
      if ((customBirthDate ?? birthDate) != null)
        'birth_date': customBirthDate ?? birthDate,
      if ((customBirthPlace ?? birthPlace) != null)
        'birth_place': customBirthPlace ?? birthPlace,
      if ((customOccupation ?? occupation) != null)
        'occupation': customOccupation ?? occupation,
      if (father != null) 'father': father,
      if (mother != null) 'mother': mother,
      if (spouse != null) 'spouse': spouse,
      if (notes != null) 'notes': notes,
    };
  }
}

class OCRImportResult {
  final bool success;
  final int created;
  final int updated;
  final int skipped;
  final int total;
  final List<String>? errors;
  final String? error;
  
  OCRImportResult._({
    required this.success,
    this.created = 0,
    this.updated = 0,
    this.skipped = 0,
    this.total = 0,
    this.errors,
    this.error,
  });
  
  factory OCRImportResult.fromJson(Map<String, dynamic> json) {
    return OCRImportResult._(
      success: true,
      created: json['created'] ?? 0,
      updated: json['updated'] ?? 0,
      skipped: json['skipped'] ?? 0,
      total: json['total'] ?? 0,
      errors: (json['errors'] as List?)?.cast<String>(),
    );
  }
  
  factory OCRImportResult.error(String error) {
    return OCRImportResult._(success: false, error: error);
  }
}

class GenealogyScanScreen extends ConsumerStatefulWidget {
  const GenealogyScanScreen({super.key});

  @override
  ConsumerState<GenealogyScanScreen> createState() => _GenealogyScanScreenState();
}

class _GenealogyScanScreenState extends ConsumerState<GenealogyScanScreen> {
  File? _selectedImage;
  bool _isScanning = false;
  OCRResult? _scanResult;
  final ImagePicker _picker = ImagePicker();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('扫描族谱'),
        actions: [
          if (_scanResult != null)
            TextButton.icon(
              onPressed: _reset,
              icon: const Icon(Icons.refresh),
              label: const Text('重新扫描'),
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_selectedImage == null) {
      return _buildImageSelection();
    }
    
    if (_isScanning) {
      return _buildScanning();
    }
    
    if (_scanResult != null) {
      return _buildResult();
    }
    
    return _buildImagePreview();
  }

  Widget _buildImageSelection() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.document_scanner, size: 100, color: Colors.blue[300]),
            const SizedBox(height: 24),
            const Text(
              '扫描族谱图片',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              '拍摄或选择族谱照片，AI将自动识别家族成员信息',
              style: TextStyle(color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => _pickImage(ImageSource.camera),
              icon: const Icon(Icons.camera_alt),
              label: const Text('拍照'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => _pickImage(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: const Text('从相册选择'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            ),
            const SizedBox(height: 32),
            Card(
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
                          '扫描建议',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text('• 确保图片清晰，光线充足'),
                    const Text('• 尽量让族谱文字保持水平'),
                    const Text('• 优先扫描完整的族谱图片'),
                    const Text('• 手写体识别可能需要手动校正'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildImagePreview() {
    return Column(
      children: [
        Expanded(
          child: Stack(
            children: [
              Center(
                child: InteractiveViewer(
                  child: Image.file(_selectedImage!),
                ),
              ),
              Positioned(
                top: 16,
                right: 16,
                child: FloatingActionButton.small(
                  heroTag: 'change_image',
                  onPressed: _showImageSourceDialog,
                  child: const Icon(Icons.edit),
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _reset,
                  child: const Text('取消'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  onPressed: _startScan,
                  icon: const Icon(Icons.document_scanner),
                  label: const Text('开始扫描'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildScanning() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 24),
          const Text(
            '正在识别族谱...',
            style: TextStyle(fontSize: 18),
          ),
          const SizedBox(height: 8),
          Text(
            'AI 正在分析图片中的家族成员信息',
            style: TextStyle(color: Colors.grey[600]),
          ),
          const SizedBox(height: 24),
          if (_selectedImage != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.file(
                _selectedImage!,
                height: 200,
                fit: BoxFit.cover,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildResult() {
    if (!_scanResult!.success) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
              const SizedBox(height: 16),
              const Text(
                '识别失败',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                _scanResult!.error ?? '未知错误',
                style: TextStyle(color: Colors.grey[600]),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _startScan,
                child: const Text('重新扫描'),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        // 识别统计
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.blue[50],
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatItem('识别成员', '${_scanResult!.members.length}'),
              _buildStatItem('置信度', '${(_scanResult!.confidence * 100).toInt()}%'),
              _buildStatItem(
                '已选',
                '${_scanResult!.members.where((m) => m.isSelected).length}',
              ),
            ],
          ),
        ),
        // 成员列表
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _scanResult!.members.length,
            itemBuilder: (context, index) {
              return _buildMemberCard(_scanResult!.members[index], index);
            },
          ),
        ),
        // 底部操作
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 4,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: _selectAll,
                  child: const Text('全选'),
                ),
              ),
              Expanded(
                child: TextButton(
                  onPressed: _deselectAll,
                  child: const Text('取消全选'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  onPressed: _scanResult!.members.any((m) => m.isSelected)
                      ? _importSelected
                      : null,
                  icon: const Icon(Icons.download),
                  label: const Text('导入选中成员'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey[600], fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildMemberCard(OCRMemberData member, int index) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          setState(() {
            member.isSelected = !member.isSelected;
          });
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Checkbox(
                    value: member.isSelected,
                    onChanged: (value) {
                      setState(() {
                        member.isSelected = value ?? false;
                      });
                    },
                  ),
                  CircleAvatar(
                    backgroundColor: member.gender == 'M' ? Colors.blue[100] : Colors.pink[100],
                    child: Text(
                      member.name.isNotEmpty ? member.name[0] : '?',
                      style: TextStyle(
                        color: member.gender == 'M' ? Colors.blue[700] : Colors.pink[700],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          member.customName ?? member.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          '${member.gender == 'M' ? '男' : '女'}'
                          '${member.birthDate != null ? ' • ${member.birthDate}' : ''}',
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.edit),
                    onPressed: () => _showEditDialog(member),
                  ),
                ],
              ),
              if (member.birthPlace != null || member.occupation != null)
                Padding(
                  padding: const EdgeInsets.only(left: 56, top: 8),
                  child: Wrap(
                    spacing: 8,
                    children: [
                      if (member.birthPlace != null)
                        Chip(
                          avatar: const Icon(Icons.location_on, size: 16),
                          label: Text(member.birthPlace!, style: const TextStyle(fontSize: 12)),
                          visualDensity: VisualDensity.compact,
                        ),
                      if (member.occupation != null)
                        Chip(
                          avatar: const Icon(Icons.work, size: 16),
                          label: Text(member.occupation!, style: const TextStyle(fontSize: 12)),
                          visualDensity: VisualDensity.compact,
                        ),
                      if (member.father != null)
                        Chip(
                          avatar: const Icon(Icons.person, size: 16),
                          label: Text('父: ${member.father}', style: const TextStyle(fontSize: 12)),
                          visualDensity: VisualDensity.compact,
                        ),
                    ],
                  ),
                ),
              if (member.notes != null && member.notes!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(left: 56, top: 8),
                  child: Text(
                    '备注: ${member.notes}',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        imageQuality: 90,
        maxWidth: 2000,
        maxHeight: 2000,
      );
      
      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _scanResult = null;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('选择图片失败: $e')),
        );
      }
    }
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('拍照'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _startScan() async {
    if (_selectedImage == null) return;

    setState(() {
      _isScanning = true;
    });

    final ocrService = ref.read(ocrProvider);
    final result = await ocrService.scanImage(_selectedImage!);

    setState(() {
      _isScanning = false;
      _scanResult = result;
    });
  }

  void _showEditDialog(OCRMemberData member) {
    final nameController = TextEditingController(text: member.name);
    final birthDateController = TextEditingController(text: member.birthDate);
    final birthPlaceController = TextEditingController(text: member.birthPlace);
    final occupationController = TextEditingController(text: member.occupation);
    String selectedGender = member.gender;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('编辑成员信息'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: '姓名 *',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedGender,
                decoration: const InputDecoration(
                  labelText: '性别',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'M', child: Text('男')),
                  DropdownMenuItem(value: 'F', child: Text('女')),
                ],
                onChanged: (value) {
                  selectedGender = value ?? 'M';
                },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: birthDateController,
                decoration: const InputDecoration(
                  labelText: '出生日期',
                  hintText: 'YYYY-MM-DD 或 年份',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: birthPlaceController,
                decoration: const InputDecoration(
                  labelText: '籍贯/出生地',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: occupationController,
                decoration: const InputDecoration(
                  labelText: '职业',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                member.customName = nameController.text;
                member.customGender = selectedGender;
                member.customBirthDate = birthDateController.text;
                member.customBirthPlace = birthPlaceController.text;
                member.customOccupation = occupationController.text;
              });
              Navigator.pop(context);
            },
            child: const Text('保存'),
          ),
        ],
      ),
    );
  }

  void _selectAll() {
    setState(() {
      for (var member in _scanResult!.members) {
        member.isSelected = true;
      }
    });
  }

  void _deselectAll() {
    setState(() {
      for (var member in _scanResult!.members) {
        member.isSelected = false;
      }
    });
  }

  Future<void> _importSelected() async {
    final selectedMembers = _scanResult!.members
        .where((m) => m.isSelected)
        .map((m) => m.toMemberJson())
        .toList();

    if (selectedMembers.isEmpty) return;

    // 显示确认对话框
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认导入'),
        content: Text('将导入 ${selectedMembers.length} 个家族成员'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('确认导入'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    // 显示加载
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('正在导入成员...'),
              ],
            ),
          ),
        ),
      ),
    );

    final ocrService = ref.read(ocrProvider);
    final result = await ocrService.importMembers(
      selectedMembers,
      generateBios: true,
    );

    Navigator.pop(context); // 关闭加载对话框

    if (mounted) {
      if (result.success) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('导入成功'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('创建: ${result.created} 人'),
                Text('更新: ${result.updated} 人'),
                Text('跳过: ${result.skipped} 人'),
                if (result.errors != null && result.errors!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      '错误: ${result.errors!.length} 个',
                      style: TextStyle(color: Colors.red[600]),
                    ),
                  ),
              ],
            ),
            actions: [
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  _reset();
                },
                child: const Text('完成'),
              ),
            ],
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result.error ?? '导入失败')),
        );
      }
    }
  }

  void _reset() {
    setState(() {
      _selectedImage = null;
      _scanResult = null;
      _isScanning = false;
    });
  }
}
