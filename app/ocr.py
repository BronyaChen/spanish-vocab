"""
OCR 模块
调用 AI 视觉模型从截图中提取西班牙语单词列表。
支持：qwen（通义千问 VL）、openai（GPT-4o）。
超长截图自动切片分段识别。
"""
import base64
import json
import re
import math
from io import BytesIO
from typing import List, Dict

import httpx
from PIL import Image

# ============================================================
# AI 供应商配置
# ============================================================
PROVIDERS = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-vl-max",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
    },
}

# 切片高度（像素），截图超过此高度则分段送识别
SLICE_HEIGHT = 2048

# 提取 JSON 的 Prompt
EXTRACTION_PROMPT = (
    "请从这张图片中提取所有西班牙语单词/词组列表。"
    "返回严格的 JSON 数组，格式为：\n"
    '[{"spanish":"单词","english":"英文翻译","chinese":"中文翻译"}]\n'
    "要求：\n"
    "1. chinese 是中文翻译\n"
    "2. 只提取词表条目，不要多余文本\n"
    "3. 如果图片中没有单词，返回空数组 []\n"
    "4. 只返回 JSON，不要任何其他说明文字"
)


# ============================================================
# 主入口
# ============================================================
async def extract_words(provider: str, api_key: str, image_bytes: bytes) -> List[Dict]:
    """
    从图片中提取单词列表。

    Args:
        provider: AI 供应商名称 (qwen / openai)
        api_key: 对应的 API Key
        image_bytes: 图片的原始字节数据

    Returns:
        [{"spanish": "...", "english": "...", "chinese": "..."}, ...]

    Raises:
        ValueError: 无 API Key 或调用失败
    """
    if not api_key:
        raise ValueError("请先在设置中配置 API Key")

    if provider not in PROVIDERS:
        raise ValueError(f"不支持的 AI 供应商：{provider}")

    # 打开图片，判断是否需要切片
    img = Image.open(BytesIO(image_bytes))
    width, height = img.size

    if height <= SLICE_HEIGHT:
        # 单片直接识别
        return await _recognize_single(provider, api_key, image_bytes)
    else:
        # 超长截图：按高度切片，逐段识别再合并去重
        return await _recognize_sliced(provider, api_key, img, width, height)


# ============================================================
# 单张图片识别
# ============================================================
async def _recognize_single(provider: str, api_key: str, image_bytes: bytes) -> List[Dict]:
    """对单张图片调用 AI 识别"""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    config = PROVIDERS[provider]
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(config["base_url"], json=payload, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"AI 接口返回错误 {e.response.status_code}：{e.response.text[:200]}")
        except httpx.RequestError as e:
            raise ValueError(f"AI 接口请求失败：{str(e)}")

    # 解析响应
    result = resp.json()
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ValueError(f"AI 返回格式异常：{json.dumps(result, ensure_ascii=False)[:200]}")

    return _parse_json_response(content)


# ============================================================
# 超长截图切片识别
# ============================================================
async def _recognize_sliced(
    provider: str, api_key: str, img: Image.Image, width: int, height: int
) -> List[Dict]:
    """将超长截图按 SLICE_HEIGHT 切片，逐段送 AI 再合并"""
    num_slices = math.ceil(height / SLICE_HEIGHT)
    all_words: List[Dict] = []
    seen_spanish: set = set()

    for i in range(num_slices):
        top = i * SLICE_HEIGHT
        bottom = min((i + 1) * SLICE_HEIGHT, height)
        slice_img = img.crop((0, top, width, bottom))

        # 转为字节
        buf = BytesIO()
        slice_img.save(buf, format="JPEG", quality=85)
        slice_bytes = buf.getvalue()

        # 识别该切片
        words = await _recognize_single(provider, api_key, slice_bytes)

        # 按 spanish 去重合并
        for w in words:
            sp = w.get("spanish", "").strip()
            if sp and sp not in seen_spanish:
                seen_spanish.add(sp)
                all_words.append(w)

    return all_words


# ============================================================
# JSON 解析容错
# ============================================================
def _parse_json_response(content: str) -> List[Dict]:
    """
    尝试从 AI 返回的文本中解析 JSON 数组。
    容错：正则提取 JSON 片段。
    """
    # 先尝试直接解析
    content = content.strip()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return _normalize_words(data)
    except json.JSONDecodeError:
        pass

    # 正则兜底：提取第一个 [...] 片段
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list):
                return _normalize_words(data)
        except json.JSONDecodeError:
            pass

    # 都失败了，返回空
    return []


def _normalize_words(data: list) -> List[Dict]:
    """标准化单词列表，确保每项有 spanish/english/chinese 字段"""
    result = []
    for item in data:
        if isinstance(item, dict) and "spanish" in item:
            result.append({
                "spanish": str(item.get("spanish", "")).strip(),
                "english": str(item.get("english", "")).strip(),
                "chinese": str(item.get("chinese", "")).strip(),
            })
    return result
