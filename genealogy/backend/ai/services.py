"""
AI Service - OpenAI/Claude Integration for Genealogy
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class AIResponse:
    """AI响应数据结构"""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None


class AIService:
    """AI服务基类"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('AI_API_KEY')
        self.model = None
        self.max_tokens = 1000
        self.temperature = 0.7
    
    async def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        """生成文本"""
        raise NotImplementedError
    
    def generate_sync(self, prompt: str, system_prompt: str = "") -> AIResponse:
        """同步生成文本"""
        raise NotImplementedError


class OpenAIService(AIService):
    """OpenAI GPT 服务"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        super().__init__(api_key)
        self.model = model
        self.api_base = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    def generate_sync(self, prompt: str, system_prompt: str = "") -> AIResponse:
        """同步调用 OpenAI API"""
        if not self.api_key:
            logger.warning("OpenAI API key not configured, using mock response")
            return MockAIService().generate_sync(prompt, system_prompt)
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            return AIResponse(
                success=True,
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=self.model,
            )
        except ImportError:
            logger.warning("OpenAI package not installed, using mock response")
            return MockAIService().generate_sync(prompt, system_prompt)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return AIResponse(success=False, error=str(e))


class AnthropicService(AIService):
    """Anthropic Claude 服务"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key)
        self.model = model
        self.api_base = os.environ.get('ANTHROPIC_API_BASE', 'https://api.anthropic.com/v1')
    
    def generate_sync(self, prompt: str, system_prompt: str = "") -> AIResponse:
        """同步调用 Anthropic API"""
        if not self.api_key:
            logger.warning("Anthropic API key not configured, using mock response")
            return MockAIService().generate_sync(prompt, system_prompt)
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt if system_prompt else None,
                messages=[{"role": "user", "content": prompt}],
            )
            
            return AIResponse(
                success=True,
                content=response.content[0].text,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                model=self.model,
            )
        except ImportError:
            logger.warning("Anthropic package not installed, using mock response")
            return MockAIService().generate_sync(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return AIResponse(success=False, error=str(e))


class MockAIService(AIService):
    """Mock AI 服务 (用于测试)"""
    
    def __init__(self):
        super().__init__()
        self.model = "mock"
    
    def generate_sync(self, prompt: str, system_prompt: str = "") -> AIResponse:
        """返回模拟响应"""
        # 根据 prompt 类型返回不同的模拟内容
        if "简介" in prompt or "bio" in prompt.lower():
            content = "这位家族成员是一位勤劳朴实的人，为家族的发展做出了重要贡献。"
        elif "关系" in prompt or "recommend" in prompt.lower():
            content = json.dumps([
                {"type": "spouse", "name": "建议添加配偶关系"},
                {"type": "child", "name": "建议添加子女关系"},
            ])
        elif "分析" in prompt or "analysis" in prompt.lower():
            content = json.dumps({
                "total_members": 50,
                "generations": 5,
                "oldest_member": "张三",
                "youngest_member": "李四",
                "insights": ["家族主要分布在北方地区", "有较强的文化传承"],
            })
        elif "建议" in prompt or "suggest" in prompt.lower():
            content = "建议：1. 完善家族历史记录 2. 添加更多历史照片 3. 记录家族传统"
        else:
            content = "感谢您使用AI家谱助手！请问还有什么可以帮助您的？"
        
        return AIResponse(
            success=True,
            content=content,
            model="mock",
        )


def get_ai_service(provider: str = None) -> AIService:
    """获取AI服务实例"""
    provider = provider or os.environ.get('AI_PROVIDER', 'mock')
    
    if provider == AIProvider.OPENAI.value:
        return OpenAIService()
    elif provider == AIProvider.ANTHROPIC.value:
        return AnthropicService()
    else:
        return MockAIService()


# 全局 AI 服务实例
_ai_service: Optional[AIService] = None


def get_default_ai_service() -> AIService:
    """获取默认AI服务"""
    global _ai_service
    if _ai_service is None:
        _ai_service = get_ai_service()
    return _ai_service


def set_ai_service(service: AIService):
    """设置全局AI服务"""
    global _ai_service
    _ai_service = service
