"""
MiniMax Music 音乐生成服务
使用 MiniMax API 生成背景音乐和音效
高品质 BGM 配置
"""
import os
import time
import base64
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class MiniMaxMusic:
    """MiniMax 音乐生成器 - 高品质配置"""

    BASE_URL = "https://api.minimax.io/v1"

    MUSIC_STYLES = {
        "epic": "史诗",
        "peaceful": "平静",
        "tense": "紧张",
        "romantic": "浪漫",
        "mysterious": "神秘",
        "action": "动作",
        "sad": "悲伤",
        "happy": "欢快",
        "folk": "民族风",
        "modern": "现代",
        "classical": "古典",
        "ambient": "氛围",
        "wuxia": "武侠",
        "scifi": "科幻",
        "horror": "恐怖",
    }

    def __init__(self):
        api_key = os.getenv('MINIMAX_API_KEY')
        group_id = os.getenv('MINIMAX_GROUP_ID')

        if not api_key or not group_id:
            raise ValueError("MINIMAX_API_KEY 或 MINIMAX_GROUP_ID 环境变量未设置")

        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.group_id = group_id

    def generate_music(
        self,
        prompt: str,
        model: str = "music-01",
        output_path: Optional[str] = None,
        duration: int = 60,
        wait_for_completion: bool = True,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        生成音乐 - 高品质参数

        Args:
            prompt: 音乐描述提示词
            model: 模型选择 (music-01/music-02)
            output_path: 输出文件路径
            duration: 期望时长（秒）
            wait_for_completion: 是否等待生成完成
            timeout: 超时时间（秒）

        Returns:
            生成结果，包含 audio_url 或 audio_file_path
        """
        try:
            response = self.client.audio.music.generate(
                model=model,
                prompt=prompt,
                duration=duration
            )

            result = {
                'success': True,
                'task_id': getattr(response, 'id', 'unknown'),
                'model': model,
                'prompt': prompt,
                'duration': duration
            }

            if hasattr(response, 'data') and response.data:
                audio_item = response.data[0]
                if hasattr(audio_item, 'audio_file') and audio_item.audio_file:
                    result['audio_url'] = audio_item.audio_file
                elif hasattr(audio_item, 'audio_url') and audio_item.audio_url:
                    result['audio_url'] = audio_item.audio_url

                    if output_path:
                        os.makedirs(os.path.dirname(output_path) or '/tmp', exist_ok=True)
                        self._download_audio(audio_item.audio_url, output_path)
                        result['audio_file_path'] = output_path

            return result

        except Exception as e:
            print(f"音乐生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _download_audio(self, url: str, output_path: str):
        """下载音频文件"""
        import requests
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)

    def generate_bgm_for_scene(
        self,
        scene_type: str,
        mood: str,
        setting: str = "",
        duration: int = 60,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据场景生成背景音乐

        Args:
            scene_type: 场景类型
            mood: 情绪
            setting: 背景设定
            duration: 时长（秒）
            output_path: 输出路径

        Returns:
            生成结果
        """
        prompt = self._build_bgm_prompt(scene_type, mood, setting)
        return self.generate_music(prompt, duration=duration, output_path=output_path)

    def _build_bgm_prompt(self, scene_type: str, mood: str, setting: str = "") -> str:
        """构建高质量 BGM 提示词"""
        parts = []

        if setting:
            if "古代" in setting or "武侠" in setting or "仙侠" in setting:
                parts.append("古风中国风")
            elif "现代" in setting:
                parts.append("现代都市")
            elif "奇幻" in setting or "玄幻" in setting:
                parts.append("奇幻魔法")
            elif "科幻" in setting or "未来" in setting:
                parts.append("科幻电子")
            elif "历史" in setting:
                parts.append("古典风格")
            elif "都市" in setting:
                parts.append("都市风格")

        if mood:
            mood_map = {
                "happy": "欢快愉悦，轻快活泼，木管乐器",
                "tense": "紧张悬疑，低沉紧迫，节奏感强",
                "sad": "悲伤忧郁，缓慢低沉，钢琴弦乐",
                "romantic": "浪漫温馨，柔情似水，弦乐竖琴",
                "mysterious": "神秘空灵，飘渺虚幻，电子合成",
                "calm": "平静舒缓，自然放松，钢琴吉他",
                "excited": "激动昂扬，振奋人心，鼓点铜管",
                "horror": "恐怖阴森，诡异紧张，低频震动",
                "peaceful": "宁静祥和，轻柔温和，钢琴自然",
                "epic": "史诗宏大，壮丽震撼，管弦乐团",
            }
            mood_text = mood_map.get(mood, mood)
            parts.append(mood_text)

        if scene_type:
            scene_map = {
                "battle": "战斗场景",
                "dialogue": "对话场景",
                "monologue": "独白沉思",
                "transition": "场景过渡",
                "climax": "高潮时刻",
                "opening": "开场序曲",
                "ending": "结尾终章",
                "opening_chapter": "章节开篇",
                "closing_chapter": "章节收尾",
            }
            scene_text = scene_map.get(scene_type, scene_type)
            parts.append(scene_text)

        parts.append("背景音乐，循环流畅，音质纯净")

        return "，".join(filter(None, parts))

    def generate_sound_effect(
        self,
        effect_type: str,
        description: str = "",
        duration: int = 5,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成音效

        Args:
            effect_type: 音效类型
            description: 详细描述
            duration: 时长（秒）
            output_path: 输出路径

        Returns:
            生成结果
        """
        prompt = self._build_sfx_prompt(effect_type, description)
        return self.generate_music(prompt, duration=duration, output_path=output_path)

    def _build_sfx_prompt(self, effect_type: str, description: str = "") -> str:
        """构建音效提示词"""
        sfx_presets = {
            "footstep_wood": "木地板脚步声，自然舒适，行走节奏",
            "footstep_stone": "石板路脚步声，回声空旷，坚定有力",
            "footstep_grass": "草地脚步声，轻柔自然，环境氛围",
            "footstep_stairs": "楼梯脚步声，上下节奏，木质结构",
            "knock": "敲门声，礼貌有节奏，三下敲门",
            "door_open_wood": "木门打开声，吱呀作响，自然音效",
            "door_close": "关门声，沉稳厚重，木质门扇",
            "rain_light": "细雨声，淅淅沥沥，轻柔舒缓",
            "rain_heavy": "暴雨声，倾盆大雨，激烈震撼",
            "thunder": "雷声，远处轰隆，暴风雨中",
            "wind_gentle": "微风声，轻柔拂过，自然舒适",
            "wind_strong": "强风声，呼啸而过，狂风大作",
            "bird_chirp": "鸟鸣声，清晨森林，婉转悦耳",
            "insect": "虫鸣声，夏夜草丛，此起彼伏",
            "water_stream": "流水声，小溪潺潺，自然清澈",
            "water_wave": "海浪声，波涛汹涌，广阔大海",
            "heartbeat_normal": "心跳声，正常节律，平稳有力",
            "heartbeat_fast": "快速心跳，紧张激动，加速心跳",
            "heartbeat_slow": "缓慢心跳，沉重悲伤，缓慢虚弱",
            "laugh": "欢笑声，愉快开心，热闹氛围",
            "cry": "哭泣声，悲伤抽泣，情感表达",
            "sigh": "叹息声，深沉感慨，情感释放",
            "breath_normal": "正常呼吸声，平稳自然",
            "breath_panic": "急促呼吸，紧张害怕，呼吸急促",
            "sword_clash": "剑击声，金属碰撞，武打音效",
            "horse_hoof": "马蹄声，奔跑有力，由远及近",
            "explosion": "爆炸声，震撼强烈，冲击波感",
            "phone_ring": "电话铃声，现代通讯，响铃提示",
            "clock_tick": "时钟滴答声，规律计时，岁月流逝",
            "page_turn": "翻书声，书页翻动，纸张质感",
            "cup_place": "茶杯放置声，瓷器碰撞，轻柔叮当",
            "bell_ancient": "古钟敲击，悠远回荡，庄严神秘",
        }

        if effect_type in sfx_presets:
            prompt = sfx_presets[effect_type]
        else:
            prompt = f"{effect_type}音效"

        if description:
            prompt += f"，{description}"

        return prompt

    def batch_generate_bgm(
        self,
        scenes: List[Dict[str, Any]],
        output_dir: str = "/tmp/bgm"
    ) -> List[Dict[str, Any]]:
        """
        批量生成背景音乐

        Args:
            scenes: 场景列表
            output_dir: 输出目录

        Returns:
            生成结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, scene in enumerate(scenes):
            try:
                output_path = os.path.join(output_dir, scene.get('filename', f'bgm_{i}.mp3'))

                result = self.generate_bgm_for_scene(
                    scene_type=scene.get('scene_type', 'dialogue'),
                    mood=scene.get('mood', 'calm'),
                    setting=scene.get('setting', ''),
                    duration=scene.get('duration', 60),
                    output_path=output_path
                )

                result['scene_id'] = i
                results.append(result)

            except Exception as e:
                results.append({
                    'success': False,
                    'scene_id': i,
                    'error': str(e)
                })

        return results


class MiniMaxMusicLibrary:
    """MiniMax 音乐库 - 高品质预设 BGM"""

    PRESET_BGMS = {
        "ancient_battle": {
            "prompt": "古风武侠，紧张激烈，琵琶+鼓点，打斗场景，史诗气势",
            "description": "古风战斗",
            "mood": "tense",
            "instruments": ["琵琶", "古筝", "鼓点", "笛子"]
        },
        "modern_romance": {
            "prompt": "现代浪漫，温馨柔情，钢琴+弦乐，对话场景，甜蜜氛围",
            "description": "现代言情",
            "mood": "romantic",
            "instruments": ["钢琴", "弦乐", "竖琴"]
        },
        "fantasy_adventure": {
            "prompt": "奇幻冒险，史诗宏大，管弦乐+合成器，冒险场景，神秘奇幻",
            "description": "奇幻冒险",
            "mood": "excited",
            "instruments": ["管弦乐", "合成器", "合唱"]
        },
        "mystery_tense": {
            "prompt": "悬疑紧张，神秘空灵，合成器+环境音，悬疑场景，扣人心弦",
            "description": "悬疑紧张",
            "mood": "mysterious",
            "instruments": ["合成器", "钟琴", "低音"]
        },
        "peaceful_nature": {
            "prompt": "平静自然，轻柔舒缓，钢琴+自然音效，平静场景，心旷神怡",
            "description": "自然平静",
            "mood": "calm",
            "instruments": ["钢琴", "吉他", "自然音"]
        },
        "sad_melancholy": {
            "prompt": "悲伤忧郁，忧伤缓慢，钢琴独奏，悲伤场景，催人泪下",
            "description": "悲伤忧郁",
            "mood": "sad",
            "instruments": ["钢琴", "大提琴", "弦乐"]
        },
        "happy_cheerful": {
            "prompt": "欢快活泼，轻快跳跃，钢琴+木管，欢快场景，阳光明媚",
            "description": "欢快活泼",
            "mood": "happy",
            "instruments": ["钢琴", "长笛", "木管"]
        },
        "epic_climax": {
            "prompt": "史诗高潮，宏大震撼，管弦乐团，高潮时刻，壮丽恢宏",
            "description": "史诗高潮",
            "mood": "epic",
            "instruments": ["交响乐团", "合唱", "铜管"]
        },
        "scene_transition": {
            "prompt": "过渡转场，自然流畅，轻柔音效，转场场景，衔接自然",
            "description": "场景转场",
            "mood": "calm",
            "instruments": ["钢琴", "弦乐", "轻柔敲击"]
        },
        "ancient_drama": {
            "prompt": "古风戏剧，典雅深沉，古筝+二胡，戏剧场景，韵味悠长",
            "description": "古风戏剧",
            "mood": "mysterious",
            "instruments": ["古筝", "二胡", "箫", "编钟"]
        },
        "wuxia_hero": {
            "prompt": "武侠江湖，侠义豪情，琵琶+箫，英雄气概，快意恩仇",
            "description": "武侠豪情",
            "mood": "tense",
            "instruments": ["琵琶", "箫", "鼓"]
        },
        "scifi_future": {
            "prompt": "科幻未来，电子合成，空间感强，未来场景，神秘深邃",
            "description": "科幻未来",
            "mood": "mysterious",
            "instruments": ["合成器", "电子音", "低频"]
        },
        "horror_dark": {
            "prompt": "恐怖阴森，诡异紧张，低频震动，恐怖场景，毛骨悚然",
            "description": "恐怖悬疑",
            "mood": "horror",
            "instruments": ["低频音", "合成器", "不协和音"]
        },
        "romance_tender": {
            "prompt": "柔情似水，温馨浪漫，小提琴+钢琴，恋爱场景，心动时刻",
            "description": "柔情浪漫",
            "mood": "romantic",
            "instruments": ["小提琴", "钢琴", "弦乐"]
        },
        "tension_build": {
            "prompt": "紧张积累，悬疑递进，低音弦乐，紧张铺垫，悬念迭起",
            "description": "紧张铺垫",
            "mood": "tense",
            "instruments": ["低音弦乐", "定音鼓", "铜管"]
        },
    }

    def __init__(self):
        self.music_generator = MiniMaxMusic()
        self._cache = {}
        self._sfx_cache = {}

    def get_preset_bgm(
        self,
        preset_key: str,
        output_path: str = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取预设BGM"""
        if preset_key not in self.PRESET_BGMS:
            return {'success': False, 'error': f'未知预设: {preset_key}'}

        cache_key = f"bgm_{preset_key}"
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached.get('path') and os.path.exists(cached.get('path')):
                return {
                    'success': True,
                    'audio_url': cached.get('url'),
                    'audio_file_path': cached['path'],
                    'from_cache': True,
                    'preset': preset_key
                }

        preset = self.PRESET_BGMS[preset_key]
        output = output_path or f"/tmp/{preset_key}.mp3"

        result = self.music_generator.generate_music(
            prompt=preset['prompt'],
            output_path=output,
            duration=120
        )

        if result.get('success'):
            self._cache[cache_key] = {
                'url': result.get('audio_url'),
                'path': result.get('audio_file_path'),
                'preset': preset_key
            }

        result['preset'] = preset_key
        return result

    def get_bgm_for_mood(
        self,
        mood: str,
        setting: str = "",
        duration: int = 60
    ) -> Dict[str, Any]:
        """根据情绪获取最合适的 BGM"""
        mood_to_preset = {
            'happy': 'happy_cheerful',
            'tense': 'tension_build',
            'sad': 'sad_melancholy',
            'romantic': 'romance_tender',
            'mysterious': 'mystery_tense',
            'calm': 'peaceful_nature',
            'excited': 'epic_climax',
            'horror': 'horror_dark',
        }

        if setting:
            if '古' in setting or '武' in setting or '仙' in setting:
                mood_to_preset['tense'] = 'ancient_battle'
                mood_to_preset['calm'] = 'ancient_drama'
            elif '科' in setting or '未来' in setting:
                mood_to_preset['mysterious'] = 'scifi_future'

        preset_key = mood_to_preset.get(mood, 'peaceful_nature')
        return self.get_preset_bgm(preset_key, duration=duration)

    def get_sfx(
        self,
        sfx_type: str,
        duration: int = 3,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取音效"""
        cache_key = f"sfx_{sfx_type}"
        if use_cache and cache_key in self._sfx_cache:
            cached = self._sfx_cache[cache_key]
            if cached.get('path') and os.path.exists(cached.get('path')):
                return {
                    'success': True,
                    'audio_url': cached.get('url'),
                    'audio_file_path': cached['path'],
                    'from_cache': True,
                    'sfx_type': sfx_type
                }

        sfx_presets = {
            '笑声': '欢笑声，愉快开心，热闹氛围',
            '哭声': '哭泣声，悲伤抽泣，情感表达',
            '雨声': '细雨声，淅淅沥沥，轻柔舒缓',
            '雷声': '雷声，远处轰隆，暴风雨中',
            '风声': '微风声，轻柔拂过，自然舒适',
            '心跳声': '心跳声，紧张激动，加速心跳',
            '叹息声': '叹息声，深沉感慨，情感释放',
            '脚步声': '木地板脚步声，自然舒适，行走节奏',
            '开门声': '木门打开声，吱呀作响，自然音效',
            '敲门声': '敲门声，礼貌有节奏，三下敲门',
            '海浪声': '海浪声，波涛汹涌，广阔大海',
            '鸟鸣声': '鸟鸣声，清晨森林，婉转悦耳',
            '流水声': '流水声，小溪潺潺，自然清澈',
            '钟声': '古钟敲击，悠远回荡，庄严神秘',
        }

        prompt = sfx_presets.get(sfx_type, f'{sfx_type}音效')
        output_path = f"/tmp/sfx_{sfx_type}_{duration}s.mp3"

        result = self.music_generator.generate_music(
            prompt=prompt,
            duration=duration,
            output_path=output_path
        )

        if result.get('success'):
            self._sfx_cache[cache_key] = {
                'url': result.get('audio_url'),
                'path': result.get('audio_file_path'),
                'sfx_type': sfx_type
            }

        result['sfx_type'] = sfx_type
        return result

    def get_all_presets(self) -> Dict[str, Dict]:
        """获取所有预设"""
        return {
            key: {
                'prompt': val['prompt'],
                'description': val['description'],
                'mood': val.get('mood', ''),
                'instruments': val.get('instruments', [])
            }
            for key, val in self.PRESET_BGMS.items()
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self._sfx_cache.clear()


def generate_music(prompt: str, output_path: str = None) -> Dict[str, Any]:
    """便捷函数：生成音乐"""
    music = MiniMaxMusic()
    return music.generate_music(prompt, output_path=output_path)


def generate_scene_bgm(
    scene_type: str,
    mood: str,
    setting: str = "",
    output_path: str = None
) -> Dict[str, Any]:
    """便捷函数：根据场景生成BGM"""
    music = MiniMaxMusic()
    return music.generate_bgm_for_scene(scene_type, mood, setting, output_path=output_path)
