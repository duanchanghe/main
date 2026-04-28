"""
AI Services Package
提供 DeepSeek 小说分析和 MiniMax 语音/音乐生成服务
"""

from .deepseek_extractor import DeepSeekNovelAnalyzer, analyze_novel_content
from .minimax_tts import MiniMaxTTS, MiniMaxTTSManager, text_to_speech
from .minimax_music import MiniMaxMusic, MiniMaxMusicLibrary, generate_music, generate_scene_bgm
from .audio_producer import AIAudioProducer

__all__ = [
    'DeepSeekNovelAnalyzer',
    'analyze_novel_content',
    'MiniMaxTTS',
    'MiniMaxTTSManager',
    'text_to_speech',
    'MiniMaxMusic',
    'MiniMaxMusicLibrary',
    'generate_music',
    'generate_scene_bgm',
    'AIAudioProducer',
]
