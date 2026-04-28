"""
精品有声书制作服务
支持按章节生成音频，资源存储到 MinIO
高品质音频处理
"""
import os
import re
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from functools import wraps
from django.conf import settings
from django.db import transaction

from services.deepseek_extractor import DeepSeekNovelAnalyzer
from services.minimax_tts import MiniMaxTTSManager
from services.minimax_music import MiniMaxMusicLibrary
from services.storage import storage, MinIOStorageError

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 重试次数耗尽: {e}")

            raise last_exception
        return wrapper
    return decorator


class AudioBookError(Exception):
    """有声书制作异常"""
    pass


class ChapterAudio:
    """章节音频片段"""

    def __init__(
        self,
        chapter_number: int,
        title: str = '',
        scenes: List[Dict] = None,
        total_duration: int = 0
    ):
        self.chapter_number = chapter_number
        self.title = title
        self.scenes = scenes or []
        self.total_duration = total_duration
        self.output_path = ''
        self.minio_path = ''
        self.status = 'pending'
        self.error_message = ''
        self.quality_score = 0
        self.error_count = 0

    def to_dict(self) -> Dict:
        return {
            'chapter_number': self.chapter_number,
            'title': self.title,
            'scenes_count': len(self.scenes),
            'total_duration': self.total_duration,
            'output_path': self.output_path,
            'minio_path': self.minio_path,
            'status': self.status,
            'error_message': self.error_message,
            'quality_score': self.quality_score
        }


class AudioQualityChecker:
    """音频质量检查器"""

    @staticmethod
    def check_audio_quality(audio_path: str) -> Dict[str, Any]:
        """
        检查音频质量

        Returns:
            {
                'valid': bool,
                'duration_ms': int,
                'sample_rate': int,
                'channels': int,
                'bitrate': str,
                'issues': []
            }
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(audio_path)

            issues = []

            duration_sec = len(audio) / 1000
            if duration_sec < 1:
                issues.append('音频时长过短')

            if audio.frame_rate < 22050:
                issues.append('采样率过低')

            if audio.channels not in [1, 2]:
                issues.append('声道数异常')

            dbfs = audio.dBFS
            if dbfs < -40:
                issues.append('音量过小')
            elif dbfs > -3:
                issues.append('音量过大可能失真')

            return {
                'valid': len(issues) == 0,
                'duration_ms': len(audio),
                'duration_sec': duration_sec,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'dbfs': round(dbfs, 2),
                'issues': issues
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'issues': ['无法读取音频文件']
            }

    @staticmethod
    def normalize_audio(audio: 'AudioSegment', target_dbfs: float = -20.0) -> 'AudioSegment':
        """音频音量标准化"""
        change_in_dbfs = target_dbfs - audio.dBFS
        return audio.apply_gain(change_in_dbfs)

    @staticmethod
    def apply_fade(audio: 'AudioSegment', fade_in_ms: int = 500, fade_out_ms: int = 1000) -> 'AudioSegment':
        """应用淡入淡出"""
        duration = len(audio)
        fade_in = min(fade_in_ms, duration // 4)
        fade_out = min(fade_out_ms, duration // 4)
        return audio.fade_in(fade_in).fade_out(fade_out)


class AudioBookProducer:
    """精品有声书制作器"""

    BUCKET_AUDIOBOOKS = 'audiobooks'
    BUCKET_CHAPTERS = 'chapters'
    BUCKET_SFX = 'sfx'
    BUCKET_BGM = 'bgm'

    TTS_QUALITY_SETTINGS = {
        'high': {
            'model': 'speech-02-hd',
            'sample_rate': 32000,
            'speed': 0.95,
        },
        'standard': {
            'model': 'speech-02',
            'sample_rate': 16000,
            'speed': 1.0,
        }
    }

    def __init__(self, quality: str = 'high'):
        self.deepseek = DeepSeekNovelAnalyzer()
        self.tts = MiniMaxTTSManager()
        self.music = MiniMaxMusicLibrary()
        self.quality = quality
        self._sfx_cache = {}
        self._bgm_cache = {}
        self._tts = None

    @property
    def tts_service(self):
        """获取 TTS 服务实例"""
        if self._tts is None:
            from services.minimax_tts import MiniMaxTTS
            self._tts = MiniMaxTTS()
        return self._tts

    def upload_to_minio(self, local_path: str, bucket: str, object_name: str) -> Dict[str, Any]:
        """上传文件到 MinIO"""
        try:
            result = storage.upload_file(
                file_path=local_path,
                object_name=object_name,
                bucket_name=bucket,
                content_type='audio/mpeg',
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'service': 'audiobook_producer',
                    'quality': self.quality
                }
            )
            return result
        except MinIOStorageError as e:
            logger.error(f"上传到MinIO失败: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_novel(self, content: str, max_chars: int = 15000) -> Dict[str, Any]:
        """分析小说文本"""
        return self.deepseek.analyze_novel(content, max_chars)

    def save_analysis(self, novel, analysis_result: Dict) -> Dict[str, Any]:
        """保存分析结果到数据库 - 使用事务保证数据一致性"""
        from novels.models import Novel, Character, Scene, Dialogue

        with transaction.atomic():
            novel.ai_analysis = analysis_result
            novel.genre = analysis_result.get('novel_info', {}).get('genre', 'other')
            novel.setting = analysis_result.get('novel_info', {}).get('setting', '')
            novel.analysis_completed_at = datetime.now()
            novel.save()

            # 删除旧数据
            novel.characters.all().delete()
            novel.scenes.all().delete()

            char_map = {}
            for char_data in analysis_result.get('characters', []):
                char = Character.objects.create(
                    novel=novel,
                    name=char_data['name'],
                    role_type=char_data.get('role_type', 'supporting'),
                    gender=char_data.get('gender', 'unknown'),
                    age=char_data.get('age', 'unknown'),
                    voice_id=char_data.get('voice_id', 'Chinese_Male_Neutral'),
                    importance_score=char_data.get('importance_score', 50),
                    personality=char_data.get('personality', ''),
                    speaking_style=char_data.get('speaking_style', ''),
                    temperament=char_data.get('temperament', ''),
                    catchphrase=char_data.get('catchphrase', ''),
                )
                char_map[char_data['name']] = char

            chapter_summaries = []
            for chapter_data in analysis_result.get('chapters', []):
                chapter_num = chapter_data.get('chapter_number', 1)
                chapter_title = chapter_data.get('title', f'第{chapter_num}章')
                chapter_summaries.append({
                    'chapter_number': chapter_num,
                    'title': chapter_title,
                    'summary': chapter_data.get('summary', ''),
                    'scenes_count': len(chapter_data.get('scene_changes', []))
                })

                for scene_data in chapter_data.get('scene_changes', []):
                    bgm_data = scene_data.get('bgm', {})
                    ambient_data = scene_data.get('ambient_sound', {})

                    scene = Scene.objects.create(
                        novel=novel,
                        chapter_number=chapter_num,
                        scene_id=scene_data.get('scene_id', 1),
                        location=scene_data.get('location', ''),
                        time_of_day=scene_data.get('time_of_day', ''),
                        season=scene_data.get('season', ''),
                        weather=scene_data.get('weather', ''),
                        atmosphere=scene_data.get('atmosphere', ''),
                        mood=scene_data.get('mood', 'calm'),
                        suggested_bgm=self._extract_bgm(scene_data),
                        suggested_sfx=self._extract_sfx(scene_data),
                        bgm_volume=bgm_data.get('volume', 0.3) if isinstance(bgm_data, dict) else 0.3,
                        sfx_volume=scene_data.get('sfx_volume', 0.5),
                        narration_text=scene_data.get('narration', ''),
                    )

                    for dialogue_data in scene_data.get('dialogues', []):
                        char_name = dialogue_data.get('character', '')
                        if char_name in char_map:
                            sfx_data = dialogue_data.get('sfx', {})
                            sfx_params = {}
                            if isinstance(sfx_data, dict):
                                sfx_params = {
                                    'type': sfx_data.get('type', []),
                                    'timing': sfx_data.get('timing', 'during'),
                                    'position_ms': sfx_data.get('position_ms', 0),
                                    'duration': sfx_data.get('duration', 1000),
                                    'volume': sfx_data.get('volume', 0.3),
                                }

                            Dialogue.objects.create(
                                scene=scene,
                                character=char_map[char_name],
                                text=dialogue_data.get('text', ''),
                                emotion=dialogue_data.get('emotion', 'neutral'),
                                volume=dialogue_data.get('volume', 'normal'),
                                speed=dialogue_data.get('speed', 'normal'),
                                special_effects=dialogue_data.get('sfx', {}).get('description', '') if isinstance(dialogue_data.get('sfx'), dict) else '',
                                sfx_timing=sfx_params,
                                order=dialogue_data.get('id', 0),
                            )

        return {
            'characters_count': len(char_map),
            'scenes_count': Scene.objects.filter(novel=novel).count(),
            'chapters': chapter_summaries
        }

    def _extract_bgm(self, scene_data: Dict) -> str:
        """提取 BGM 描述"""
        bgm = scene_data.get('bgm', {})
        if isinstance(bgm, dict):
            style = bgm.get('style', '')
            instruments = bgm.get('instruments', '')
            description = bgm.get('description', '')
            parts = [p for p in [style, instruments, description] if p]
            return '，'.join(parts) if parts else ''
        return scene_data.get('suggested_bgm', '')

    def _extract_sfx(self, scene_data: Dict) -> List[str]:
        """提取音效列表"""
        sfx_list = list(scene_data.get('suggested_sfx', []))

        for event in scene_data.get('sfx_events', []):
            sfx_type = event.get('type', '')
            if sfx_type and sfx_type not in sfx_list:
                sfx_list.append(sfx_type)

        ambient = scene_data.get('ambient_sound', {})
        if isinstance(ambient, dict) and ambient.get('description'):
            desc = ambient['description']
            sfx_keywords = {
                '雨': '雨声', '雷': '雷声', '风': '风声', '鸟': '鸟鸣声',
                '海': '海浪声', '水': '流水声', '虫': '虫鸣声', '钟': '钟声'
            }
            for kw, sfx in sfx_keywords.items():
                if kw in desc and sfx not in sfx_list:
                    sfx_list.append(sfx)

        return sfx_list[:8]

    def generate_chapter_audio(
        self,
        novel,
        chapter_number: int,
        output_dir: str,
        use_multi_voice: bool = True,
        use_bgm: bool = True,
        use_sfx: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> ChapterAudio:
        """生成单个章节的音频 - 增强错误处理"""
        from novels.models import Scene
        from pydub import AudioSegment

        chapter_audio = ChapterAudio(chapter_number=chapter_number)

        scenes = Scene.objects.filter(
            novel=novel,
            chapter_number=chapter_number
        ).order_by('scene_id')

        if not scenes.exists():
            chapter_audio.status = 'failed'
            chapter_audio.error_message = f'章节 {chapter_number} 不存在'
            return chapter_audio

        chapter_audio.title = f'第{chapter_number}章'
        chapter_audio.scenes = [
            {'scene_id': s.scene_id, 'location': s.location, 'mood': s.mood}
            for s in scenes
        ]

        analysis = novel.ai_analysis or {}
        chapter_analysis = self._get_chapter_analysis(analysis, chapter_number)

        total_scenes = scenes.count()
        scene_audio_files = []
        quality_scores = []

        for idx, scene in enumerate(scenes):
            try:
                scene_analysis = self._get_scene_analysis(chapter_analysis, scene.scene_id)

                scene_result = self._generate_single_scene(
                    scene=scene,
                    scene_analysis=scene_analysis,
                    output_dir=output_dir,
                    use_multi_voice=use_multi_voice,
                    use_bgm=use_bgm,
                    use_sfx=use_sfx
                )

                if scene_result.get('success'):
                    scene_audio_files.append(scene_result['path'])
                    chapter_audio.total_duration += scene_result.get('duration', 0)
                    if 'quality_score' in scene_result:
                        quality_scores.append(scene_result['quality_score'])
                else:
                    logger.error(f"场景 {scene.scene_id} 生成失败: {scene_result.get('error')}")
                    chapter_audio.error_count += 1

                if progress_callback:
                    progress = int((idx + 1) / total_scenes * 100)
                    progress_callback(progress, f'场景 {idx + 1}/{total_scenes}')

            except Exception as e:
                logger.exception(f"场景 {scene.scene_id} 处理异常")
                chapter_audio.error_count += 1
                if progress_callback:
                    progress = int((idx + 1) / total_scenes * 100)
                    progress_callback(progress, f'场景 {idx + 1}/{total_scenes} (失败)')

        if scene_audio_files:
            try:
                output_path = os.path.join(output_dir, f'chapter_{chapter_number}.mp3')
                self._merge_audio_files(scene_audio_files, output_path)

                quality_result = self._post_process_audio(output_path)
                if quality_result:
                    chapter_audio.quality_score = quality_result.get('score', 80)

                chapter_audio.output_path = output_path

                # 上传到 MinIO (带重试)
                minio_result = self._upload_with_retry(
                    local_path=output_path,
                    bucket=self.BUCKET_CHAPTERS,
                    object_name=f'{novel.id}/chapter_{chapter_number}.mp3'
                )

                if minio_result.get('success'):
                    chapter_audio.minio_path = minio_result['path']
                    chapter_audio.status = 'completed'
                else:
                    chapter_audio.status = 'completed_local'
                    chapter_audio.error_message = f'MinIO上传失败: {minio_result.get("error")}'

            except Exception as e:
                logger.exception("章节音频合并/处理失败")
                chapter_audio.status = 'failed'
                chapter_audio.error_message = str(e)
        else:
            chapter_audio.status = 'failed'
            chapter_audio.error_message = '没有生成任何场景音频'

        return chapter_audio

    def _upload_with_retry(self, local_path: str, bucket: str, object_name: str, max_retries: int = 3) -> Dict:
        """带重试的 MinIO 上传"""
        for attempt in range(max_retries):
            try:
                return self.upload_to_minio(local_path, bucket, object_name)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"MinIO 上传失败 (尝试 {attempt + 1}/{max_retries}): {e}, {wait_time}秒后重试")
                    time.sleep(wait_time)
                else:
                    return {'success': False, 'error': str(e)}
        return {'success': False, 'error': '重试次数耗尽'}

    def generate_full_audiobook(
        self,
        novel,
        output_dir: str,
        use_multi_voice: bool = True,
        use_bgm: bool = True,
        use_sfx: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """生成完整有声书 - 增强错误处理"""
        analysis = novel.ai_analysis or {}
        chapters_data = analysis.get('chapters', [])

        if not chapters_data:
            chapters_data = [{'chapter_number': i + 1} for i in range(10)]

        total_chapters = len(chapters_data)
        all_chapter_paths = []
        failed_chapters = []
        total_quality = 0
        quality_count = 0

        for idx, chapter_data in enumerate(chapters_data):
            chapter_num = chapter_data.get('chapter_number', idx + 1)

            chapter_dir = os.path.join(output_dir, f'chapter_{chapter_num}')
            os.makedirs(chapter_dir, exist_ok=True)

            def make_callback(base_idx, base_chapter):
                def cb(progress, step):
                    if progress_callback:
                        progress_callback(
                            int((base_idx + progress / 100) / total_chapters * 100),
                            f'第{base_chapter}章 {step}'
                        )
                return cb

            try:
                chapter_audio = self.generate_chapter_audio(
                    novel=novel,
                    chapter_number=chapter_num,
                    output_dir=chapter_dir,
                    use_multi_voice=use_multi_voice,
                    use_bgm=use_bgm,
                    use_sfx=use_sfx,
                    progress_callback=make_callback(idx, chapter_num)
                )

                if chapter_audio.output_path:
                    all_chapter_paths.append(chapter_audio.output_path)
                    total_quality += chapter_audio.quality_score
                    quality_count += 1
                else:
                    failed_chapters.append(chapter_num)
                    logger.error(f"章节 {chapter_num} 生成失败: {chapter_audio.error_message}")

                if progress_callback:
                    progress_callback(int((idx + 1) / total_chapters * 100), f'完成第{chapter_num}章')

            except Exception as e:
                logger.exception(f"章节 {chapter_num} 处理异常")
                failed_chapters.append(chapter_num)

        if not all_chapter_paths:
            raise AudioBookError(f"所有章节生成失败: {failed_chapters}")

        full_output = os.path.join(output_dir, 'full_audiobook.mp3')
        self._merge_audio_files(all_chapter_paths, full_output, add_silence=300)

        avg_quality = total_quality / quality_count if quality_count > 0 else 0

        minio_result = self._upload_with_retry(
            local_path=full_output,
            bucket=self.BUCKET_AUDIOBOOKS,
            object_name=f'{novel.id}/full_audiobook.mp3'
        )

        return {
            'success': True,
            'full_audiobook_path': full_output,
            'full_audiobook_minio': minio_result.get('path', ''),
            'chapters_count': total_chapters,
            'completed_chapters': len(all_chapter_paths),
            'failed_chapters': failed_chapters,
            'avg_quality_score': round(avg_quality, 1)
        }

    def _generate_single_scene(
        self,
        scene,
        scene_analysis: Dict,
        output_dir: str,
        use_multi_voice: bool,
        use_bgm: bool,
        use_sfx: bool
    ) -> Dict[str, Any]:
        """生成单个场景的音频"""
        from pydub import AudioSegment

        try:
            os.makedirs(output_dir, exist_ok=True)

            dialogues = scene.dialogues.all().order_by('order')
            scene_audio = AudioSegment.silent(duration=0)
            bgm_audio = None

            if use_bgm:
                bgm_audio = self._generate_scene_bgm(scene, scene_analysis)

            for dialogue in dialogues:
                char_name = dialogue.character.name if use_multi_voice else 'narrator'

                audio_path = self._synthesize_dialogue(
                    dialogue=dialogue,
                    character_name=char_name,
                    output_dir=output_dir
                )

                dialogue.audio_path = audio_path
                dialogue.save()

                dialogue_audio = AudioSegment.from_mp3(audio_path)

                dialogue_audio = self._apply_dialogue_processing(dialogue_audio, dialogue)

                if use_sfx:
                    dialogue_audio = self._add_dialogue_sfx(dialogue, dialogue_audio, scene_analysis)

                if bgm_audio:
                    dialogue_audio = self._mix_with_bgm(dialogue_audio, bgm_audio, scene)

                scene_audio = scene_audio + dialogue_audio

            if scene.narration_text and not dialogues.exists():
                audio_path = self._synthesize_narration(scene.narration_text, output_dir)
                narration_audio = AudioSegment.from_mp3(audio_path)
                narration_audio = self._apply_dialogue_processing(narration_audio, None)

                if bgm_audio:
                    narration_audio = self._mix_with_bgm(narration_audio, bgm_audio, scene)

                scene_audio = narration_audio

            scene_file = os.path.join(output_dir, 'scene_audio.mp3')

            quality_score = self._calculate_quality_score(scene_audio)
            scene_audio.export(scene_file, format='mp3', bitrate='192k')

            return {
                'success': True,
                'path': scene_file,
                'duration': len(scene_audio),
                'quality_score': quality_score
            }

        except Exception as e:
            logger.error(f"场景生成失败: {e}")
            return {'success': False, 'error': str(e)}

    def _synthesize_dialogue(self, dialogue, character_name: str, output_dir: str) -> str:
        """高质量语音合成"""
        emotion = dialogue.emotion or 'neutral'
        speed = self._get_speed_value(dialogue.speed)
        pitch = self._get_pitch_adjustment(emotion)

        output_path = os.path.join(output_dir, f'dialogue_{dialogue.id}.mp3')

        self.tts_service.text_to_speech(
            text=dialogue.text,
            voice_id=dialogue.character.voice_id,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            volume=1.0,
            output_path=output_path
        )

        return output_path

    def _synthesize_narration(self, text: str, output_dir: str) -> str:
        """旁白语音合成"""
        output_path = os.path.join(output_dir, 'narration.mp3')

        self.tts_service.text_to_speech(
            text=text,
            voice_id='Chinese_Male_Neutral',
            emotion='neutral',
            speed=0.95,
            pitch=0,
            volume=1.0,
            output_path=output_path
        )

        return output_path

    def _get_speed_value(self, speed: str) -> float:
        """获取语速值"""
        speed_map = {
            'slow': 0.85,
            'normal': 1.0,
            'fast': 1.15
        }
        return speed_map.get(speed, 1.0)

    def _get_pitch_adjustment(self, emotion: str) -> float:
        """根据情感调整音调"""
        pitch_map = {
            'happy': 50,
            'sad': -100,
            'angry': 100,
            'fearful': 200,
            'surprised': 150,
            'excited': 150,
            'romantic': -50,
            'tense': 100,
        }
        return pitch_map.get(emotion, 0)

    def _apply_dialogue_processing(self, audio: 'AudioSegment', dialogue) -> 'AudioSegment':
        """对话音频后处理"""
        audio = AudioQualityChecker.normalize_audio(audio, target_dbfs=-18.0)

        if dialogue:
            volume_map = {'loud': 1.2, 'normal': 1.0, 'whisper': 0.5, 'calling': 1.3}
            vol_mult = volume_map.get(dialogue.volume, 1.0)
            audio = audio.apply_gain(20 * (vol_mult - 1))

        return audio

    def _add_dialogue_sfx(self, dialogue, audio: 'AudioSegment', scene_analysis: Dict) -> 'AudioSegment':
        """为对话添加音效"""
        text = getattr(dialogue, 'text', '') or ''
        sfx_timing = getattr(dialogue, 'sfx_timing', None) or {}

        sfx_keywords = {
            '笑': {'name': '笑声', 'position': 0.3, 'volume': 0.2},
            '哈哈': {'name': '笑声', 'position': 0.3, 'volume': 0.25},
            '哭': {'name': '哭泣声', 'position': 0.5, 'volume': 0.3},
            '雨': {'name': '雨声', 'position': 0.0, 'volume': 0.15},
            '雷': {'name': '雷声', 'position': 0.0, 'volume': 0.2},
            '门': {'name': '开门声', 'position': 0.8, 'volume': 0.25},
            '敲': {'name': '敲门声', 'position': 0.8, 'volume': 0.3},
            '心跳': {'name': '心跳声', 'position': 0.3, 'volume': 0.15},
            '叹息': {'name': '叹息声', 'position': 0.5, 'volume': 0.2},
        }

        for kw, config in sfx_keywords.items():
            if kw in text:
                sfx_audio = self._get_sfx_audio(config['name'], 1500)
                if sfx_audio:
                    pos = int(len(audio) * config['position'])
                    vol = config['volume']
                    sfx_adjusted = sfx_audio.apply_gain(-20 + 20 * vol)
                    audio = audio.overlay(sfx_adjusted, position=pos)

        return audio

    def _generate_scene_bgm(self, scene, scene_analysis: Dict) -> Optional['AudioSegment']:
        """生成场景 BGM"""
        from pydub import AudioSegment

        mood = scene.mood or 'calm'
        suggested_bgm = scene.suggested_bgm or ''

        cache_key = f"{mood}_{suggested_bgm[:20]}"
        if cache_key in self._bgm_cache:
            bgm_path = self._bgm_cache[cache_key]
            if os.path.exists(bgm_path):
                return AudioSegment.from_mp3(bgm_path)

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

        preset = mood_to_preset.get(mood, 'peaceful_nature')

        if suggested_bgm:
            result = self.music.generate_music(prompt=suggested_bgm, duration=120)
        else:
            result = self.music.get_preset_bgm(preset)

        if result.get('success') and result.get('audio_file_path'):
            bgm_path = result['audio_file_path']
            self._bgm_cache[cache_key] = bgm_path
            return AudioSegment.from_mp3(bgm_path)

        return None

    def _mix_with_bgm(self, audio: 'AudioSegment', bgm: 'AudioSegment', scene) -> 'AudioSegment':
        """混合对话音频和 BGM"""
        bgm_copy = bgm[:len(audio)]

        bgm_volume = scene.bgm_volume if hasattr(scene, 'bgm_volume') else 0.3
        volume_reduction = -20 + 20 * bgm_volume
        bgm_copy = bgm_copy.apply_gain(volume_reduction)

        return audio.overlay(bgm_copy)

    def _get_sfx_audio(self, sfx_name: str, duration_ms: int) -> Optional['AudioSegment']:
        """获取音效音频"""
        from pydub import AudioSegment

        if sfx_name in self._sfx_cache:
            sfx_path = self._sfx_cache[sfx_name]
            if os.path.exists(sfx_path):
                sfx = AudioSegment.from_mp3(sfx_path)
                return sfx[:duration_ms]

        presets = {
            '笑声': '笑声，愉快的笑声，温馨场景',
            '哭泣声': '哭泣声，悲伤抽泣',
            '雨声': '雨声，细雨淅沥，自然环境',
            '雷声': '雷声，远处轰隆，暴风雨',
            '风声': '风声，自然环境微风轻拂',
            '心跳声': '心跳声，紧张加速的心跳',
            '叹息声': '叹息声，深沉叹息',
            '开门声': '开门声，木门吱呀打开',
            '敲门声': '敲门声，礼貌敲门三下',
            '海浪声': '海浪声，波涛汹涌',
            '鸟鸣声': '鸟鸣声，清晨森林鸟叫',
            '流水声': '流水声，小溪潺潺',
            '钟声': '古钟敲击声，悠远回荡',
            '马蹄声': '马蹄声，奔跑中的马',
            '剑击声': '剑击声，金属碰撞',
        }

        prompt = presets.get(sfx_name)
        if not prompt:
            return None

        try:
            result = self.music.generate_music(
                prompt=prompt,
                duration=duration_ms // 1000 + 2
            )
            if result.get('success') and result.get('audio_file_path'):
                self._sfx_cache[sfx_name] = result['audio_file_path']
                sfx = AudioSegment.from_mp3(result['audio_file_path'])
                return sfx[:duration_ms]
        except Exception as e:
            logger.error(f"生成音效失败 {sfx_name}: {e}")

        return None

    def _post_process_audio(self, audio_path: str) -> Optional[Dict]:
        """音频后处理"""
        from pydub import AudioSegment

        try:
            audio = AudioSegment.from_mp3(audio_path)

            audio = AudioQualityChecker.normalize_audio(audio, target_dbfs=-16.0)

            audio = AudioQualityChecker.apply_fade(audio, fade_in_ms=500, fade_out_ms=1500)

            audio.export(audio_path, format='mp3', bitrate='192k')

            quality_result = AudioQualityChecker.check_audio_quality(audio_path)

            return {
                'success': True,
                'score': self._calculate_quality_score(audio),
                'details': quality_result
            }
        except Exception as e:
            logger.error(f"音频后处理失败: {e}")
            return None

    def _calculate_quality_score(self, audio: 'AudioSegment') -> int:
        """计算音频质量评分"""
        score = 100

        if audio.dBFS > -3:
            score -= 20
        elif audio.dBFS < -35:
            score -= 15
        elif audio.dBFS < -25 or audio.dBFS > -10:
            score -= 5

        if audio.frame_rate < 22050:
            score -= 30
        elif audio.frame_rate >= 32000:
            score += 5

        return max(0, min(100, score))

    def _merge_audio_files(
        self,
        file_paths: List[str],
        output_path: str,
        add_silence: int = 500
    ):
        """合并多个音频文件"""
        from pydub import AudioSegment

        combined = AudioSegment.silent(duration=0)

        for path in file_paths:
            if os.path.exists(path):
                audio = AudioSegment.from_mp3(path)
                audio = AudioQualityChecker.normalize_audio(audio, target_dbfs=-18.0)
                combined = combined + audio + AudioSegment.silent(duration=add_silence)

        silence = AudioSegment.silent(duration=300)
        combined = silence + combined + AudioSegment.silent(duration=500)

        combined.export(output_path, format='mp3', bitrate='192k')
        logger.info(f"音频合并完成: {output_path}")

    def _get_chapter_analysis(self, analysis: Dict, chapter_number: int) -> Dict:
        """获取章节分析数据"""
        for chapter in analysis.get('chapters', []):
            if chapter.get('chapter_number') == chapter_number:
                return chapter
        return {}

    def _get_scene_analysis(self, chapter_analysis: Dict, scene_id: int) -> Dict:
        """获取场景分析数据"""
        for scene in chapter_analysis.get('scene_changes', []):
            if scene.get('scene_id') == scene_id:
                return scene
        return {}

    def _get_chapter_summary(self, novel, chapter_number: int) -> ChapterAudio:
        """获取章节摘要"""
        from novels.models import Scene

        scenes = Scene.objects.filter(novel=novel, chapter_number=chapter_number)
        return ChapterAudio(
            chapter_number=chapter_number,
            title=f'第{chapter_number}章',
            scenes=[{'scene_id': s.scene_id} for s in scenes],
            total_duration=0,
            status='ready'
        )


def get_audiobook_producer(quality: str = 'high') -> AudioBookProducer:
    """获取有声书制作器实例"""
    return AudioBookProducer(quality=quality)
