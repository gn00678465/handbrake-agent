"""Video transcoding using FFmpeg and HandBrake"""

import json
import re
import subprocess
from typing import Any, Dict

from tqdm import tqdm

from tools.sleep_guard import prevent_sleep


def _get_duration(path: str) -> float:
    """取得影片時長（秒）"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path]
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace"
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def transcode_with_ffmpeg(
    input_path: str, output_path: str, params: Dict[str, Any], duration_limit: int = None, multi_segment: bool = False
) -> bool:
    """
    使用 FFmpeg 轉碼影片

    Args:
        input_path: 輸入影片路徑
        output_path: 輸出影片路徑
        params: 轉碼參數（包含 CRF, preset, resolution 等）
        duration_limit: 時長限制（秒），用於預覽模式
        multi_segment: 是否使用多段採樣（20%, 50%, 80% 各 10 秒）

    Returns:
        成功返回 True，失敗返回 False
    """
    crf = params.get("recommended_crf", 23)
    preset = params.get("preset", "medium")
    resolution = params.get("resolution", "keep")

    if multi_segment and duration_limit:
        # 多段採樣邏輯：10%, 50%, 80% 各取 duration_limit / 3 秒
        # preview 僅供 VMAF 使用，不需要音訊（-an），避免無音軌時 asplit 失敗
        total_dur = _get_duration(input_path)
        seg_dur = duration_limit / 3
        starts = [total_dur * 0.1, total_dur * 0.5, total_dur * 0.8]

        # 只處理影像：split → trim → concat
        filter_str = "[0:v]split=3[sv0][sv1][sv2];"
        for i, start in enumerate(starts):
            filter_str += f"[sv{i}]trim=start={start}:duration={seg_dur},setpts=PTS-STARTPTS[v{i}];"
        filter_str += "[v0][v1][v2]concat=n=3:v=1:a=0[outv]"

        if resolution != "keep":
            filter_str += f";[outv]scale={resolution}[finalv]"
            map_video = "[finalv]"
        else:
            map_video = "[outv]"

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-filter_complex", filter_str,
            "-map", map_video,
            "-c:v", "libx265", "-crf", str(crf), "-preset", preset,
            "-an",  # preview 不需要音訊
            output_path,
        ]
        total = duration_limit
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path]
        if duration_limit is not None:
            cmd.extend(["-t", str(duration_limit)])
        cmd.extend(["-c:v", "libx265", "-crf", str(crf), "-preset", preset, "-c:a", "copy"])
        if resolution != "keep":
            cmd.extend(["-vf", f"scale={resolution}"])
        cmd.append(output_path)
        total = duration_limit if duration_limit is not None else _get_duration(input_path)

    try:
        with prevent_sleep():
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            last_elapsed = 0.0
            with tqdm(total=total, unit="s", unit_scale=True, desc="FFmpeg 轉碼中", dynamic_ncols=True) as pbar:
                buf = b""
                while True:
                    chunk = process.stderr.read(256)
                    if not chunk:
                        break
                    buf += chunk
                    parts = re.split(b"[\r\n]", buf)
                    buf = parts[-1]
                    for segment in parts[:-1]:
                        line = segment.decode("utf-8", errors="ignore")
                        m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                        if m:
                            h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                            elapsed = h * 3600 + mi * 60 + s
                            increment = elapsed - last_elapsed
                            if increment > 0:
                                pbar.update(min(increment, total - pbar.n))
                                last_elapsed = elapsed
                # 確保進度條滿格
                remaining = total - pbar.n
                if remaining > 0:
                    pbar.update(remaining)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

        print("[OK] FFmpeg 轉碼完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] FFmpeg 轉碼失敗: {e}")
        return False


def transcode_with_handbrake(
    input_path: str, output_path: str, params: Dict[str, Any], duration_limit: int = None
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

    cmd = [
        "HandBrakeCLI",
        "-i",
        input_path,
        "-o",
        output_path,
    ]

    # 添加時長限制（預覽模式）
    if duration_limit is not None:
        cmd.extend(["--start-at", "duration:0", "--stop-at", f"duration:{duration_limit}"])

    cmd.extend(
        [
            "-e",
            "x265",
            "-q",
            str(crf),
            "--encoder-preset",
            preset,
            "-E",
            "copy",  # 音訊直接複製，不重新編碼
        ]
    )

    # 處理解析度調整
    if resolution != "keep":
        width = resolution.split("x")[0] if "x" in resolution else resolution.split(":")[0]
        cmd.extend(["-w", width])

    try:
        with prevent_sleep():
            # HandBrake 將進度輸出至 stdout（格式：Encoding: task 1 of 1, XX.XX %）
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            last_pct = 0.0
            with tqdm(
                total=100.0,
                unit="%",
                desc="HandBrake 轉碼中",
                dynamic_ncols=True,
                bar_format="{desc}: {percentage:.1f}%|{bar}| [{elapsed}<{remaining}]",
            ) as pbar:
                buf = b""
                while True:
                    chunk = process.stdout.read(256)
                    if not chunk:
                        break
                    buf += chunk
                    parts = re.split(b"[\r\n]", buf)
                    buf = parts[-1]
                    for segment in parts[:-1]:
                        line = segment.decode("utf-8", errors="ignore")
                        m = re.search(r"(\d+\.\d+) %", line)
                        if m:
                            pct = float(m.group(1))
                            increment = pct - last_pct
                            if increment > 0:
                                pbar.update(min(increment, 100.0 - pbar.n))
                                last_pct = pct
                # 確保進度條滿格
                remaining = 100.0 - pbar.n
                if remaining > 0:
                    pbar.update(remaining)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

        print("[OK] HandBrake 轉碼完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] HandBrake 轉碼失敗: {e}")
        return False
