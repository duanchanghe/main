"""
AI 音频合成服务
严格遵循 DeepSeek 提取的音效和BGM切入点
"""
import os
import re
import time
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from django.conf import settings

from services.deepseek_extractor import DeepSeekNovelAnalyzer
from services.minimax_tts import MiniMaxTTS, MiniMaxTTSManager
from services.minimax_music import MiniMaxMusicLibrary

logger = logging.getLogger(__name__)


class AudioProductionError(Exception):
    """音频制作异常"""
    pass


class AIAudioProducer:
    """AI 音频制作器 - 基于 DeepSeek 精确分析"""

    SFX_KEYWORD_MAP = {
        "脚步": "脚步声",
        "走": "脚步声",
        "步行": "脚步声",
        "敲门": "敲门声",
        "叩门": "敲门声",
        "关门": "关门声",
        "门关": "关门声",
        "开门": "开门声",
        "推门": "开门声",
        "雨": "雨声",
        "下雨": "雨声",
        "雷": "雷声",
        "闪电": "雷声",
        "风": "风声",
        "马": "马蹄声",
        "骑马": "马蹄声",
        "剑": "剑击声",
        "刀": "剑击声",
        "砍": "剑击声",
        "劈": "剑击声",
        "斩": "剑击声",
        "喊": "喊叫声",
        "叫": "喊叫声",
        "吼": "喊叫声",
        "咆哮": "喊叫声",
        "笑": "笑声",
        "哈哈": "笑声",
        "欢笑": "笑声",
        "叹": "叹息声",
        "唉": "叹息声",
        "心跳": "心跳声",
        "紧张": "心跳声",
        "害怕": "心跳声",
        "电话": "电话铃声",
        "手机响": "电话铃声",
        "铃声": "电话铃声",
        "鸟": "鸟鸣声",
        "鸟鸣": "鸟鸣声",
        "水": "流水声",
        "溪": "流水声",
        "河": "流水声",
        "流水": "流水声",
        "茶": "茶杯声",
        "品茶": "茶杯声",
        "纸": "纸张声",
        "翻书": "纸张声",
        "钟": "钟声",
        "古钟": "钟声",
        "撞": "撞击声",
        "碰撞": "撞击声",
        "砰": "撞击声",
        "爆炸": "爆炸声",
        "炸": "爆炸声",
        "火": "火焰声",
        "燃烧": "火焰声",
        "狼": "狼嚎声",
        "嚎叫": "狼嚎声",
        "海": "海浪声",
        "浪": "海浪声",
        "鼓掌": "掌声",
        "喝彩": "掌声",
    }

    SFX_PRESETS = {
        "脚步声": {"prompt": "脚步声，木地板，自然走路节奏", "duration": 2},
        "敲门声": {"prompt": "敲门声，礼貌敲门三下", "duration": 1},
        "关门声": {"prompt": "关门声，木门关闭", "duration": 1},
        "开门声": {"prompt": "开门声，木门吱呀打开", "duration": 1},
        "风声": {"prompt": "风声，自然环境微风", "duration": 3},
        "雷声": {"prompt": "雷声，远处轰隆", "duration": 2},
        "雨声": {"prompt": "雨声，细雨淅沥", "duration": 3},
        "马蹄声": {"prompt": "马蹄声，奔跑中的马", "duration": 2},
        "剑击声": {"prompt": "剑击声，金属碰撞", "duration": 1},
        "喊叫声": {"prompt": "人群喧哗声，远距离呼喊", "duration": 2},
        "笑声": {"prompt": "笑声，愉快的笑声", "duration": 1},
        "叹息声": {"prompt": "叹息声，深沉叹息", "duration": 1},
        "心跳声": {"prompt": "心跳声，紧张加速的心跳", "duration": 1},
        "电话铃声": {"prompt": "电话铃声，响铃", "duration": 3},
        "汽车声": {"prompt": "汽车声，城市背景交通", "duration": 3},
        "鸟鸣声": {"prompt": "鸟鸣声，清晨鸟叫", "duration": 3},
        "流水声": {"prompt": "流水声，小溪潺潺", "duration": 3},
        "茶杯声": {"prompt": "茶杯碰撞声，瓷器轻碰", "duration": 1},
        "纸张声": {"prompt": "纸张翻动声", "duration": 1},
        "钟声": {"prompt": "古钟敲击声，悠远回荡", "duration": 3},
        "撞击声": {"prompt": "撞击声，物体碰撞", "duration": 1},
        "爆炸声": {"prompt": "爆炸声，剧烈轰鸣", "duration": 2},
        "火焰声": {"prompt": "火焰燃烧声，噼啪作响", "duration": 3},
        "狼嚎声": {"prompt": "狼嚎声，荒野回荡", "duration": 2},
        "海浪声": {"prompt": "海浪声，波涛汹涌", "duration": 3},
        "掌声": {"prompt": "掌声，观众的掌声", "duration": 2},
    }

    def __init__(self):
        self.deepseek = DeepSeekNovelAnalyzer()
        self.tts = MiniMaxTTS()
        self.music = MiniMaxMusicLibrary()
        self._sfx_cache = {}
        self._cache_lock = threading.Lock()

    def analyze_novel(self, content: str, max_chars: int = 10000) -> Dict[str, Any]:
        """分析小说文本"""
        return self.deepseek.analyze_novel(content, max_chars)

    def save_analysis_to_models(self, novel, analysis_result: Dict) -> Dict[str, Any]:
        """保存 DeepSeek 分析结果到数据库模型"""
        from novels.models import Novel, Character, Scene, Dialogue

        novel.ai_analysis = analysis_result
        novel.genre = analysis_result.get('novel_info', {}).get('genre', 'other')
        novel.setting = analysis_result.get('novel_info', {}).get('setting', '')
        novel.save()

        created_chars = {}
        for char_data in analysis_result.get('characters', []):
            char, created = Character.objects.get_or_create(
                novel=novel,
                name=char_data['name'],
                defaults={
                    'role_type': char_data.get('role_type', 'supporting'),
                    'gender': char_data.get('gender', 'unknown'),
                    'age': char_data.get('age', 'unknown'),
                    'voice_id': char_data.get('voice_id', 'Chinese_Male_Neutral'),
                    'importance_score': char_data.get('importance_score', 50),
                    'auto_detected': True,
                }
            )
            created_chars[char_data['name']] = char

        for chapter_data in analysis_result.get('chapters', []):
            chapter_num = chapter_data.get('chapter_number', 1)

            for scene_data in chapter_data.get('scene_changes', []):
                scene, _ = Scene.objects.get_or_create(
                    novel=novel,
                    chapter_number=chapter_num,
                    scene_id=scene_data.get('scene_id', 1),
                    defaults={
                        'location': scene_data.get('location', ''),
                        'time_of_day': scene_data.get('time_of_day', ''),
                        'season': scene_data.get('season', ''),
                        'weather': scene_data.get('weather', ''),
                        'atmosphere': scene_data.get('atmosphere', ''),
                        'mood': scene_data.get('mood', 'calm'),
                        'suggested_bgm': self._extract_bgm_from_deepseek(scene_data),
                        'suggested_sfx': self._extract_sfx_list_from_deepseek(scene_data),
                        'bgm_volume': self._get_bgm_volume(scene_data),
                        'sfx_volume': self._get_sfx_volume(scene_data),
                        'narration_text': scene_data.get('narration', ''),
                    }
                )

                for dialogue_data in scene_data.get('dialogues', []):
                    char_name = dialogue_data.get('character', '')
                    if char_name in created_chars:
                        Dialogue.objects.create(
                            scene=scene,
                            character=created_chars[char_name],
                            text=dialogue_data.get('text', ''),
                            emotion=dialogue_data.get('emotion', 'neutral'),
                            volume=dialogue_data.get('volume', 'normal'),
                            speed=dialogue_data.get('speed', 'normal'),
                            special_effects=self._extract_dialogue_sfx(dialogue_data),
                            order=dialogue_data.get('id', 0),
                        )

        return {
            'characters_count': len(created_chars),
            'scenes_count': Scene.objects.filter(novel=novel).count(),
        }

    def _extract_bgm_from_deepseek(self, scene_data: Dict) -> str:
        """从 DeepSeek 数据中提取 BGM 描述"""
        bgm = scene_data.get('bgm', {})
        if isinstance(bgm, dict):
            style = bgm.get('style', '')
            instruments = bgm.get('instruments', '')
            return f"{style}，{instruments}"
        return scene_data.get('suggested_bgm', '')

    def _extract_sfx_list_from_deepseek(self, scene_data: Dict) -> List[str]:
        """从 DeepSeek 数据中提取音效列表"""
        sfx_list = []

        explicit_sfx = scene_data.get('suggested_sfx', [])
        if explicit_sfx:
            sfx_list.extend(explicit_sfx)

        sfx_events = scene_data.get('sfx_events', [])
        for event in sfx_events:
            sfx_type = event.get('type', '')
            if sfx_type and sfx_type not in sfx_list:
                sfx_list.append(sfx_type)

        ambient = scene_data.get('ambient_sound', {})
        if isinstance(ambient, dict):
            desc = ambient.get('description', '')
            if desc:
                mapped = self._map_text_to_sfx(desc)
                sfx_list.extend(mapped)

        return list(set(sfx_list))[:5]

    def _extract_dialogue_sfx(self, dialogue_data: Dict) -> str:
        """从对话数据中提取音效信息"""
        sfx_info = dialogue_data.get('sfx', {})
        if isinstance(sfx_info, dict):
            return sfx_info.get('description', '')
        return dialogue_data.get('special_effects', '')

    def _get_bgm_volume(self, scene_data: Dict) -> float:
        """获取 BGM 音量"""
        bgm = scene_data.get('bgm', {})
        if isinstance(bgm, dict) and 'volume' in bgm:
            return float(bgm['volume'])
        return float(scene_data.get('bgm_volume', 0.3))

    def _get_sfx_volume(self, scene_data: Dict) -> float:
        """获取 SFX 音量"""
        if isinstance(scene_data.get('ambient_sound'), dict):
            vol = scene_data['ambient_sound'].get('volume')
            if vol is not None:
                return float(vol)
        return float(scene_data.get('sfx_volume', 0.5))

    def _map_text_to_sfx(self, text: str) -> List[str]:
        """将文本关键词映射到音效"""
        result = []
        for keyword, sfx in self.SFX_KEYWORD_MAP.items():
            if keyword in text and sfx not in result:
                result.append(sfx)
        return result

    def generate_audiobook(
        self,
        novel,
        use_multi_voice: bool = True,
        use_bgm: bool = True,
        use_sfx: bool = True,
        progress_callback=None
    ) -> str:
        """生成完整有声书 - 严格遵循 DeepSeek 分析"""
        from novels.models import Character, Scene, Dialogue

        media_dir = settings.MEDIA_ROOT / 'audiobooks'
        os.makedirs(media_dir, exist_ok=True)
        output_file = media_dir / f'{novel.id}_audiobook.mp3'

        analysis = novel.ai_analysis or {}

        audio_segments = []
        tts_manager = MiniMaxTTSManager()

        if use_multi_voice:
            for char in Character.objects.filter(novel=novel):
                tts_manager.register_character_voice(
                    character_name=char.name,
                    voice_id=char.voice_id,
                    emotion='neutral'
                )
        else:
            tts_manager.register_character_voice(
                character_name='narrator',
                voice_id='Chinese_Male_Neutral',
                emotion='neutral'
            )

        scenes = Scene.objects.filter(novel=novel).order_by('chapter_number', 'scene_id')
        total_scenes = scenes.count()

        for idx, scene in enumerate(scenes):
            scene_analysis = self._get_scene_analysis(analysis, scene)

            scene_audio = self._generate_scene_audio(
                scene=scene,
                scene_analysis=scene_analysis,
                tts_manager=tts_manager,
                use_multi_voice=use_multi_voice,
                use_bgm=use_bgm,
                use_sfx=use_sfx,
                output_dir=media_dir / f'scene_{scene.id}'
            )
            audio_segments.append(scene_audio)

            if progress_callback:
                progress = int((idx + 1) / total_scenes * 100)
                progress_callback(progress)

        self._merge_audio_segments(
            segments=audio_segments,
            output_path=str(output_file)
        )

        return str(output_file)

    def _get_scene_analysis(self, analysis: Dict, scene) -> Dict:
        """从 DeepSeek 分析结果中获取场景对应的分析数据"""
        chapter_num = scene.chapter_number
        scene_id = scene.scene_id

        for chapter in analysis.get('chapters', []):
            if chapter.get('chapter_number') == chapter_num:
                for s in chapter.get('scene_changes', []):
                    if s.get('scene_id') == scene_id:
                        return s

        return {}

    def _generate_scene_audio(
        self,
        scene,
        scene_analysis: Dict,
        tts_manager,
        use_multi_voice: bool,
        use_bgm: bool,
        use_sfx: bool,
        output_dir
    ) -> Dict[str, Any]:
        """生成单个场景的音频 - 基于 DeepSeek 精确切入点"""
        from pydub import AudioSegment

        os.makedirs(output_dir, exist_ok=True)

        dialogues = scene.dialogues.all().order_by('order')
        total_dialogues = dialogues.count()

        dialogue_audios = []
        dialogue_durations = []
        sfx_timeline = []

        if use_sfx:
            ambient_sfx = self._prepare_ambient_sfx(scene, scene_analysis, output_dir)
            scene_sfx_events = self._extract_sfx_events(scene_analysis)
        else:
            ambient_sfx = None
            scene_sfx_events = []

        for idx, dialogue in enumerate(dialogues):
            char_name = dialogue.character.name if use_multi_voice else 'narrator'

            audio_path = tts_manager.convert_dialogue(
                character=char_name,
                text=dialogue.text,
                emotion=dialogue.emotion,
                output_path=str(output_dir / f'dialogue_{dialogue.id}.mp3')
            )

            dialogue.audio_path = audio_path
            dialogue.save()

            dialogue_audio = AudioSegment.from_mp3(audio_path)
            dialogue_duration = len(dialogue_audio)

            dialogue_sfx = self._extract_dialogue_sfx_events(dialogue, scene_analysis, idx, total_dialogues)
            sfx_timeline.extend(dialogue_sfx)

            dialogue_audios.append(dialogue_audio)
            dialogue_durations.append(dialogue_duration)

        if scene.narration_text and not dialogues.exists():
            audio_path = tts_manager.convert_dialogue(
                character='narrator',
                text=scene.narration_text,
                emotion='neutral',
                output_path=str(output_dir / 'narration.mp3')
            )
            narration_audio = AudioSegment.from_mp3(audio_path)
            dialogue_audios.append(narration_audio)
            dialogue_durations.append(len(narration_audio))

        scene_audio = AudioSegment.silent(duration=0)
        current_position = 0

        for i, (d_audio, d_duration) in enumerate(zip(dialogue_audios, dialogue_durations)):
            position_sfx = [sfx for sfx in sfx_timeline if sfx['target_dialogue'] == i]

            if position_sfx:
                segment_with_sfx = self._add_sfx_to_segment(
                    d_audio, position_sfx, current_position, output_dir
                )
                scene_audio = scene_audio + segment_with_sfx
            else:
                scene_audio = scene_audio + d_audio

            current_position += d_duration
            scene_audio = scene_audio + AudioSegment.silent(duration=500)
            current_position += 500

        scene_file = output_dir / 'scene_audio.mp3'
        scene_audio.export(str(scene_file), format='mp3')

        if use_bgm:
            bgm_result = self._generate_bgm_from_deepseek(scene, scene_analysis, len(scene_audio), output_dir)
            if bgm_result.get('success') and bgm_result.get('path'):
                bgm_audio = AudioSegment.from_mp3(bgm_result['path'])
                bgm_audio = self._apply_bgm_timing(bgm_audio, scene_analysis, len(scene_audio))
                bgm_audio = bgm_audio[:len(scene_audio)]
                volume = scene.bgm_volume
                bgm_audio = bgm_audio.apply_gain(-20 + 20 * volume)
                scene_audio = scene_audio.overlay(bgm_audio)
                scene_audio.export(str(scene_file), format='mp3')

        return {'path': str(scene_file), 'duration': len(scene_audio)}

    def _prepare_ambient_sfx(self, scene, scene_analysis: Dict, output_dir) -> Optional[Dict]:
        """准备环境音效 - 基于 DeepSeek 分析"""
        ambient = scene_analysis.get('ambient_sound', {})
        if not ambient:
            return None

        desc = ambient.get('description', '')
        if not desc:
            return None

        sfx_name = self._map_text_to_sfx(desc)
        if sfx_name:
            sfx_path = self._get_or_generate_sfx(sfx_name[0], output_dir)
            if sfx_path:
                return {
                    'path': sfx_path,
                    'volume': ambient.get('volume', 0.3),
                    'continuous': ambient.get('continuous', True)
                }

        return None

    def _extract_sfx_events(self, scene_analysis: Dict) -> List[Dict]:
        """从 DeepSeek 分析中提取场景级音效事件"""
        events = []
        sfx_events = scene_analysis.get('sfx_events', [])

        for event in sfx_events:
            sfx_type = event.get('type', '')
            if sfx_type in self.SFX_PRESETS:
                events.append({
                    'type': sfx_type,
                    'position_ms': event.get('position_ms', 0),
                    'duration': event.get('duration', 1000),
                    'volume': event.get('volume', 0.5),
                    'fade_in': event.get('fade_in', 0),
                    'fade_out': event.get('fade_out', 0),
                    'repeat': event.get('repeat', 1),
                    'description': event.get('description', ''),
                    'target_dialogue': -1,
                })

        return events

    def _extract_dialogue_sfx_events(self, dialogue, scene_analysis: Dict, dialogue_idx: int, total: int) -> List[Dict]:
        """从 DeepSeek 分析中提取对话级音效事件"""
        events = []

        dialogues_analysis = scene_analysis.get('dialogues', [])
        dialogue_analysis = None
        
        dialogue_char_name = getattr(dialogue.character, 'name', None)
        
        for d in dialogues_analysis:
            char_name_in_analysis = d.get('character', '')
            dialogue_id_in_analysis = d.get('id')
            
            if dialogue_id_in_analysis == dialogue.id:
                dialogue_analysis = d
                break
            if dialogue_char_name and char_name_in_analysis == dialogue_char_name:
                dialogue_analysis = d
                break

        if dialogue_analysis:
            sfx_data = dialogue_analysis.get('sfx', {})
            if isinstance(sfx_data, dict) and sfx_data.get('type'):
                sfx_types = sfx_data['type'] if isinstance(sfx_data['type'], list) else [sfx_data['type']]
                for sfx_type in sfx_types:
                    if sfx_type in self.SFX_PRESETS:
                        events.append({
                            'type': sfx_type,
                            'position_ms': sfx_data.get('position_ms', 0),
                            'duration': sfx_data.get('duration', 1000),
                            'volume': sfx_data.get('volume', 0.5),
                            'timing': sfx_data.get('timing', 'during'),
                            'description': sfx_data.get('description', ''),
                            'target_dialogue': dialogue_idx,
                        })

        dialogue_text = getattr(dialogue, 'text', '') or ''
        text_sfx = self._map_text_to_sfx(dialogue_text)
        for sfx_type in text_sfx[:2]:
            if not any(e['type'] == sfx_type for e in events):
                events.append({
                    'type': sfx_type,
                    'position_ms': 0,
                    'duration': 1000,
                    'volume': 0.3,
                    'timing': 'during',
                    'description': '文本关键词触发',
                    'target_dialogue': dialogue_idx,
                })

        return events

    def _add_sfx_to_segment(
        self,
        audio_segment: 'AudioSegment',
        sfx_events: List[Dict],
        segment_start: int,
        output_dir
    ) -> 'AudioSegment':
        """为音频片段添加音效 - 严格按 DeepSeek 位置"""
        from pydub import AudioSegment

        result = audio_segment

        for event in sfx_events:
            sfx_type = event['type']
            position_ms = event.get('position_ms', 0)
            timing = event.get('timing', 'during')
            duration = event.get('duration', 1000)
            volume = event.get('volume', 0.5)
            fade_in = event.get('fade_in', 0)
            fade_out = event.get('fade_out', 0)
            repeat = event.get('repeat', 1)

            sfx_path = self._get_or_generate_sfx(sfx_type, output_dir)
            if not sfx_path:
                continue

            for _ in range(repeat):
                sfx_audio = AudioSegment.from_mp3(sfx_path)
                sfx_audio = sfx_audio[:duration]

                adjusted_vol = -20 + 20 * volume
                sfx_audio = sfx_audio.apply_gain(adjusted_vol)

                if fade_in > 0:
                    sfx_audio = sfx_audio.fade_in(fade_in * 1000)
                if fade_out > 0:
                    sfx_audio = sfx_audio.fade_out(fade_out * 1000)

                if timing == 'before':
                    insert_pos = max(0, position_ms - duration)
                elif timing == 'after':
                    insert_pos = position_ms + duration
                else:
                    insert_pos = position_ms

                insert_pos = min(insert_pos, len(result))

                result = result.overlay(sfx_audio, position=insert_pos)

        return result

    def _generate_bgm_from_deepseek(
        self, scene, scene_analysis: Dict, audio_duration: int, output_dir
    ) -> Dict[str, Any]:
        """根据 DeepSeek 分析生成 BGM - 严格按分析配置"""
        bgm_config = scene_analysis.get('bgm', {})
        if not bgm_config:
            mood_to_preset = {
                'happy': 'happy_cheerful',
                'tense': 'mystery_tense',
                'sad': 'sad_melancholy',
                'romantic': 'modern_romance',
                'mysterious': 'mystery_tense',
                'calm': 'peaceful_nature',
                'excited': 'epic_climax',
                'horror': 'mystery_tense',
            }
            preset_key = mood_to_preset.get(scene.mood, 'peaceful_nature')
            result = self.music.get_preset_bgm(preset_key)
            if result.get('success') and result.get('audio_file_path'):
                return {'success': True, 'path': result['audio_file_path'], 'config': bgm_config}
            return {'success': False}

        style = bgm_config.get('style', '')
        instruments = bgm_config.get('instruments', '')
        prompt = f"{style}，{instruments}" if instruments else style

        if not prompt:
            prompt = scene.suggested_bgm or '背景音乐'

        bgm_file = output_dir / 'scene_bgm.mp3'
        result = self.music.generate_music(
            prompt=prompt,
            output_path=str(bgm_file),
            duration=max(60, audio_duration // 1000 + 10)
        )

        if result.get('success') and result.get('audio_file_path'):
            return {'success': True, 'path': result['audio_file_path'], 'config': bgm_config}

        return {'success': False}

    def _apply_bgm_timing(
        self, bgm_audio: 'AudioSegment', scene_analysis: Dict, audio_duration: int
    ) -> 'AudioSegment':
        """应用 DeepSeek 指定的 BGM 时机"""
        bgm_config = scene_analysis.get('bgm', {})

        fade_in = bgm_config.get('fade_in', 0)
        fade_out = bgm_config.get('fade_out', 0)

        if fade_in > 0:
            bgm_audio = bgm_audio.fade_in(fade_in * 1000)

        loop = bgm_config.get('loop', True)
        if not loop:
            fade_out_time = bgm_config.get('fade_out', 2)
            bgm_audio = bgm_audio.fade_out(fade_out_time * 1000)

        return bgm_audio

    def _get_or_generate_sfx(self, sfx_name: str, output_dir) -> Optional[str]:
        """获取或生成音效"""
        with self._cache_lock:
            if sfx_name in self._sfx_cache:
                return self._sfx_cache[sfx_name]

        if sfx_name not in self.SFX_PRESETS:
            return None

        preset = self.SFX_PRESETS[sfx_name]
        sfx_file = os.path.join(str(output_dir), f'sfx_{sfx_name}.mp3')

        try:
            result = self.music.generate_music(
                prompt=preset['prompt'],
                duration=preset['duration'],
                output_path=sfx_file
            )
            if result.get('success') and result.get('audio_file_path'):
                with self._cache_lock:
                    self._sfx_cache[sfx_name] = result['audio_file_path']
                return result['audio_file_path']
        except Exception as e:
            print(f"生成音效失败 {sfx_name}: {e}")

        return None

    def _merge_audio_segments(
        self,
        segments: List[Dict[str, Any]],
        output_path: str
    ):
        """合并音频片段"""
        from pydub import AudioSegment

        combined = AudioSegment.silent(duration=0)

        for segment in segments:
            if os.path.exists(segment.get('path', '')):
                audio = AudioSegment.from_mp3(segment['path'])
                combined = combined + audio + AudioSegment.silent(duration=1000)

        combined.export(output_path, format='mp3')

    def get_available_sfx(self) -> List[str]:
        """获取可用的音效列表"""
        return list(self.SFX_PRESETS.keys())

    def generate_audiobook_with_job(
        self,
        job_id: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """基于任务ID生成有声书（带完整状态管理）"""
        from novels.models import AudioJob, AudioSegment

        try:
            job = AudioJob.objects.select_related('novel').get(id=job_id)
        except AudioJob.DoesNotExist:
            raise AudioProductionError(f"任务 {job_id} 不存在")

        if job.status in ('completed', 'cancelled'):
            return {
                'success': False,
                'error': f"任务状态为 {job.get_status_display()}，无法执行"
            }

        novel = job.novel
        analysis = novel.ai_analysis

        if not analysis:
            job.status = 'failed'
            job.error_message = '小说尚未进行AI分析'
            job.save()
            raise AudioProductionError('小说尚未进行AI分析')

        try:
            job.status = 'generating'
            job.started_at = datetime.now()
            job.current_step = '初始化音频生成'
            job.save()

            media_dir = settings.MEDIA_ROOT / 'audiobooks' / f'job_{job.id}'
            os.makedirs(media_dir, exist_ok=True)

            job.total_scenes = novel.scenes.count()
            job.save()

            self._generate_audio_with_job(
                job=job,
                novel=novel,
                analysis=analysis,
                media_dir=media_dir,
                progress_callback=progress_callback
            )

            output_file = media_dir / f'{novel.id}_audiobook.mp3'
            self._merge_audio_segments(
                segments=AudioSegment.objects.filter(job=job).values('path', 'duration_ms'),
                output_path=str(output_file)
            )

            job.status = 'completed'
            job.progress = 100
            job.output_path = str(output_file)
            job.completed_at = datetime.now()
            job.current_step = '制作完成'
            job.save()

            logger.info(f"有声书生成完成: {job.id}")
            return {
                'success': True,
                'output_path': str(output_file),
                'job_id': job.id
            }

        except Exception as e:
            logger.exception(f"有声书生成失败: {job.id}")
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            raise AudioProductionError(f"生成失败: {e}")

    def _generate_audio_with_job(
        self,
        job: 'AudioJob',
        novel,
        analysis: Dict,
        media_dir,
        progress_callback: Optional[Callable]
    ):
        """使用任务对象生成音频"""
        from novels.models import Scene, AudioSegment, Character

        tts_manager = MiniMaxTTSManager()

        if job.use_multi_voice:
            for char in Character.objects.filter(novel=novel):
                tts_manager.register_character_voice(
                    character_name=char.name,
                    voice_id=char.voice_id,
                    emotion='neutral'
                )
        else:
            tts_manager.register_character_voice(
                character_name='narrator',
                voice_id='Chinese_Male_Neutral',
                emotion='neutral'
            )

        scenes = Scene.objects.filter(novel=novel).order_by('chapter_number', 'scene_id')
        total = scenes.count()

        for idx, scene in enumerate(scenes):
            scene_analysis = self._get_scene_analysis(analysis, scene)

            AudioSegment.objects.update_or_create(
                job=job,
                scene=scene,
                defaults={'status': 'processing'}
            )

            try:
                segment_info = self._generate_scene_audio(
                    scene=scene,
                    scene_analysis=scene_analysis,
                    tts_manager=tts_manager,
                    use_multi_voice=job.use_multi_voice,
                    use_bgm=job.use_bgm,
                    use_sfx=job.use_sfx,
                    output_dir=media_dir / f'scene_{scene.id}'
                )

                AudioSegment.objects.filter(job=job, scene=scene).update(
                    output_path=segment_info['path'],
                    duration_ms=segment_info['duration'],
                    status='completed'
                )

            except Exception as e:
                AudioSegment.objects.filter(job=job, scene=scene).update(
                    status='failed',
                    error_message=str(e)
                )
                logger.error(f"场景 {scene.id} 生成失败: {e}")

            job.completed_scenes = idx + 1
            job.progress = int((idx + 1) / total * 100)
            job.current_step = f'处理场景 {idx + 1}/{total}'
            job.save()

            if progress_callback:
                progress_callback(job.progress, job.current_step)

    def cancel_job(self, job_id: int) -> bool:
        """取消任务"""
        from novels.models import AudioJob

        try:
            job = AudioJob.objects.get(id=job_id)
            if job.status in ('completed', 'failed', 'cancelled'):
                return False

            job.status = 'cancelled'
            job.save()
            return True
        except AudioJob.DoesNotExist:
            return False

    def cleanup_job_files(self, job_id: int) -> Dict[str, Any]:
        """清理任务生成的临时文件"""
        from novels.models import AudioJob

        try:
            job = AudioJob.objects.get(id=job_id)
        except AudioJob.DoesNotExist:
            return {'success': False, 'error': '任务不存在'}

        media_dir = settings.MEDIA_ROOT / 'audiobooks' / f'job_{job_id}'
        deleted_files = 0
        deleted_dirs = 0

        if media_dir.exists():
            for file_path in media_dir.rglob('*'):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_files += 1

            media_dir.rmdir()
            deleted_dirs += 1

        return {
            'success': True,
            'deleted_files': deleted_files,
            'deleted_dirs': deleted_dirs
        }

    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """获取任务状态"""
        from novels.models import AudioJob

        try:
            job = AudioJob.objects.select_related('novel').get(id=job_id)
            return {
                'id': job.id,
                'novel_title': job.novel.title,
                'status': job.status,
                'status_display': job.get_status_display(),
                'progress': job.progress,
                'current_step': job.current_step,
                'output_path': job.output_path,
                'error_message': job.error_message,
                'total_scenes': job.total_scenes,
                'completed_scenes': job.completed_scenes,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            }
        except AudioJob.DoesNotExist:
            return None

    def estimate_duration(self, novel) -> Dict[str, int]:
        """估算音频总时长（秒）"""
        from novels.models import Scene

        total_chars = 0
        scene_count = 0

        for scene in Scene.objects.filter(novel=novel):
            scene_count += 1
            for dialogue in scene.dialogues.all():
                total_chars += len(dialogue.text)
            if scene.narration_text:
                total_chars += len(scene.narration_text)

        avg_chars_per_second = 5
        estimated_seconds = total_chars // avg_chars_per_second

        return {
            'total_characters': total_chars,
            'scene_count': scene_count,
            'estimated_seconds': estimated_seconds,
            'estimated_formatted': f"{estimated_seconds // 60}分{estimated_seconds % 60}秒"
        }
