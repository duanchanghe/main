"""
OCR Service for Genealogy - Text Extraction from Images
"""
import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import base64
import json

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR 识别结果"""
    success: bool
    text: Optional[str] = None
    structured_data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    confidence: float = 0.0


class OCRService:
    """OCR 服务基类"""
    
    def extract_text(self, image_path: str) -> OCRResult:
        """从图片提取文本"""
        raise NotImplementedError
    
    def extract_text_base64(self, image_data: str) -> OCRResult:
        """从 Base64 图片数据提取文本"""
        raise NotImplementedError


class GoogleVisionOCR(OCRService):
    """Google Vision API OCR"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('GOOGLE_VISION_API_KEY')
        self.api_base = 'https://vision.googleapis.com/v1/images:annotate'
    
    def extract_text(self, image_path: str) -> OCRResult:
        """从图片文件提取文本"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            return self.extract_text_base64(image_data)
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            return OCRResult(success=False, error=str(e))
    
    def extract_text_base64(self, image_data: str) -> OCRResult:
        """从 Base64 数据提取文本"""
        if not self.api_key:
            logger.warning("Google Vision API key not configured")
            return OCRResult(success=False, error="OCR 服务未配置")
        
        try:
            import requests
            
            url = f"{self.api_base}?key={self.api_key}"
            payload = {
                "requests": [{
                    "image": {"content": image_data},
                    "features": [
                        {"type": "TEXT_DETECTION", "maxResults": 1},
                        {"type": "DOCUMENT_TEXT_DETECTION", "maxResults": 1},
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if 'responses' in result and result['responses']:
                resp = result['responses'][0]
                if 'textAnnotations' in resp:
                    text = resp['textAnnotations'][0]['description']
                    return OCRResult(
                        success=True,
                        text=text,
                        confidence=resp.get('fullTextAnnotation', {}).get('pages', [{}])[0].get('confidence', 0.8)
                    )
                elif 'fullTextAnnotation' in resp:
                    text = resp['fullTextAnnotation']['text']
                    return OCRResult(
                        success=True,
                        text=text,
                        confidence=0.8
                    )
            
            return OCRResult(success=False, error="未识别到文本")
            
        except Exception as e:
            logger.error(f"Google Vision OCR error: {e}")
            return OCRResult(success=False, error=str(e))


class OpenAIVisionOCR(OCRService):
    """OpenAI GPT-4 Vision OCR"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('AI_API_KEY')
        self.model = model
        self.api_base = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    def extract_text(self, image_path: str) -> OCRResult:
        """从图片文件提取文本"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            return self.extract_text_base64(image_data)
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            return OCRResult(success=False, error=str(e))
    
    def extract_text_base64(self, image_data: str) -> OCRResult:
        """使用 GPT-4 Vision 提取并解析族谱文本"""
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            return OCRResult(success=False, error="OCR 服务未配置")
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """请识别这张族谱图片中的所有成员信息，并以JSON格式返回。

族谱通常包含以下信息：
- 姓名
- 性别
- 出生日期
- 籍贯/出生地
- 配偶姓名
- 子女姓名
- 职业
- 备注

请尽可能提取所有可见的信息。如果不确定某些字段，请留空。

返回格式：
{
  "members": [
    {
      "name": "姓名",
      "gender": "M或F",
      "birth_date": "YYYY-MM-DD或年份",
      "birth_place": "籍贯",
      "spouse": "配偶姓名",
      "children": ["子女1", "子女2"],
      "occupation": "职业",
      "generation": "代数",
      "notes": "备注"
    }
  ],
  "family_name": "姓氏",
  "origin_place": "籍贯",
  "notes": "整体备注"
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    return OCRResult(
                        success=True,
                        text=content,
                        structured_data=data.get('members', []),
                        confidence=0.85
                    )
            except json.JSONDecodeError:
                pass
            
            return OCRResult(
                success=True,
                text=content,
                confidence=0.7
            )
            
        except ImportError:
            return OCRResult(success=False, error="OpenAI 库未安装")
        except Exception as e:
            logger.error(f"OpenAI Vision OCR error: {e}")
            return OCRResult(success=False, error=str(e))


class MockOCRService(OCRService):
    """Mock OCR 服务 (用于测试)"""
    
    def extract_text(self, image_path: str) -> OCRResult:
        return self._mock_result()
    
    def extract_text_base64(self, image_data: str) -> OCRResult:
        return self._mock_result()
    
    def _mock_result(self) -> OCRResult:
        """返回模拟的族谱数据"""
        mock_data = {
            "family_name": "王",
            "origin_place": "山西太原",
            "members": [
                {
                    "name": "王德明",
                    "gender": "M",
                    "birth_date": "1920",
                    "birth_place": "山西太原",
                    "generation": 1,
                    "notes": "迁居始祖"
                },
                {
                    "name": "王建国",
                    "gender": "M",
                    "birth_date": "1945",
                    "birth_place": "山西太原",
                    "father": "王德明",
                    "generation": 2,
                    "occupation": "教师"
                },
                {
                    "name": "王小华",
                    "gender": "F",
                    "birth_date": "1948",
                    "birth_place": "山西太原",
                    "father": "王德明",
                    "generation": 2,
                    "spouse": "李文斌"
                },
                {
                    "name": "王志强",
                    "gender": "M",
                    "birth_date": "1970",
                    "birth_place": "北京",
                    "father": "王建国",
                    "mother": "张秀英",
                    "generation": 3,
                    "occupation": "工程师"
                },
                {
                    "name": "王丽娜",
                    "gender": "F",
                    "birth_date": "1975",
                    "birth_place": "北京",
                    "father": "王建国",
                    "mother": "张秀英",
                    "generation": 3,
                    "occupation": "医生"
                }
            ],
            "notes": "此族谱记录王氏家族五代传承"
        }
        
        return OCRResult(
            success=True,
            text="王德明 (1920) - 王建国 (1945) - 王志强 (1970) ...",
            structured_data=mock_data['members'],
            confidence=0.75
        )


def get_ocr_service(provider: str = None) -> OCRService:
    """获取 OCR 服务实例"""
    provider = provider or os.environ.get('OCR_PROVIDER', 'mock')
    
    if provider == 'google_vision':
        return GoogleVisionOCR()
    elif provider == 'openai_vision':
        return OpenAIVisionOCR()
    else:
        return MockOCRService()


def parse_genealogy_text(text: str) -> Dict[str, Any]:
    """使用 AI 解析族谱文本"""
    from .capabilities import get_default_ai_service
    
    ai_service = get_default_ai_service()
    
    prompt = f"""请分析以下族谱文本，提取结构化的家族成员信息：

{text}

请以JSON格式返回：
{{
  "family_name": "姓氏",
  "origin_place": "籍贯",
  "members": [
    {{
      "name": "姓名",
      "gender": "M或F",
      "birth_date": "出生日期",
      "birth_place": "出生地",
      "father": "父亲姓名",
      "mother": "母亲姓名",
      "spouse": "配偶",
      "generation": 代数,
      "occupation": "职业",
      "notes": "备注"
    }}
  ],
  "notes": "整体备注"
}}"""
    
    system_prompt = """你是一位专业的族谱研究专家，擅长从历史文献中提取家族信息。
请仔细分析文本，尽可能准确地提取每个成员的详细信息。
对于不完整的信息，基于上下文进行合理推断。
始终返回有效的JSON格式。"""
    
    response = ai_service.generate_sync(prompt, system_prompt)
    
    if not response.success:
        return {"members": [], "error": response.error}
    
    try:
        json_start = response.content.find('{')
        json_end = response.content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response.content[json_start:json_end]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    return {"members": [], "raw_text": response.content}
