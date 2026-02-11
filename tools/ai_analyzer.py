"""Video analysis using GitHub Copilot SDK"""
import asyncio
import json
from typing import Dict, Any
from copilot import CopilotClient


def analyze_video(video_info: Dict[str, Any], file_size_mb: float) -> Dict[str, Any]:
    """
    使用 GitHub Copilot SDK 分析影片並建議最佳轉碼參數

    Args:
        video_info: 影片資訊字典（來自 ffprobe）
        file_size_mb: 影片檔案大小（MB）

    Returns:
        包含建議參數的字典
    """
    return asyncio.run(_analyze_video_async(video_info, file_size_mb))


async def _analyze_video_async(video_info: Dict[str, Any], file_size_mb: float) -> Dict[str, Any]:
    """
    異步分析影片並建議最佳轉碼參數

    Args:
        video_info: 影片資訊字典（來自 ffprobe）
        file_size_mb: 影片檔案大小（MB）

    Returns:
        包含建議參數的字典
    """
    # 初始化 Copilot 客戶端
    client = CopilotClient()
    await client.start()

    try:
        # 創建對話會話
        session = await client.create_session({
            "model": "claude-sonnet-4.5",
            "streaming": False,
        })

        # 構建分析提示
        prompt = _build_analysis_prompt(video_info, file_size_mb)

        # 收集響應
        done = asyncio.Event()
        final_content = ""

        def on_event(event):
            nonlocal final_content
            event_type = event.type.value

            if event_type == "assistant.message":
                final_content = event.data.content
            elif event_type == "session.idle":
                done.set()

        # 註冊事件處理器（必須在 send 之前）
        session.on(on_event)

        # 發送分析請求
        await session.send({"prompt": prompt})
        await done.wait()

        # 解析 AI 響應
        params = _parse_ai_response(final_content)

        # 清理資源
        await session.destroy()
        await client.stop()

        return params

    except Exception as e:
        await client.stop()
        raise RuntimeError(f"AI 分析失敗: {e}")


def _build_analysis_prompt(video_info: Dict[str, Any], file_size_mb: float) -> str:
    """
    構建 AI 分析提示詞

    Args:
        video_info: 影片資訊
        file_size_mb: 檔案大小（MB）

    Returns:
        提示詞字串
    """
    video = video_info.get("video", {})
    audio = video_info.get("audio", {})

    prompt = f"""你是一個專業的影片轉碼參數優化專家。請分析以下影片資訊，並建議最佳的 H.265 轉碼參數。

影片資訊：
- 解析度: {video.get('width', 0)}x{video.get('height', 0)}
- 編碼格式: {video.get('codec', 'unknown')}
- 幀率: {video.get('fps', 0):.2f} fps
- 位元率: {video.get('bit_rate', 0) / 1000:.0f} kbps
- 像素格式: {video.get('pix_fmt', 'unknown')}
- 檔案大小: {file_size_mb:.2f} MB
- 時長: {video_info.get('duration', 0):.1f} 秒

音訊資訊：
- 編碼格式: {audio.get('codec', 'unknown')}
- 取樣率: {audio.get('sample_rate', 0)} Hz
- 聲道數: {audio.get('channels', 0)}
- 位元率: {audio.get('bit_rate', 0) / 1000:.0f} kbps

請根據以下原則提供建議：
1. **CRF 值**（18-28，越低品質越好但檔案越大）：
   - 高清晰度內容（1080p+）建議 20-24
   - 標清內容（720p-）建議 22-26
   - 考慮原始位元率和品質

2. **Preset**（速度與壓縮效率平衡）：
   - ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
   - 建議 medium 或 slow

3. **解析度**：
   - 如果原始解析度過高且位元率較低，建議降低解析度
   - 4K → 1080p, 1080p → 720p（如果合適）
   - 否則保持 "keep"

4. **音訊位元率**：
   - 立體聲建議 128k-192k
   - 多聲道建議 192k-256k

5. **預估壓縮率**：
   - H.265 通常可達到 30-50% 的壓縮率

請以 JSON 格式回覆，格式如下：
```json
{{
  "recommended_crf": 23,
  "preset": "medium",
  "resolution": "keep",
  "audio_bitrate": "128k",
  "estimated_size_reduction": "40%",
  "reasoning": "簡短說明建議理由"
}}
```

只回傳 JSON，不要有其他文字。"""

    return prompt


def _parse_ai_response(response: str) -> Dict[str, Any]:
    """
    解析 AI 響應並提取參數

    Args:
        response: AI 的回應文字

    Returns:
        參數字典
    """
    try:
        # 嘗試從回應中提取 JSON
        # 移除可能的 markdown 代碼塊標記
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # 解析 JSON
        params = json.loads(response)

        # 驗證必要欄位
        required_fields = [
            "recommended_crf",
            "preset",
            "resolution",
            "audio_bitrate",
            "estimated_size_reduction",
            "reasoning"
        ]

        for field in required_fields:
            if field not in params:
                raise ValueError(f"缺少必要欄位: {field}")

        return params

    except json.JSONDecodeError as e:
        # 如果 JSON 解析失敗，使用預設值
        print(f"[WARN] 無法解析 AI 回應，使用預設參數: {e}")
        return {
            "recommended_crf": 23,
            "preset": "medium",
            "resolution": "keep",
            "audio_bitrate": "128k",
            "estimated_size_reduction": "40%",
            "reasoning": "AI 分析失敗，使用預設安全參數"
        }
    except Exception as e:
        print(f"[WARN] 解析錯誤，使用預設參數: {e}")
        return {
            "recommended_crf": 23,
            "preset": "medium",
            "resolution": "keep",
            "audio_bitrate": "128k",
            "estimated_size_reduction": "40%",
            "reasoning": "參數解析失敗，使用預設安全參數"
        }
