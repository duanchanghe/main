import 'package:flutter_test/flutter_test.dart';
import 'package:genealogy_app/models/models.dart';

void main() {
  group('User Model', () {
    test('fromJson creates User correctly', () {
      final json = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'profile': {'phone': '1234567890'},
      };

      final user = User.fromJson(json);

      expect(user.id, 1);
      expect(user.username, 'testuser');
      expect(user.email, 'test@example.com');
      expect(user.phone, '1234567890');
    });

    test('fromJson handles missing profile', () {
      final json = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
      };

      final user = User.fromJson(json);

      expect(user.phone, isNull);
    });
  });

  group('Member Model', () {
    test('fromJson creates Member correctly', () {
      final json = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'name': '张三',
        'gender': 'M',
        'birth_date': '1990-01-01',
        'death_date': null,
        'bio': '测试简介',
        'is_alive': true,
      };

      final member = Member.fromJson(json);

      expect(member.name, '张三');
      expect(member.gender, 'M');
      expect(member.birthDate?.year, 1990);
      expect(member.isAlive, true);
    });

    test('toJson serializes correctly', () {
      final member = Member(
        id: '123',
        name: '张三',
        gender: 'M',
        birthDate: DateTime(1990, 1, 1),
      );

      final json = member.toJson();

      expect(json['name'], '张三');
      expect(json['gender'], 'M');
      expect(json['birth_date'], '1990-01-01');
    });

    test('handles nested children', () {
      final json = {
        'id': '1',
        'name': '父亲',
        'gender': 'M',
        'children': [
          {
            'id': '2',
            'name': '儿子',
            'gender': 'M',
            'children': [],
          },
        ],
      };

      final member = Member.fromJson(json);

      expect(member.children, isNotNull);
      expect(member.children!.length, 1);
      expect(member.children!.first.name, '儿子');
    });
  });

  group('Relation Model', () {
    test('fromJson creates Relation correctly', () {
      final json = {
        'id': 1,
        'from_member': 1,
        'to_member': 2,
        'relation_type': 'father',
        'from_member_name': '张三',
        'to_member_name': '李四',
      };

      final relation = Relation.fromJson(json);

      expect(relation.relationType, 'father');
      expect(relation.fromMemberName, '张三');
      expect(relation.toMemberName, '李四');
    });

    test('getRelationLabel returns correct Chinese labels', () {
      expect(Relation.getRelationLabel('father'), '父亲');
      expect(Relation.getRelationLabel('mother'), '母亲');
      expect(Relation.getRelationLabel('spouse'), '配偶');
      expect(Relation.getRelationLabel('child'), '子女');
    });
  });

  group('AuthTokens', () {
    test('fromJson creates AuthTokens correctly', () {
      final json = {
        'access': 'access_token_123',
        'refresh': 'refresh_token_456',
      };

      final tokens = AuthTokens.fromJson(json);

      expect(tokens.access, 'access_token_123');
      expect(tokens.refresh, 'refresh_token_456');
    });
  });

  group('AuthResponse', () {
    test('fromJson creates AuthResponse correctly', () {
      final json = {
        'user': {
          'id': 1,
          'username': 'testuser',
          'email': 'test@example.com',
        },
        'tokens': {
          'access': 'access_token',
          'refresh': 'refresh_token',
        },
      };

      final response = AuthResponse.fromJson(json);

      expect(response.user.username, 'testuser');
      expect(response.tokens.access, 'access_token');
    });
  });
}
