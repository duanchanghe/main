class Member {
  final String? id;
  final String name;
  final String gender;
  final DateTime? birthDate;
  final DateTime? deathDate;
  final String? photo;
  final String? bio;
  final String? fatherId;
  final String? motherId;
  final String? fatherName;
  final String? motherName;
  final String? birthPlace;
  final String? occupation;
  final bool? isAlive;
  final int? age;
  final List<Member>? children;

  Member({
    this.id,
    required this.name,
    required this.gender,
    this.birthDate,
    this.deathDate,
    this.photo,
    this.bio,
    this.fatherId,
    this.motherId,
    this.fatherName,
    this.motherName,
    this.birthPlace,
    this.occupation,
    this.isAlive,
    this.age,
    this.children,
  });

  factory Member.fromJson(Map<String, dynamic> json) {
    return Member(
      id: json['id']?.toString(),
      name: json['name']?.toString() ?? '',
      gender: json['gender']?.toString() ?? 'M',
      birthDate: _parseDate(json['birth_date']),
      deathDate: _parseDate(json['death_date']),
      photo: json['photo']?.toString(),
      bio: json['bio']?.toString(),
      fatherId: json['father']?.toString(),
      motherId: json['mother']?.toString(),
      fatherName: json['father_name']?.toString(),
      motherName: json['mother_name']?.toString(),
      birthPlace: json['birth_place']?.toString(),
      occupation: json['occupation']?.toString(),
      isAlive: json['is_alive'] as bool?,
      age: json['age'] as int?,
      children: json['children'] != null
          ? (json['children'] as List)
              .map((e) => Member.fromJson(e as Map<String, dynamic>))
              .toList()
          : null,
    );
  }

  static DateTime? _parseDate(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    if (value is String && value.isNotEmpty) {
      return DateTime.tryParse(value);
    }
    return null;
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'gender': gender,
      if (birthDate != null)
        'birth_date': birthDate!.toIso8601String().split('T')[0],
      if (deathDate != null)
        'death_date': deathDate!.toIso8601String().split('T')[0],
      if (bio != null && bio!.isNotEmpty) 'bio': bio,
      if (fatherId != null) 'father': fatherId,
      if (motherId != null) 'mother': motherId,
      if (birthPlace != null) 'birth_place': birthPlace,
      if (occupation != null) 'occupation': occupation,
    };
  }

  /// 创建副本并更新指定字段
  Member copyWith({
    String? id,
    String? name,
    String? gender,
    DateTime? birthDate,
    DateTime? deathDate,
    String? photo,
    String? bio,
    String? fatherId,
    String? motherId,
    String? fatherName,
    String? motherName,
    bool? isAlive,
    int? age,
    List<Member>? children,
  }) {
    return Member(
      id: id ?? this.id,
      name: name ?? this.name,
      gender: gender ?? this.gender,
      birthDate: birthDate ?? this.birthDate,
      deathDate: deathDate ?? this.deathDate,
      photo: photo ?? this.photo,
      bio: bio ?? this.bio,
      fatherId: fatherId ?? this.fatherId,
      motherId: motherId ?? this.motherId,
      fatherName: fatherName ?? this.fatherName,
      motherName: motherName ?? this.motherName,
      birthPlace: birthPlace ?? this.birthPlace,
      occupation: occupation ?? this.occupation,
      isAlive: isAlive ?? this.isAlive,
      age: age ?? this.age,
      children: children ?? this.children,
    );
  }

  @override
  String toString() {
    return 'Member(id: $id, name: $name, gender: $gender)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Member && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
