"""Video information extraction using ffprobe"""

import json
import subprocess
from typing import Any, Dict


def get_video_info_ffprobe(video_path: str) -> Dict[str, Any]:
    """
    使用 ffprobe 取得影片資訊

    Args:
        video_path: 影片檔案路徑

    Returns:
        包含影片資訊的字典
    """
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        # 提取關鍵資訊
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

        info = {
            "format": data.get("format", {}).get("format_name", "unknown"),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "bit_rate": int(data.get("format", {}).get("bit_rate", 0)),
            "size": int(data.get("format", {}).get("size", 0)),
        }

        if video_stream:
            info["video"] = {
                "codec": video_stream.get("codec_name", "unknown"),
                "width": video_stream.get("width", 0),
                "height": video_stream.get("height", 0),
                "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                "bit_rate": int(video_stream.get("bit_rate", 0)),
                "pix_fmt": video_stream.get("pix_fmt", "unknown"),
            }

        if audio_stream:
            info["audio"] = {
                "codec": audio_stream.get("codec_name", "unknown"),
                "sample_rate": int(audio_stream.get("sample_rate", 0)),
                "channels": audio_stream.get("channels", 0),
                "bit_rate": int(audio_stream.get("bit_rate", 0)),
            }

        return info

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe 執行失敗: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 ffprobe 輸出失敗: {e}")
