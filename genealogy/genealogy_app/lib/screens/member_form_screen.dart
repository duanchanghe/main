import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../providers/providers.dart';
import '../models/models.dart';

class MemberFormScreen extends ConsumerStatefulWidget {
  final int? memberId;

  const MemberFormScreen({super.key, this.memberId});

  @override
  ConsumerState<MemberFormScreen> createState() => _MemberFormScreenState();
}

class _MemberFormScreenState extends ConsumerState<MemberFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _bioController = TextEditingController();

  String _gender = 'M';
  DateTime? _birthDate;
  DateTime? _deathDate;
  int? _fatherId;
  int? _motherId;
  bool _isLoading = false;

  bool get isEditing => widget.memberId != null;

  @override
  void initState() {
    super.initState();
    if (isEditing) {
      _loadMember();
    }
  }

  Future<void> _loadMember() async {
    setState(() => _isLoading = true);
    try {
      final member = await ref.read(apiServiceProvider).getMember(widget.memberId!);
      _nameController.text = member.name;
      _bioController.text = member.bio ?? '';
      setState(() {
        _gender = member.gender;
        _birthDate = member.birthDate;
        _deathDate = member.deathDate;
        _fatherId = member.fatherId;
        _motherId = member.motherId;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('加载成员失败')),
        );
        context.pop();
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(bool isBirth) async {
    final date = await showDatePicker(
      context: context,
      initialDate: isBirth
          ? (_birthDate ?? DateTime.now())
          : (_deathDate ?? DateTime.now()),
      firstDate: DateTime(1800),
      lastDate: DateTime.now(),
    );
    if (date != null) {
      setState(() {
        if (isBirth) {
          _birthDate = date;
        } else {
          _deathDate = date;
        }
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    final member = Member(
      id: widget.memberId,
      name: _nameController.text.trim(),
      gender: _gender,
      birthDate: _birthDate,
      deathDate: _deathDate,
      bio: _bioController.text.trim(),
      fatherId: _fatherId,
      motherId: _motherId,
    );

    bool success;
    if (isEditing) {
      success = await ref.read(familyProvider.notifier).updateMember(widget.memberId!, member);
    } else {
      success = await ref.read(familyProvider.notifier).createMember(member);
    }

    if (success && mounted) {
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final familyState = ref.watch(familyProvider);
    final availableParents = familyState.members.where((m) => m.id != widget.memberId).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing ? '编辑成员' : '添加成员'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(
                        labelText: '姓名 *',
                        prefixIcon: Icon(Icons.person),
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v?.isEmpty == true ? '请输入姓名' : null,
                    ),
                    const SizedBox(height: 16),
                    const Text('性别 *', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    const SizedBox(height: 8),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'M', label: Text('男'), icon: Icon(Icons.man)),
                        ButtonSegment(value: 'F', label: Text('女'), icon: Icon(Icons.woman)),
                      ],
                      selected: {_gender},
                      onSelectionChanged: (s) => setState(() => _gender = s.first),
                    ),
                    const SizedBox(height: 16),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.cake),
                      title: Text(_birthDate == null
                          ? '选择出生日期'
                          : DateFormat('yyyy-MM-dd').format(_birthDate!)),
                      trailing: IconButton(
                        icon: const Icon(Icons.edit_calendar),
                        onPressed: () => _selectDate(true),
                      ),
                      onTap: () => _selectDate(true),
                    ),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.event),
                      title: Text(_deathDate == null
                          ? '选择逝世日期 (可选)'
                          : DateFormat('yyyy-MM-dd').format(_deathDate!)),
                      trailing: _deathDate != null
                          ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () => setState(() => _deathDate = null),
                            )
                          : IconButton(
                              icon: const Icon(Icons.edit_calendar),
                              onPressed: () => _selectDate(false),
                            ),
                      onTap: () => _selectDate(false),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<int>(
                      value: _fatherId,
                      decoration: const InputDecoration(
                        labelText: '父亲',
                        prefixIcon: Icon(Icons.man),
                        border: OutlineInputBorder(),
                      ),
                      items: [
                        const DropdownMenuItem(value: null, child: Text('无')),
                        ...availableParents
                            .where((m) => m.gender == 'M')
                            .map((m) => DropdownMenuItem(value: m.id, child: Text(m.name))),
                      ],
                      onChanged: (v) => setState(() => _fatherId = v),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<int>(
                      value: _motherId,
                      decoration: const InputDecoration(
                        labelText: '母亲',
                        prefixIcon: Icon(Icons.woman),
                        border: OutlineInputBorder(),
                      ),
                      items: [
                        const DropdownMenuItem(value: null, child: Text('无')),
                        ...availableParents
                            .where((m) => m.gender == 'F')
                            .map((m) => DropdownMenuItem(value: m.id, child: Text(m.name))),
                      ],
                      onChanged: (v) => setState(() => _motherId = v),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _bioController,
                      decoration: const InputDecoration(
                        labelText: '个人简介',
                        prefixIcon: Icon(Icons.description),
                        border: OutlineInputBorder(),
                      ),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _save,
                      child: Text(isEditing ? '保存修改' : '添加'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
