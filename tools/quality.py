"""Video quality assessment using VMAF, PSNR, and SSIM"""
import subprocess
import json
import re
from typing import Dict, Any


def _get_duration(path: str) -> float:
    """取得影片時長（秒）"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(json.loads(result.stdout)["format"]["duration"])


def calculate_vmaf(reference_path: str, distorted_path: str) -> Dict[str, float]:
    """
    使用 VMAF 計算影片品質

    Args:
        reference_path: 原始影片路徑
        distorted_path: 轉碼後影片路徑

    Returns:
        VMAF 分數字典
    """
    # 取得 distorted 時長，限制 reference 只比對相同長度，避免 VMAF 對空幀計分
    distorted_duration = _get_duration(distorted_path)

    cmd = [
        "ffmpeg",
        "-i", distorted_path,
        "-t", str(distorted_duration),
        "-i", reference_path,
        "-lavfi", "[0:v]scale=1920:1080:flags=bicubic[dis];[1:v]scale=1920:1080:flags=bicubic[ref];[dis][ref]libvmaf=log_fmt=json:log_path=vmaf.json",
        "-f", "null",
        "-"
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)

        with open("vmaf.json", "r") as f:
            data = json.load(f)
            pooled = data.get("pooled_metrics", {})

        scores = {
            "vmaf": pooled.get("vmaf", {}).get("mean", 0),
        }
        # 僅在 JSON 中確實存在時才回傳（libvmaf 預設不計算 PSNR/SSIM）
        if "psnr" in pooled:
            scores["psnr"] = pooled["psnr"].get("mean", 0)
        if "ssim" in pooled:
            scores["ssim"] = pooled["ssim"].get("mean", 0)
        return scores

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"VMAF 計算失敗: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"VMAF 結果解析失敗: {e}")


def calculate_psnr_ssim(reference_path: str, distorted_path: str) -> Dict[str, float]:
    """
    使用 FFmpeg 計算 PSNR 和 SSIM

    Args:
        reference_path: 原始影片路徑
        distorted_path: 轉碼後影片路徑

    Returns:
        包含 PSNR 和 SSIM 分數的字典
    """
    # 計算 PSNR
    psnr_cmd = [
        "ffmpeg",
        "-i", distorted_path,
        "-i", reference_path,
        "-lavfi", "psnr",
        "-f", "null",
        "-"
    ]

    # 計算 SSIM
    ssim_cmd = [
        "ffmpeg",
        "-i", distorted_path,
        "-i", reference_path,
        "-lavfi", "ssim",
        "-f", "null",
        "-"
    ]

    try:
        # 執行 PSNR
        psnr_result = subprocess.run(
            psnr_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        psnr_match = re.search(r"average:(\d+\.\d+)", psnr_result.stderr)
        psnr = float(psnr_match.group(1)) if psnr_match else 0

        # 執行 SSIM
        ssim_result = subprocess.run(
            ssim_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        ssim_match = re.search(r"All:(\d+\.\d+)", ssim_result.stderr)
        ssim = float(ssim_match.group(1)) if ssim_match else 0

        return {
            "psnr": psnr,
            "ssim": ssim,
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"品質計算失敗: {e.stderr}")


def evaluate_quality(scores: Dict[str, float]) -> Dict[str, Any]:
    """
    評估品質分數並給出建議

    Args:
        scores: 包含品質指標的字典

    Returns:
        評估結果字典
    """
    evaluation = {
        "details": [],
        "overall": "",
    }

    # VMAF 評估（0-100，越高越好）
    if "vmaf" in scores:
        vmaf = scores["vmaf"]
        if vmaf >= 95:
            evaluation["details"].append(f"VMAF: {vmaf:.2f} - 優秀 (幾乎無損)")
        elif vmaf >= 85:
            evaluation["details"].append(f"VMAF: {vmaf:.2f} - 良好 (高品質)")
        elif vmaf >= 70:
            evaluation["details"].append(f"VMAF: {vmaf:.2f} - 可接受 (中等品質)")
        else:
            evaluation["details"].append(f"VMAF: {vmaf:.2f} - 較差 (低品質)")

    # PSNR 評估（dB，越高越好，通常 30-50）
    if "psnr" in scores:
        psnr = scores["psnr"]
        if psnr >= 40:
            evaluation["details"].append(f"PSNR: {psnr:.2f} dB - 優秀")
        elif psnr >= 35:
            evaluation["details"].append(f"PSNR: {psnr:.2f} dB - 良好")
        elif psnr >= 30:
            evaluation["details"].append(f"PSNR: {psnr:.2f} dB - 可接受")
        else:
            evaluation["details"].append(f"PSNR: {psnr:.2f} dB - 較差")

    # SSIM 評估（0-1，越高越好）
    if "ssim" in scores:
        ssim = scores["ssim"]
        if ssim >= 0.95:
            evaluation["details"].append(f"SSIM: {ssim:.4f} - 優秀")
        elif ssim >= 0.90:
            evaluation["details"].append(f"SSIM: {ssim:.4f} - 良好")
        elif ssim >= 0.80:
            evaluation["details"].append(f"SSIM: {ssim:.4f} - 可接受")
        else:
            evaluation["details"].append(f"SSIM: {ssim:.4f} - 較差")

    # 整體評價
    vmaf_score = scores.get("vmaf", 0)
    psnr_score = scores.get("psnr", 0)
    ssim_score = scores.get("ssim", 0)

    if vmaf_score >= 90 or (psnr_score >= 38 and ssim_score >= 0.93):
        evaluation["overall"] = "轉碼品質優秀，推薦使用"
    elif vmaf_score >= 80 or (psnr_score >= 33 and ssim_score >= 0.88):
        evaluation["overall"] = "轉碼品質良好，可以使用"
    elif vmaf_score >= 70 or (psnr_score >= 30 and ssim_score >= 0.80):
        evaluation["overall"] = "轉碼品質可接受"
    else:
        evaluation["overall"] = "轉碼品質較差，建議調整參數"

    return evaluation
