"""
MiniMax TTS 语音合成服务
使用 MiniMax API 进行语音合成，支持多角色配音
高品质音频参数配置
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class MiniMaxTTS:
    """MiniMax 语音合成器 - 高品质配置"""

    BASE_URL = "https://api.minimax.io/v1"

    VOICE_OPTIONS = {
        "Chinese_Male_Neutral": "标准中文男声（旁白）",
        "Chinese_Female_Neutral": "标准中文女声",
        "male-qn-qingse": "磁性男声（年轻男性）",
        "female-tianmei": "甜美女声（年轻女性）",
        "male-yuanfang": "成熟男声（中年男性）",
        "female-shaoyu": "淑女声（温柔女性）",
        "male-bada": "大叔声（粗犷男性）",
        "male-tiancheng": "天成男声（清澈有力）",
        "female-yunyang": "云扬女声（活泼可爱）",
    }

    EMOTION_OPTIONS = [
        "neutral", "happy", "sad", "angry", "fearful",
        "surprised", "tense", "excited", "romantic", "mysterious"
    ]

    EMOTION_PITCH_ADJUSTMENTS = {
        'neutral': 0,
        'happy': 50,
        'sad': -100,
        'angry': 100,
        'fearful': 200,
        'surprised': 150,
        'tense': 100,
        'excited': 150,
        'romantic': -50,
        'mysterious': -50,
    }

    EMOTION_SPEED_ADJUSTMENTS = {
        'neutral': 1.0,
        'happy': 1.1,
        'sad': 0.85,
        'angry': 1.15,
        'fearful': 1.1,
        'surprised': 1.05,
        'tense': 1.05,
        'excited': 1.15,
        'romantic': 0.95,
        'mysterious': 0.9,
    }

    def __init__(self):
        api_key = os.getenv('MINIMAX_API_KEY')
        group_id = os.getenv('MINIMAX_GROUP_ID')

        if not api_key or not group_id:
            raise ValueError("MINIMAX_API_KEY 或 MINIMAX_GROUP_ID 环境变量未设置")

        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.group_id = group_id

    def text_to_speech(
        self,
        text: str,
        voice_id: str = "Chinese_Male_Neutral",
        emotion: str = "neutral",
        speed: float = 1.0,
        pitch: float = 0,
        volume: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        文本转语音 - 高品质参数

        Args:
            text: 要转换的文本
            voice_id: 音色ID
            emotion: 情感
            speed: 语速 (0.5-2.0)
            pitch: 音调 (-500到500)
            volume: 音量 (0.5-2.0)
            output_path: 输出文件路径

        Returns:
            生成的音频文件路径
        """
        try:
            response = self.client.audio.speech.create(
                model="speech-02-hd",
                voice=voice_id,
                input=text,
                response_format="mp3",
                speed=speed,
                pitch=pitch,
                volume=volume,
                emotion=emotion
            )

            if not output_path:
                output_path = "/tmp/tts_output.mp3"

            os.makedirs(os.path.dirname(output_path) or '/tmp', exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

        except Exception as e:
            print(f"TTS 生成失败: {e}")
            raise

    def text_to_speech_with_emotion(
        self,
        text: str,
        voice_id: str,
        emotion: str = "neutral",
        output_path: Optional[str] = None
    ) -> str:
        """
        带情感参数的语音合成（自动调整音调和语速）

        Args:
            text: 要转换的文本
            voice_id: 音色ID
            emotion: 情感
            output_path: 输出文件路径

        Returns:
            生成的音频文件路径
        """
        pitch = self.EMOTION_PITCH_ADJUSTMENTS.get(emotion, 0)
        speed = self.EMOTION_SPEED_ADJUSTMENTS.get(emotion, 1.0)

        return self.text_to_speech(
            text=text,
            voice_id=voice_id,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            volume=1.0,
            output_path=output_path
        )

    async def text_to_speech_async(
        self,
        text: str,
        voice_id: str = "Chinese_Male_Neutral",
        emotion: str = "neutral",
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """异步版本"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.text_to_speech,
            text, voice_id, emotion, speed, 0, 1.0, output_path
        )

    def batch_text_to_speech(
        self,
        segments: List[Dict[str, Any]],
        output_dir: str = "/tmp/tts_segments"
    ) -> List[Dict[str, Any]]:
        """
        批量文本转语音
        
        Args:
            segments: 音频片段列表，每项包含:
                - text: 文本内容
                - voice_id: 音色ID
                - emotion: 情感
                - filename: 输出文件名
                
        Returns:
            生成结果列表，包含每个片段的音频路径
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, segment in enumerate(segments):
            try:
                output_path = os.path.join(output_dir, segment.get('filename', f'segment_{i}.mp3'))
                
                audio_path = self.text_to_speech(
                    text=segment.get('text', ''),
                    voice_id=segment.get('voice_id', 'Chinese_Male_Neutral'),
                    emotion=segment.get('emotion', 'neutral'),
                    speed=segment.get('speed', 1.0),
                    output_path=output_path
                )
                
                results.append({
                    'success': True,
                    'segment_id': i,
                    'audio_path': audio_path
                })
                
            except Exception as e:
                results.append({
                    'success': False,
                    'segment_id': i,
                    'error': str(e)
                })
        
        return results

    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的音色列表"""
        return self.VOICE_OPTIONS

    def suggest_voice_for_character(
        self,
        gender: str = "unknown",
        age: str = "unknown",
        personality: str = "",
        speaking_style: str = ""
    ) -> str:
        """
        根据角色特征推荐音色
        
        Args:
            gender: 性别（male/female/unknown）
            age: 年龄（young/middle-aged/elderly/unknown）
            personality: 性格描述
            speaking_style: 说话风格
            
        Returns:
            推荐的 voice_id
        """
        if gender == "female":
            if "温柔" in personality or "淑女" in personality:
                return "female-shaoyu"
            elif "活泼" in personality or "年轻" in age:
                return "female-tianmei"
            else:
                return "Chinese_Female_Neutral"
        elif gender == "male":
            if "磁性" in personality or "优雅" in personality:
                return "male-qn-qingse"
            elif "粗犷" in personality or "大叔" in personality or age == "middle-aged":
                return "male-bada"
            elif "成熟" in personality or "稳重" in personality:
                return "male-yuanfang"
            else:
                return "Chinese_Male_Neutral"
        else:
            return "Chinese_Male_Neutral"


class MiniMaxTTSManager:
    """MiniMax TTS 管理器，用于管理多角色配音"""

    def __init__(self):
        self.tts = MiniMaxTTS()
        self.character_voices = {}

    def register_character_voice(
        self,
        character_name: str,
        voice_id: str,
        emotion: str = "neutral"
    ):
        """注册角色音色"""
        self.character_voices[character_name] = {
            'voice_id': voice_id,
            'default_emotion': emotion
        }

    def get_voice_for_character(self, character_name: str) -> Dict[str, str]:
        """获取角色的音色配置"""
        return self.character_voices.get(character_name, {
            'voice_id': 'Chinese_Male_Neutral',
            'default_emotion': 'neutral'
        })

    def convert_dialogue(
        self,
        character: str,
        text: str,
        emotion: str = None,
        speed: float = 1.0,
        output_path: str = None
    ) -> str:
        """转换对话"""
        voice_config = self.get_voice_for_character(character)
        emotion = emotion or voice_config.get('default_emotion', 'neutral')
        
        return self.tts.text_to_speech(
            text=text,
            voice_id=voice_config['voice_id'],
            emotion=emotion,
            speed=speed,
            output_path=output_path
        )


def text_to_speech(
    text: str,
    voice_id: str = "Chinese_Male_Neutral",
    emotion: str = "neutral",
    output_path: str = None
) -> str:
    """
    便捷函数：文本转语音
    
    Args:
        text: 要转换的文本
        voice_id: 音色ID
        emotion: 情感
        output_path: 输出路径
        
    Returns:
        音频文件路径
    """
    tts = MiniMaxTTS()
    return tts.text_to_speech(text, voice_id, emotion, output_path=output_path)
