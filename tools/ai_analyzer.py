"""Video analysis using GitHub Copilot SDK"""

import asyncio
import json
from typing import Any, Dict

from copilot import CopilotClient
from copilot.session import PermissionHandler


def analyze_video(
    video_info: Dict[str, Any],
    file_size_mb: float,
    vmaf_data: Dict[str, Any] = None,
    model: str = "gpt5-mini",
    extra_prompt: str = None,
) -> Dict[str, Any]:
    """
    使用 GitHub Copilot SDK 分析影片並建議最佳轉碼參數

    Args:
        video_info: 影片資訊字典（來自 ffprobe）
        file_size_mb: 影片檔案大小（MB）
        vmaf_data: 上次轉碼的 vmaf.json pooled_metrics（可選）；
                   提供時 AI 會依據品質指標給出調整後的參數
        model: 使用的 AI 模型名稱，預設為 gpt5-mini
        extra_prompt: 使用者自訂的額外提示詞，會附加在原始 prompt 後面

    Returns:
        包含建議參數的字典
    """
    return asyncio.run(_analyze_video_async(video_info, file_size_mb, vmaf_data, model, extra_prompt))


async def _analyze_video_async(
    video_info: Dict[str, Any],
    file_size_mb: float,
    vmaf_data: Dict[str, Any] = None,
    model: str = "gpt5-mini",
    extra_prompt: str = None,
) -> Dict[str, Any]:
    """
    異步分析影片並建議最佳轉碼參數

    Args:
        video_info: 影片資訊字典（來自 ffprobe）
        file_size_mb: 影片檔案大小（MB）
        vmaf_data: 上次轉碼的 vmaf.json pooled_metrics（可選）
        model: 使用的 AI 模型名稱
        extra_prompt: 使用者自訂的額外提示詞

    Returns:
        包含建議參數的字典
    """
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=model,
            streaming=False,
        )

        prompt = _build_analysis_prompt(video_info, file_size_mb, vmaf_data, extra_prompt)

        # send_and_wait 會自動 attach 事件 handler、發 prompt、等到 session.idle，回傳最後一則 assistant message
        result = await session.send_and_wait(prompt, timeout=120.0)
        final_content = ""
        if result is not None:
            content = getattr(getattr(result, "data", None), "content", None)
            if isinstance(content, str):
                final_content = content

        params = _parse_ai_response(final_content)
        await session.destroy()
        return params
    finally:
        await client.stop()


def _build_analysis_prompt(
    video_info: Dict[str, Any], file_size_mb: float, vmaf_data: Dict[str, Any] = None, extra_prompt: str = None
) -> str:
    """
    構建 AI 分析提示詞

    Args:
        video_info: 影片資訊
        file_size_mb: 檔案大小（MB）
        vmaf_data: vmaf.json 的 pooled_metrics（可選）
        extra_prompt: 使用者自訂的額外提示詞，附加在 prompt 末尾（可選）

    Returns:
        提示詞字串
    """
    video = video_info.get("video", {})

    prompt = f"""你是一個專業的影片轉碼參數優化專家。請分析以下影片資訊，並建議最佳的 H.265 轉碼參數。

影片資訊：
- 解析度: {video.get("width", 0)}x{video.get("height", 0)}
- 編碼格式: {video.get("codec", "unknown")}
- 幀率: {video.get("fps", 0):.2f} fps
- 位元率: {video.get("bit_rate", 0) / 1000:.0f} kbps
- 像素格式: {video.get("pix_fmt", "unknown")}
- 檔案大小: {file_size_mb:.2f} MB
- 時長: {video_info.get("duration", 0):.1f} 秒

音訊：直接複製原始音軌，不重新編碼。

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

4. **預估壓縮率**：
   - H.265 通常可達到 30-50% 的壓縮率（不含音訊部分）

請以 JSON 格式回覆，格式如下：
```json
{{
  "recommended_crf": 23,
  "preset": "medium",
  "resolution": "keep",
  "estimated_size_reduction": "40%",
  "reasoning": "簡短說明建議理由"
}}
```

只回傳 JSON，不要有其他文字。"""

    # 有 VMAF 資料時，在 prompt 末尾插入反饋區段，要求 AI 依指標調整參數
    if vmaf_data:

        def m(key: str) -> str:
            v = vmaf_data.get(key, {})
            mean = v.get("mean", None) if isinstance(v, dict) else None
            return f"{mean:.4f}" if mean is not None else "N/A"

        vmaf_section = f"""

---
## 上次轉碼的 VMAF 品質反饋

以下是上次轉碼後 libvmaf 測量的 pooled_metrics（平均值），請依據這些數值調整參數：

| 指標 | 數值 | 意義 |
|------|------|------|
| VMAF 總分 | {m("vmaf")} | 0-100，越高越好，<70 表示需要調整 |
| ADM2（邊緣保留） | {m("integer_adm2")} | <0.88 表示邊緣模糊，建議 slower preset |
| ADM scale2（中細節）| {m("integer_adm_scale2")} | <0.85 表示中等細節損失 |
| ADM scale3（細部細節）| {m("integer_adm_scale3")} | <0.85 表示精細細節損失 |
| VIF scale0（blocking）| {m("integer_vif_scale0")} | <0.70 表示有方塊感/色帶，建議降低 CRF |
| VIF scale3（細部紋理）| {m("integer_vif_scale3")} | <0.85 表示紋理損失 |
| Motion2（動態量） | {m("integer_motion2")} | >4 表示高動態，>8 表示極高動態 |

**請根據以上數值，在原本的建議基礎上進行調整，使 VMAF 分數達到 80 以上。**
調整優先順序：
1. VIF scale0 偏低 → 降低 CRF（每次 2-3）
2. ADM2 偏低 → 改用 slow 或 slower preset
3. 高動態（motion2 > 4）→ 同時降低 CRF 與改用 slower preset
4. 若各指標接近正常但 VMAF 仍低 → 可能是來源素材限制，降低 CRF 2 即可"""

        prompt = prompt.replace("只回傳 JSON，不要有其他文字。", vmaf_section + "\n\n只回傳 JSON，不要有其他文字。")

    # 附加使用者自訂 prompt
    if extra_prompt:
        prompt += f"\n\n---\n## 使用者額外需求\n\n{extra_prompt}"

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
            "estimated_size_reduction",
            "reasoning",
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
            "estimated_size_reduction": "40%",
            "reasoning": "AI 分析失敗，使用預設安全參數",
        }
    except Exception as e:
        print(f"[WARN] 解析錯誤，使用預設參數: {e}")
        return {
            "recommended_crf": 23,
            "preset": "medium",
            "resolution": "keep",
            "estimated_size_reduction": "40%",
            "reasoning": "參數解析失敗，使用預設安全參數",
        }
