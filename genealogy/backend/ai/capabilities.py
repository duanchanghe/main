"""
Genealogy AI Capabilities
"""
import json
import logging
from typing import Optional, List, Dict, Any
from .services import get_default_ai_service, AIResponse

logger = logging.getLogger(__name__)


class MemberBioGenerator:
    """成员简介生成器"""
    
    SYSTEM_PROMPT = """你是一位专业的家谱编纂专家，擅长根据家族成员的基本信息生成生动、准确的人物简介。
请用温暖、尊重的笔触撰写简介，突出人物的特点和贡献。
简介应该客观真实，避免夸大或虚构。
如果信息不足以生成完整简介，请基于现有信息生成合理的简介。
回复应该简洁明了，一般不超过200字。"""
    
    @classmethod
    def generate_prompt(cls, member_data: Dict[str, Any]) -> str:
        """生成提示词"""
        parts = []
        
        if member_data.get('name'):
            parts.append(f"姓名: {member_data['name']}")
        if member_data.get('gender'):
            gender = "男" if member_data['gender'] == 'M' else "女"
            parts.append(f"性别: {gender}")
        if member_data.get('birth_date'):
            parts.append(f"出生日期: {member_data['birth_date']}")
        if member_data.get('birth_place'):
            parts.append(f"出生地: {member_data['birth_place']}")
        if member_data.get('occupation'):
            parts.append(f"职业: {member_data['occupation']}")
        if member_data.get('education'):
            parts.append(f"学历: {member_data['education']}")
        if member_data.get('father_name'):
            parts.append(f"父亲: {member_data['father_name']}")
        if member_data.get('mother_name'):
            parts.append(f"母亲: {member_data['mother_name']}")
        
        info = "\n".join(parts)
        
        return f"""请根据以下家族成员信息生成一段简介：

{info}

请生成一段简洁的人物简介："""

    @classmethod
    def generate(cls, member_data: Dict[str, Any]) -> AIResponse:
        """生成成员简介"""
        ai_service = get_default_ai_service()
        prompt = cls.generate_prompt(member_data)
        return ai_service.generate_sync(prompt, cls.SYSTEM_PROMPT)


class RelationRecommender:
    """关系推荐器"""
    
    SYSTEM_PROMPT = """你是一位家族关系研究专家。根据家族成员的信息，分析并推荐可能存在但尚未记录的关系。
请考虑以下常见关系类型：
- 配偶关系
- 父子/母女关系
- 兄弟姐妹关系
- 祖孙关系
- 叔侄/姑舅关系
- 表兄弟姐妹关系

请基于成员的年龄、职业、地域等信息进行合理推断。
只推荐合理的关系，对于不确定的关系要谨慎。
返回JSON格式的推荐列表。"""

    @classmethod
    def generate_prompt(cls, members: List[Dict[str, Any]]) -> str:
        """生成提示词"""
        members_info = []
        for i, m in enumerate(members[:20]):  # 限制分析数量
            info = {
                "id": str(m.get('id', i)),
                "name": m.get('name', ''),
                "gender": m.get('gender', ''),
                "birth_date": str(m.get('birth_date', '')),
                "occupation": m.get('occupation', ''),
                "birth_place": m.get('birth_place', ''),
            }
            members_info.append(info)
        
        return f"""请分析以下家族成员，推荐可能存在但尚未记录的关系：

{json.dumps(members_info, ensure_ascii=False, indent=2)}

请返回JSON格式的推荐关系列表，格式如下：
{{
  "recommendations": [
    {{
      "member1_id": "成员1ID",
      "member2_id": "成员2ID",
      "relation_type": "关系类型",
      "confidence": 0.85,
      "reason": "推荐理由"
    }}
  ]
}}

只推荐置信度超过70%的关系。"""

    @classmethod
    def recommend(cls, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """推荐关系"""
        ai_service = get_default_ai_service()
        prompt = cls.generate_prompt(members)
        
        response = ai_service.generate_sync(prompt, cls.SYSTEM_PROMPT)
        
        if not response.success:
            return {"recommendations": [], "error": response.error}
        
        try:
            # 尝试解析 JSON
            data = json.loads(response.content)
            return data
        except json.JSONDecodeError:
            # 如果不是JSON，返回文本建议
            return {
                "recommendations": [],
                "raw_suggestion": response.content,
                "error": None
            }


class FamilyAnalyzer:
    """族谱分析器"""
    
    SYSTEM_PROMPT = """你是一位专业的家谱研究者。分析家族成员数据，提供有价值的洞察和建议。
请分析：
1. 家族规模和发展趋势
2. 世代分布情况
3. 地理分布特点
4. 职业分布
5. 教育水平
6. 家族传统和文化特点
7. 可能的历史事件影响

请用JSON格式返回分析结果，便于程序处理。"""

    @classmethod
    def generate_prompt(cls, members: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """生成提示词"""
        members_info = []
        for m in members[:50]:  # 限制分析数量
            info = {
                "name": m.get('name', ''),
                "gender": "男" if m.get('gender') == 'M' else "女",
                "birth_date": str(m.get('birth_date', '')),
                "birth_place": m.get('birth_place', ''),
                "occupation": m.get('occupation', ''),
                "education": m.get('education', ''),
            }
            members_info.append(info)
        
        stats_info = f"""
基本统计:
- 总成员数: {stats.get('total_members', 0)}
- 男性: {stats.get('male_count', 0)}
- 女性: {stats.get('female_count', 0)}
- 平均年龄: {stats.get('average_age', 0)}
- 最高寿: {stats.get('oldest_age', 0)}
- 最小辈分代际: {stats.get('generations', 0)}
"""
        
        return f"""请分析以下家谱数据，提供有价值的洞察：

{stats_info}

家族成员信息:
{json.dumps(members_info, ensure_ascii=False, indent=2)}

请返回JSON格式的分析结果：
{{
  "summary": "家族概述（1-2句话）",
  "size_analysis": "规模分析",
  "geographic_distribution": "地理分布分析",
  "profession_distribution": "职业分布分析",
  "education_analysis": "教育水平分析",
  "generations_insights": "世代分析",
  "traditions": "家族传统和特点",
  "suggestions": ["建议1", "建议2", "建议3"],
  "interesting_facts": ["有趣的事实1", "有趣的事实2"]
}}"""

    @classmethod
    def analyze(cls, members: List[Dict[str, Any]], stats: Dict[str, Any]) -> Dict[str, Any]:
        """分析族谱"""
        ai_service = get_default_ai_service()
        prompt = cls.generate_prompt(members, stats)
        
        response = ai_service.generate_sync(prompt, cls.SYSTEM_PROMPT)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            data = json.loads(response.content)
            return data
        except json.JSONDecodeError:
            return {
                "summary": response.content,
                "error": None
            }


class NameMeaningAnalyzer:
    """姓名寓意分析器"""
    
    SYSTEM_PROMPT = """你是一位精通中国传统文化的学者，专长于姓名学。请分析姓名的寓意和来源。"""

    @classmethod
    def generate_prompt(cls, name: str, gender: str = None) -> str:
        """生成提示词"""
        gender_hint = f"性别: {'男' if gender == 'M' else '女'}" if gender else ""
        
        return f"""请分析以下姓名的寓意和来源：

姓名: {name}
{gender_hint}

请用JSON格式返回分析结果：
{{
  "name": "{name}",
  "surname_meaning": "姓氏含义",
  "given_name_meaning": "名字含义",
  "combined_meaning": "整体寓意",
  "cultural_background": "文化背景",
  "lucky_elements": {{
    "element": "五行属性",
    "zodiac": "宜用生肖",
    "stroke_count": "吉凶笔画"
  }},
  "origin_story": "起名由来或典故"
}}"""

    @classmethod
    def analyze(cls, name: str, gender: str = None) -> AIResponse:
        """分析姓名"""
        ai_service = get_default_ai_service()
        prompt = cls.generate_prompt(name, gender)
        return ai_service.generate_sync(prompt, cls.SYSTEM_PROMPT)


class SearchAssistant:
    """搜索助手 - 智能问答"""
    
    SYSTEM_PROMPT = """你是一位家谱研究助手。请根据用户的问题，结合家族信息给出有用的回答。
你只知道用户提供的信息，如果信息不足，请坦诚告知。
请用友好的语气回答，可以适当提问以获取更多信息。"""

    @classmethod
    def answer_prompt(cls, question: str, family_context: Dict[str, Any]) -> str:
        """生成问答提示词"""
        context_str = json.dumps(family_context, ensure_ascii=False, indent=2)
        
        return f"""用户问题: {question}

家族信息:
{context_str}

请根据以上家族信息回答用户的问题。如果信息不足，请说明并提供一般性建议。"""

    @classmethod
    def answer(cls, question: str, family_context: Dict[str, Any]) -> AIResponse:
        """回答问题"""
        ai_service = get_default_ai_service()
        prompt = cls.answer_prompt(question, family_context)
        return ai_service.generate_sync(prompt, cls.SYSTEM_PROMPT)
