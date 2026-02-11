"""Video transcoding using FFmpeg and HandBrake"""
import subprocess
from typing import Dict, Any


def transcode_with_ffmpeg(
    input_path: str,
    output_path: str,
    params: Dict[str, Any],
    duration_limit: int = None
) -> bool:
    """
    使用 FFmpeg 轉碼影片

    Args:
        input_path: 輸入影片路徑
        output_path: 輸出影片路徑
        params: 轉碼參數（包含 CRF, preset, resolution 等）
        duration_limit: 時長限制（秒），用於預覽模式

    Returns:
        成功返回 True，失敗返回 False
    """
    crf = params.get("recommended_crf", 23)
    preset = params.get("preset", "medium")
    resolution = params.get("resolution", "keep")
    audio_bitrate = params.get("audio_bitrate", "128k")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
    ]

    # 添加時長限制（預覽模式）
    if duration_limit is not None:
        cmd.extend(["-t", str(duration_limit)])

    cmd.extend([
        "-c:v", "libx265",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", audio_bitrate,
    ])

    # 處理解析度調整
    if resolution != "keep":
        cmd.extend(["-vf", f"scale={resolution}"])

    cmd.append(output_path)

    try:
        print(f"執行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("[OK] FFmpeg 轉碼完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] FFmpeg 轉碼失敗: {e}")
        return False


def transcode_with_handbrake(
    input_path: str,
    output_path: str,
    params: Dict[str, Any],
    duration_limit: int = None
) -> bool:
    """
    使用 HandBrake CLI 轉碼影片

    Args:
        input_path: 輸入影片路徑
        output_path: 輸出影片路徑
        params: 轉碼參數（包含 CRF, preset, resolution 等）
        duration_limit: 時長限制（秒），用於預覽模式

    Returns:
        成功返回 True，失敗返回 False
    """
    crf = params.get("recommended_crf", 23)
    preset = params.get("preset", "medium")
    resolution = params.get("resolution", "keep")
    audio_bitrate = params.get("audio_bitrate", "128")

    cmd = [
        "HandBrakeCLI",
        "-i", input_path,
        "-o", output_path,
    ]

    # 添加時長限制（預覽模式）
    if duration_limit is not None:
        cmd.extend(["--start-at", "duration:0", "--stop-at", f"duration:{duration_limit}"])

    cmd.extend([
        "-e", "x265",
        "-q", str(crf),
        "--encoder-preset", preset,
        "-E", "av_aac",
        "-B", audio_bitrate,
    ])

    # 處理解析度調整
    if resolution != "keep":
        width = resolution.split("x")[0] if "x" in resolution else resolution.split(":")[0]
        cmd.extend(["-w", width])

    try:
        print(f"執行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("[OK] HandBrake 轉碼完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] HandBrake 轉碼失敗: {e}")
        return False
