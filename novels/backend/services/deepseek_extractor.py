"""
DeepSeek 小说分析服务
使用 DeepSeek API 分析小说文本，提取完整信息用于有声书制作
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class DeepSeekNovelAnalyzer:
    """DeepSeek 小说分析器"""

    VOICE_MAPPING = {
        # 男声
        'male-qn-qingse': {'gender': 'male', 'desc': '磁性低沉男声，适合男主角'},
        'male-yuanfang': {'gender': 'male', 'desc': '成熟稳重男声，适合中年角色'},
        'male-bada': {'gender': 'male', 'desc': '粗犷大叔声，适合硬汉角色'},
        'Chinese_Male_Neutral': {'gender': 'male', 'desc': '标准播音男声，适合旁白'},
        'male-tiancheng': {'gender': 'male', 'desc': '天成男声，清澈有力'},

        # 女声
        'female-tianmei': {'gender': 'female', 'desc': '甜美温柔女声，适合女主角'},
        'female-shaoyu': {'gender': 'female', 'desc': '淑女声，温婉柔和'},
        'Chinese_Female_Neutral': {'gender': 'female', 'desc': '标准播音女声'},
        'female-yunyang': {'gender': 'female', 'desc': '云扬女声，活泼可爱'},
    }

    EMOTION_MAPPING = {
        'happy': ['笑', '开心', '高兴', '喜悦', '愉快', '欢乐', '哈哈', '欣喜', '欢快', '乐', '欣喜', '开心'],
        'sad': ['哭', '悲伤', '难过', '伤心', '痛苦', '哀伤', '泪', '叹息', '沮丧', '低沉', '泣', '呜咽'],
        'angry': ['怒', '气愤', '愤怒', '恼怒', '吼', '咆哮', '呵斥', '斥责', '火', '暴怒', '暴跳', '大怒'],
        'fearful': ['怕', '恐惧', '害怕', '惊恐', '哆嗦', '发抖', '心虚', '胆怯', '畏惧', '发颤'],
        'surprised': ['惊', '惊讶', '诧异', '震惊', '愕然', '意外', '咦', '啊', '什么', '怎么', '啊？', '咦？', '竟'],
        'tense': ['紧', '紧张', '焦急', '焦虑', '不安', '悬', '屏息', '屏住', '心跳'],
        'excited': ['激', '激动', '兴奋', '振奋', '高昂', '热血', '沸腾', '振奋', '激昂', '慷慨'],
        'romantic': ['爱', '柔情', '温柔', '甜蜜', '亲', '吻', '心跳', '脸红', '羞涩', '倾心', '爱慕'],
        'mysterious': ['神', '神秘', '诡异', '诡异', '幽', '暗', '玄', '诡', '秘', '阴', '魔'],
    }

    SYSTEM_PROMPT = """你是一个专业的有声书制作AI助手。请对小说文本进行完整、深度分析。

【核心要求 - 必须严格遵守】
1. 提取文本中的每一句对话，不要遗漏
2. 为每个对话自动配置合适的音色和情感
3. 分析所有场景的音效和背景音乐需求
4. 输出必须是完整有效的JSON格式

【音色配置规则 - 自动匹配】
根据角色特征自动选择最适合的音色：

男性角色音色：
- 年轻男主角/英雄：male-qn-qingse（磁性男声）
- 中年男性/成熟稳重角色：male-yuanfang（成熟男声）
- 粗犷角色/硬汉/反派：male-bada（粗犷大叔声）
- 旁白/叙述：Chinese_Male_Neutral（标准播音）
- 普通男性/配角：Chinese_Male_Neutral

女性角色音色：
- 女主角/温柔女性：female-tianmei（甜美女声）
- 淑女/优雅女性：female-shaoyu（淑女声）
- 普通女性/配角：Chinese_Female_Neutral
- 年轻活泼女性：female-yunyang（活泼女声）

【情感配置规则 - 自动识别】
根据对话内容和上下文自动判断情感：
- 开心/happy：包含笑、高兴、愉快等情绪词
- 悲伤/sad：包含哭、伤心、叹息等情绪词
- 愤怒/angry：包含怒、吼、咆哮等情绪词
- 恐惧/fearful：包含怕、紧张、发抖等情绪词
- 惊讶/surprised：包含惊讶、意外、疑问等
- 紧张/tense：包含焦虑、屏息、心跳等
- 激动/excited：包含激动、振奋、沸腾等
- 浪漫/romantic：包含爱、柔情、脸红等
- 平静/calm：中性陈述，无明显情绪

【返回JSON格式 - 必须完整】

```json
{
  "novel_info": {
    "title": "小说标题（从文本中提取或生成描述性标题）",
    "genre": "类型（玄幻/都市/仙侠/武侠/悬疑/言情/科幻/历史/其他）",
    "setting": "背景设定（古代/近代/现代/未来/异世界/架空等）",
    "language_level": "语言难度（简单/中等/复杂）",
    "target_audience": "目标受众"
  },

  "characters": [
    {
      "name": "角色全名",
      "role_type": "protagonist（主角）/supporting（配角）/antagonist（反派）/minor（次要）",
      "gender": "male/female/unknown",
      "age": "young（青年）/middle-aged（中年）/elderly（老年）/unknown",
      "personality": "性格特征详细描述",
      "speaking_style": "说话风格（文绉绉/口语化/粗犷/温柔/果断等）",
      "temperament": "气质类型（儒雅/狂放/阴郁/阳光/沉稳/张扬等）",
      "voice_id": "根据角色特征自动选择的音色ID",
      "voice_desc": "音色选择理由",
      "catchphrase": "口头禅（如有）",
      "special_mannerisms": "说话习惯（如结巴、停顿、口头语）",
      "emotion_range": ["neutral", "happy", "sad", "angry", "fearful"],
      "importance_score": 0-100的重要程度评分
    }
  ],

  "narrative_voice": {
    "type": "叙述人称（第一人称/第三人称）",
    "tone": "叙述语调（客观/主观/诗意/紧张）",
    "pacing": "叙事节奏（快/中/慢）",
    "voice_id": "Chinese_Male_Neutral（旁白推荐）",
    "narration_style": "叙述风格描述"
  },

  "chapters": [
    {
      "chapter_number": 1,
      "title": "章节标题（无则留空）",
      "summary": "50字以内章节摘要",
      "word_count": 章节字数,
      "scene_changes": [
        {
          "scene_id": 1,
          "location": "具体场景地点",
          "time_of_day": "清晨/上午/中午/下午/傍晚/夜晚/深夜",
          "season": "春夏秋冬/无标注",
          "weather": "晴/雨/雪/雾/雷电/无标注",
          "atmosphere": "氛围描述（诡异/温馨/紧张等）",
          "mood": "欢快happy/紧张tense/悲伤sad/悬疑mysterious/温馨calm/浪漫romantic/恐怖horror/平静calm/激动excited",

          "bgm": {
            "style": "音乐风格（史诗/古风/悬疑/浪漫/战斗/平静/悲伤/神秘等）",
            "instruments": "主要乐器（琵琶/古筝/钢琴/管弦乐/电子/二胡等）",
            "tempo": "快/中/慢",
            "entry_time": "BGM进入时机描述",
            "fade_in": 0-5,
            "fade_out": 0-5,
            "volume": 0.0-1.0,
            "loop": true,
            "description": "音乐描述"
          },

          "ambient_sound": {
            "description": "环境音描述（雨声/鸟鸣/风声/人群等）",
            "volume": 0.0-0.5,
            "continuous": true
          },

          "dialogues": [
            {
              "id": 1,
              "character": "角色名（必须与characters中的name一致）",
              "text": "完整对话原文（不要省略，不要改写）",
              "emotion": "基于内容自动识别的情感（neutral/happy/sad/angry/fearful/surprised/tense/excited/romantic/mysterious）",
              "emotion_evidence": "判断依据关键词",
              "volume": "normal/loud/whisper/calling",
              "speed": "slow/normal/fast",
              "pitch": "high/normal/low",

              "sfx": {
                "type": ["脚步声", "笑声", "叹息声"],
                "timing": "before/during/after",
                "position_ms": 0,
                "duration": 1000,
                "volume": 0.3,
                "description": "音效效果描述"
              },

              "special_effects": {
                "type": "回声/电话/远距离等（如无则为空）",
                "params": {}
              }
            }
          ],

          "sfx_events": [
            {
              "type": "音效类型（脚步声/雨声/敲门声等）",
              "trigger": "触发条件",
              "position_ms": 0,
              "duration": 1000,
              "volume": 0.5,
              "fade_in": 0,
              "fade_out": 0,
              "repeat": 1,
              "description": "音效描述"
            }
          ],

          "narration": "需要朗读的叙述段落原文（保持原样，不要改写）",

          "transition": {
            "type": "淡入淡出/硬切/音效转场",
            "duration_ms": 1000,
            "description": "转场描述"
          }
        }
      ],

      "overall_mood": "本章整体情绪基调",
      "emotional_peak": "本章情感高潮描述（如有）"
    }
  ],

  "emotional_arc": {
    "overall_mood_curve": ["章节1情绪", "章节2情绪"],
    "climax_chapters": [3, 7, 12],
    "pacing_analysis": "节奏分析描述"
  },

  "sound_design": {
    "key_sfx_moments": ["关键音效时刻列表"],
    "emotional_peaks": ["情感高潮点列表"],
    "ambient_layering": "环境音层次设计描述",
    "transition_sounds": ["转场音效建议"]
  },

  "production_notes": "制作备注"
}
```

【音效类型参考库】
- 脚步声：木地板、石板、草地、楼梯、泥地
- 敲门声：轻敲、重敲、急促敲
- 开关门：木门、铁门、吱呀声
- 自然音：雨、雷、风、鸟、虫、流水、海浪
- 战斗音：剑击、撞击、爆炸、马蹄
- 情绪音：笑声、叹息、心跳、抽泣、喘息
- 通讯音：电话铃、门铃、手机
- 室内音：茶杯、翻书、时钟、纸张

【BGM风格关键词】
- 古风：琵琶、古筝、二胡、箫、竹笛、编钟
- 史诗：管弦乐、合唱、鼓点、铜管
- 悬疑：低音提琴、合成器、钟琴、阴声
- 浪漫：小提琴、钢琴、弦乐、竖琴
- 战斗：鼓点、铜管、快速节奏、金属
- 平静：钢琴、自然音、缓慢、纯音
- 悲伤：钢琴、弦乐、慢节奏、低沉

【重要提醒】
1. 对话原文必须100%保持原样，不得改写或省略
2. 每个场景的所有对话都要提取，一句都不能漏
3. 音色选择必须符合角色特征和性别
4. 情感识别必须有依据（关键词或语气）
5. 确保JSON格式完整，所有括号闭合"""

    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def analyze_novel(
        self,
        content: str,
        max_chars: int = 15000,
        chunk_overlap: int = 1000
    ) -> Dict[str, Any]:
        """
        分析小说文本（支持长文本分段分析）

        Args:
            content: 小说文本内容
            max_chars: 每段最大字符数
            chunk_overlap: 段落重叠字符数

        Returns:
            完整的分析结果字典
        """
        if len(content) <= max_chars:
            return self._analyze_single_chunk(content)

        chunks = self._split_content(content, max_chars, chunk_overlap)
        results = []

        for i, chunk in enumerate(chunks):
            print(f"分析第 {i+1}/{len(chunks)} 段...")
            result = self._analyze_single_chunk(chunk, chunk_index=i)
            results.append(result)

        return self._merge_results(results)

    def _split_content(self, content: str, max_chars: int, overlap: int) -> List[str]:
        """将长文本分割成多个片段"""
        chunks = []
        start = 0

        while start < len(content):
            end = start + max_chars

            if end < len(content):
                search_start = end - overlap
                punct_marks = ['。', '！', '？', '；', '，', '"', '"', '》', '】']
                for mark in punct_marks:
                    pos = content.rfind(mark, search_start, end)
                    if pos != -1:
                        end = pos + 1
                        break

            chunks.append(content[start:end])
            start = end - overlap if end < len(content) else len(content)

        return chunks

    def _analyze_single_chunk(self, content: str, chunk_index: int = 0) -> Dict[str, Any]:
        """分析单个文本片段"""
        try:
            prompt = f"请分析以下小说文本（第{chunk_index + 1}段）：\n\n{content}"

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=16000,
                timeout=120
            )

            result_text = response.choices[0].message.content
            result = self._parse_json_response(result_text)
            result['_chunk_index'] = chunk_index
            return result

        except TimeoutError:
            print(f"DeepSeek 分析超时 (chunk {chunk_index})")
            return self._parse_fallback(content)
        except Exception as e:
            print(f"DeepSeek 分析失败 (chunk {chunk_index}): {e}")
            return self._parse_fallback(content)

    def _merge_results(self, results: List[Dict]) -> Dict[str, Any]:
        """合并多个片段的分析结果"""
        if not results:
            return self._parse_fallback("")

        merged = {
            "novel_info": results[0].get("novel_info", {}),
            "characters": [],
            "narrative_voice": results[0].get("narrative_voice", {}),
            "chapters": [],
            "emotional_arc": {"overall_mood_curve": [], "climax_chapters": [], "pacing_analysis": ""},
            "sound_design": {"key_sfx_moments": [], "emotional_peaks": [], "ambient_layering": "", "transition_sounds": []},
            "production_notes": f"分{len(results)}段分析"
        }

        char_map = {}
        for result in results:
            for char in result.get("characters", []):
                name = char.get("name")
                if name and name not in char_map:
                    char_map[name] = char
                    merged["characters"].append(char)

        chapter_offset = 0
        for i, result in enumerate(results):
            for chapter in result.get("chapters", []):
                chapter_num = chapter.get("chapter_number", 1) + chapter_offset
                chapter["chapter_number"] = chapter_num

                if i > 0:
                    for scene in chapter.get("scene_changes", []):
                        scene["scene_id"] = scene.get("scene_id", 1) + i * 10

                merged["chapters"].append(chapter)
            chapter_offset = len(merged["chapters"])

        for result in results:
            arc = result.get("emotional_arc", {})
            merged["emotional_arc"]["overall_mood_curve"].extend(arc.get("overall_mood_curve", []))

            design = result.get("sound_design", {})
            merged["sound_design"]["key_sfx_moments"].extend(design.get("key_sfx_moments", []))
            merged["sound_design"]["emotional_peaks"].extend(design.get("emotional_peaks", []))

        return merged

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """解析 JSON 响应"""
        text = text.strip()

        if text.startswith('```'):
            lines = text.split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            text = '\n'.join(json_lines)

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON 解析失败: {e}")
                return self._parse_fallback_from_partial(json_str)

        return self._parse_fallback("")

    def _parse_fallback(self, content: str) -> Dict[str, Any]:
        """备用解析方法"""
        characters = self._extract_characters_fallback(content)

        return {
            "novel_info": {
                "title": "未知标题",
                "genre": "其他",
                "setting": "未知背景",
                "language_level": "中等",
                "target_audience": "通用"
            },
            "characters": characters,
            "narrative_voice": {
                "type": "第三人称",
                "tone": "客观",
                "pacing": "中等",
                "voice_id": "Chinese_Male_Neutral",
                "narration_style": "标准叙述"
            },
            "chapters": [],
            "emotional_arc": {
                "overall_mood_curve": [],
                "climax_chapters": [],
                "pacing_analysis": "中等节奏"
            },
            "sound_design": {
                "key_sfx_moments": [],
                "emotional_peaks": [],
                "ambient_layering": "",
                "transition_sounds": []
            },
            "production_notes": "使用默认配置"
        }

    def _parse_fallback_from_partial(self, json_str: str) -> Dict[str, Any]:
        """从部分JSON中提取数据"""
        result = self._parse_fallback("")

        try:
            partial = json.loads(json_str)
            if 'novel_info' in partial:
                result['novel_info'].update(partial['novel_info'])
            if 'characters' in partial and isinstance(partial['characters'], list):
                result['characters'] = partial['characters']
            if 'chapters' in partial and isinstance(partial['chapters'], list):
                result['chapters'] = partial['chapters']
        except json.JSONDecodeError:
            pass

        return result

    def _extract_characters_fallback(self, content: str) -> List[Dict]:
        """正则提取角色"""
        patterns = [
            r'"([^"]{2,4})"\s*[：:]\s*"([^"]+)"',
            r'([\u4e00-\u9fa5]{2,4})\s*[说问道喊叫咆哮低声道高声道讲道]?\s*["""]([^"""]+)["""]',
        ]

        char_map = {}

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                name = match[0].strip() if len(match) > 1 else match[0]
                if 2 <= len(name) <= 4 and name not in ['他说', '她问', '我', '它']:
                    if name not in char_map:
                        char_map[name] = {
                            "name": name,
                            "role_type": "配角",
                            "gender": self._guess_gender(name),
                            "age": "unknown",
                            "personality": "未知",
                            "speaking_style": "普通",
                            "temperament": "中性",
                            "voice_id": self._auto_select_voice(name),
                            "voice_desc": "自动选择",
                            "catchphrase": "",
                            "special_mannerisms": "",
                            "emotion_range": ["neutral"],
                            "importance_score": 50
                        }

        return list(char_map.values())

    def _guess_gender(self, name: str) -> str:
        """猜测角色性别"""
        female_indicators = ['小姐', '夫人', '女士', '姑娘', '女儿', '姐', '妹', '妈']
        for indicator in female_indicators:
            if indicator in name:
                return 'female'
        return 'unknown'

    def _auto_select_voice(self, name: str, gender: str = 'unknown') -> str:
        """根据性别自动选择音色"""
        if gender == 'female':
            return 'female-tianmei'
        elif gender == 'male':
            return 'male-qn-qingse'
        return 'Chinese_Male_Neutral'

    def suggest_voice_for_character(
        self,
        gender: str = 'unknown',
        age: str = 'unknown',
        personality: str = '',
        speaking_style: str = ''
    ) -> str:
        """
        根据角色特征推荐音色

        Args:
            gender: 性别 (male/female/unknown)
            age: 年龄 (young/middle-aged/elderly/unknown)
            personality: 性格描述
            speaking_style: 说话风格

        Returns:
            推荐的 voice_id
        """
        text = f"{personality} {speaking_style}".lower()

        if gender == 'female':
            if any(kw in text for kw in ['温柔', '淑女', '优雅', '柔和', '体贴']):
                return 'female-shaoyu'
            if any(kw in text for kw in ['活泼', '可爱', '青春', '开朗']):
                return 'female-yunyang'
            if any(kw in text for kw in ['成熟', '知性', '冷静']):
                return 'Chinese_Female_Neutral'
            return 'female-tianmei'

        elif gender == 'male':
            if any(kw in text for kw in ['磁性', '优雅', '英俊', '王子']):
                return 'male-qn-qingse'
            if any(kw in text for kw in ['粗犷', '大叔', '硬汉', '豪爽']):
                return 'male-bada'
            if any(kw in text for kw in ['成熟', '稳重', '中年', '绅士']):
                return 'male-yuanfang'
            if any(kw in text for kw in ['年轻', '少年', '活力']):
                return 'male-tiancheng'
            return 'Chinese_Male_Neutral'

        return 'Chinese_Male_Neutral'

    def suggest_emotion_for_dialogue(self, text: str, context: str = '') -> Dict[str, str]:
        """
        根据对话内容自动识别情感

        Args:
            text: 对话文本
            context: 上下文（可选）

        Returns:
            {'emotion': 'happy', 'evidence': '关键词'}
        """
        combined = f"{context} {text}".lower()

        for emotion, keywords in self.EMOTION_MAPPING.items():
            for kw in keywords:
                if kw in combined:
                    return {
                        'emotion': emotion,
                        'evidence': kw,
                        'confidence': 0.8 if len(kw) > 1 else 0.6
                    }

        if any(p in combined for p in ['？', '?', '怎么', '什么', '为何', '为什么', '是不是', '难道']):
            return {'emotion': 'surprised', 'evidence': '疑问句式', 'confidence': 0.6}

        if any(p in combined for p in ['。', '，']):
            return {'emotion': 'neutral', 'evidence': '中性陈述', 'confidence': 0.7}

        return {'emotion': 'neutral', 'evidence': '默认', 'confidence': 0.5}

    def get_character_voice_mapping(self, analysis_result: Dict) -> Dict[str, str]:
        """获取角色-音色映射"""
        mapping = {}
        for char in analysis_result.get('characters', []):
            mapping[char['name']] = char.get('voice_id', 'Chinese_Male_Neutral')
        return mapping

    def get_scene_bgm_suggestions(self, analysis_result: Dict) -> List[Dict]:
        """提取场景BGM建议"""
        suggestions = []
        for chapter in analysis_result.get('chapters', []):
            for scene in chapter.get('scene_changes', []):
                bgm_config = scene.get('bgm', {})
                if isinstance(bgm_config, dict):
                    style = bgm_config.get('style', '')
                    instruments = bgm_config.get('instruments', '')
                    suggested_bgm = f"{style}，{instruments}"
                else:
                    suggested_bgm = bgm_config or ''

                suggestions.append({
                    'chapter': chapter.get('chapter_number'),
                    'scene_id': scene.get('scene_id'),
                    'location': scene.get('location'),
                    'mood': scene.get('mood'),
                    'bgm': suggested_bgm,
                    'bgm_volume': bgm_config.get('volume') if isinstance(bgm_config, dict) else 0.3,
                    'ambient_sound': scene.get('ambient_sound', {}),
                    'sfx_events': scene.get('sfx_events', []),
                })
        return suggestions

    def get_sound_design_summary(self, analysis_result: Dict) -> Dict[str, Any]:
        """获取音效设计摘要"""
        all_sfx = set()
        bgm_styles = set()
        locations = set()
        moods = set()

        for chapter in analysis_result.get('chapters', []):
            for scene in chapter.get('scene_changes', []):
                locations.add(scene.get('location', ''))
                moods.add(scene.get('mood', ''))

                bgm = scene.get('bgm', {})
                if isinstance(bgm, dict):
                    bgm_styles.add(bgm.get('style', ''))

                for sfx_event in scene.get('sfx_events', []):
                    all_sfx.add(sfx_event.get('type', ''))

        return {
            'total_scenes': sum(len(c.get('scene_changes', [])) for c in analysis_result.get('chapters', [])),
            'total_dialogues': sum(
                sum(len(s.get('dialogues', [])) for s in c.get('scene_changes', []))
                for c in analysis_result.get('chapters', [])
            ),
            'unique_locations': list(locations),
            'unique_moods': list(moods),
            'bgm_styles': list(bgm_styles),
            'sfx_types_used': list(all_sfx),
        }


def analyze_novel_content(content: str) -> Dict[str, Any]:
    """便捷函数：分析小说内容"""
    analyzer = DeepSeekNovelAnalyzer()
    return analyzer.analyze_novel(content)
