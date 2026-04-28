class Relation {
  final int? id;
  final int fromMemberId;
  final int toMemberId;
  final String relationType;
  final String? fromMemberName;
  final String? toMemberName;

  Relation({
    this.id,
    required this.fromMemberId,
    required this.toMemberId,
    required this.relationType,
    this.fromMemberName,
    this.toMemberName,
  });

  factory Relation.fromJson(Map<String, dynamic> json) {
    return Relation(
      id: json['id'],
      fromMemberId: json['from_member'] ?? 0,
      toMemberId: json['to_member'] ?? 0,
      relationType: json['relation_type'] ?? '',
      fromMemberName: json['from_member_name'],
      toMemberName: json['to_member_name'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'from_member': fromMemberId,
      'to_member': toMemberId,
      'relation_type': relationType,
    };
  }

  static String getRelationLabel(String type) {
    const labels = {
      'father': '父亲',
      'mother': '母亲',
      'spouse': '配偶',
      'child': '子女',
      'sibling': '兄弟姐妹',
    };
    return labels[type] ?? type;
  }
}
