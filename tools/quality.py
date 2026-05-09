"""Video quality assessment using VMAF, PSNR, and SSIM"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
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


def calculate_vmaf(
    reference_path: str,
    distorted_path: str,
    n_subsample: int = 1,
    is_preview: bool = False,
) -> Dict[str, float]:
    """
    使用 VMAF 計算影片品質

    Args:
        reference_path: 原始影片路徑
        distorted_path: 轉碼後影片路徑
        n_subsample: 每 N 幀取樣一次
        is_preview: 是否為預覽模式（若是，則對原始片執行相同的多段採樣拼接以對齊）

    Returns:
        VMAF 分數字典
    """
    distorted_duration = _get_duration(distorted_path)
    ref_total_duration = _get_duration(reference_path) if is_preview else None

    # 以 timestamp 命名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    vmaf_json_path = str(Path(distorted_path).parent / f"vmaf_{timestamp}.json")

    n_threads = os.cpu_count() or 1
    # ffmpeg filter 語法用 ':' 分隔 option、'\' 當 escape；Windows 路徑（如 Z:\...）
    # 直接塞會被當成額外的 option 分隔。把反斜線換成正斜線、把冒號 escape 掉避開歧義。
    ff_log_path = vmaf_json_path.replace("\\", "/").replace(":", r"\:")
    libvmaf_opts = f"log_fmt=json:log_path={ff_log_path}:n_threads={n_threads}:n_subsample={n_subsample}"

    if is_preview:
        # 預覽模式：用 -ss/-t 各自 seek reference 的三段，再 concat 對齊 distorted
        # 每段起始點與 transcoder.py 完全一致（10%, 50%, 80%）
        seg_dur = distorted_duration / 3
        starts = [ref_total_duration * 0.1, ref_total_duration * 0.5, ref_total_duration * 0.8]

        # inputs 1/2/3 = reference 的三個片段；不使用 split，避免大量緩衝
        filter_complex = (
            "[1:v]setpts=PTS-STARTPTS[r0];"
            "[2:v]setpts=PTS-STARTPTS[r1];"
            "[3:v]setpts=PTS-STARTPTS[r2];"
            "[r0][r1][r2]concat=n=3:v=1:a=0[refv];"
            "[0:v]scale=1920:1080:flags=bicubic[dis];"
            "[refv]scale=1920:1080:flags=bicubic[ref];"
            f"[dis][ref]libvmaf={libvmaf_opts}"
        )
        cmd = [
            "ffmpeg",
            "-i", distorted_path,
            "-ss", str(starts[0]), "-t", str(seg_dur), "-i", reference_path,
            "-ss", str(starts[1]), "-t", str(seg_dur), "-i", reference_path,
            "-ss", str(starts[2]), "-t", str(seg_dur), "-i", reference_path,
            "-filter_complex", filter_complex,
            "-f", "null",
            "-",
        ]
    else:
        lavfi = (
            "[0:v]scale=1920:1080:flags=bicubic[dis];"
            "[1:v]scale=1920:1080:flags=bicubic[ref];"
            f"[dis][ref]libvmaf={libvmaf_opts}"
        )
        # -t 放在第二個 -i 前，限制 reference 只讀取與 distorted 等長，防止空幀計分
        cmd = [
            "ffmpeg",
            "-i", distorted_path,
            "-t", str(distorted_duration),
            "-i", reference_path,
            "-lavfi", lavfi,
            "-f", "null",
            "-",
        ]

    if n_subsample > 1:
        print(
            f"  (n_threads={n_threads}, n_subsample={n_subsample} → 每 {n_subsample} 幀取樣一次，加速 ~{n_subsample}x)"
        )

    try:
        # 即時解析 ffmpeg stderr，以 tqdm 顯示 VMAF 計算進度；同時阻止系統睡眠
        with prevent_sleep():
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            last_elapsed = 0.0
            stderr_lines: list = []
            with tqdm(
                total=distorted_duration,
                unit="s",
                unit_scale=True,
                desc="VMAF 計算中",
                dynamic_ncols=True,
            ) as pbar:
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
                        stderr_lines.append(line)
                        m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                        if m:
                            h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                            elapsed = h * 3600 + mi * 60 + s
                            increment = elapsed - last_elapsed
                            if increment > 0:
                                pbar.update(min(increment, distorted_duration - pbar.n))
                                last_elapsed = elapsed
                # 確保進度條滿格
                remaining = distorted_duration - pbar.n
                if remaining > 0:
                    pbar.update(remaining)

        process.wait()

        if process.returncode != 0:
            tail = "\n".join(stderr_lines[-20:])
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=tail)

        with open(vmaf_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            pooled = data.get("pooled_metrics", {})

        print(f"VMAF 結果已儲存至：{vmaf_json_path}")

        scores = {
            "vmaf": pooled.get("vmaf", {}).get("mean", 0),
            "_vmaf_json_path": vmaf_json_path,  # 供 main.py 診斷使用
        }
        # 僅在 JSON 中確實存在時才回傳（libvmaf 預設不計算 PSNR/SSIM）
        if "psnr" in pooled:
            scores["psnr"] = pooled["psnr"].get("mean", 0)
        if "ssim" in pooled:
            scores["ssim"] = pooled["ssim"].get("mean", 0)
        return scores

    except subprocess.CalledProcessError as e:
        stderr_tail = (e.stderr or "").strip()
        msg = f"VMAF 計算失敗 (exit {e.returncode})"
        if stderr_tail:
            msg += f"\n--- ffmpeg stderr (最後 20 行) ---\n{stderr_tail}"
        raise RuntimeError(msg)
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
    psnr_cmd = ["ffmpeg", "-i", distorted_path, "-i", reference_path, "-lavfi", "psnr", "-f", "null", "-"]

    # 計算 SSIM
    ssim_cmd = ["ffmpeg", "-i", distorted_path, "-i", reference_path, "-lavfi", "ssim", "-f", "null", "-"]

    try:
        with prevent_sleep():
            # 執行 PSNR
            psnr_result = subprocess.run(
                psnr_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace"
            )
            psnr_match = re.search(r"average:(\d+\.\d+)", psnr_result.stderr)
            psnr = float(psnr_match.group(1)) if psnr_match else 0

            # 執行 SSIM
            ssim_result = subprocess.run(
                ssim_cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace"
            )
            ssim_match = re.search(r"All:(\d+\.\d+)", ssim_result.stderr)
            ssim = float(ssim_match.group(1)) if ssim_match else 0

        return {
            "psnr": psnr,
            "ssim": ssim,
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"品質計算失敗: {e.stderr}")


def diagnose_vmaf_params(vmaf_json_path: str) -> Dict[str, Any]:
    """
    讀取 vmaf.json 的 sub-metrics，診斷品質問題並給出具體的參數調整建議。

    VMAF sub-metrics 說明：
      ADM2 / ADM scale0-3 : 邊緣/細節保留度（Anisotropic Distortion Measure）
      VIF scale0-3        : 視覺資訊保真度（Visual Information Fidelity）
        - scale0 = 粗粒度（對 blocking/banding 最敏感）
        - scale3 = 細粒度（對細部紋理最敏感）
      motion / motion2    : 動態量（值越高代表畫面越動態）

    Args:
        vmaf_json_path: vmaf.json 路徑

    Returns:
        包含診斷結果與建議的字典
    """
    try:
        with open(vmaf_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"available": False, "suggestions": []}

    pooled = data.get("pooled_metrics", {})
    if not pooled:
        return {"available": False, "suggestions": []}

    def mean(key: str) -> float:
        return pooled.get(key, {}).get("mean", 1.0)

    vmaf_score = mean("vmaf")
    adm2 = mean("integer_adm2")
    adm_s2 = mean("integer_adm_scale2")
    adm_s3 = mean("integer_adm_scale3")
    vif_s0 = mean("integer_vif_scale0")
    vif_s3 = mean("integer_vif_scale3")
    motion2 = mean("integer_motion2")

    suggestions = []

    # --- blocking / banding (VIF scale0 最敏感) ---
    if vif_s0 < 0.55:
        suggestions.append(
            f"VIF-scale0={vif_s0:.3f} (嚴重) -> 明顯方塊感/色帶，建議 CRF 降低 4-6（例如 CRF 23 -> 17-19）"
        )
    elif vif_s0 < 0.70:
        suggestions.append(f"VIF-scale0={vif_s0:.3f} -> 輕度 blocking/banding，建議 CRF 降低 2-3")

    # --- 邊緣模糊 (ADM2) ---
    if adm2 < 0.82:
        suggestions.append(f"ADM2={adm2:.3f} (嚴重) -> 邊緣嚴重模糊，建議降低 CRF 且改用 slower/veryslow preset")
    elif adm2 < 0.88:
        suggestions.append(f"ADM2={adm2:.3f} -> 輕度邊緣模糊，建議改用 slow 或 slower preset")

    # --- 細節紋理損失 (ADM scale2/3 + VIF scale3) ---
    if adm_s3 < 0.82 or vif_s3 < 0.80:
        suggestions.append(
            f"ADM-scale3={adm_s3:.3f} / VIF-scale3={vif_s3:.3f} -> 細部紋理損失，建議 slower preset 或 CRF -2"
        )
    elif adm_s2 < 0.85:
        suggestions.append(f"ADM-scale2={adm_s2:.3f} -> 中等細節損失，建議改用 slow preset")

    # --- 高動態場景 ---
    if motion2 > 8.0:
        suggestions.append(
            f"motion2={motion2:.2f} (極高動態) -> 動態模糊/拖影，建議 CRF -3 或增加參考幀（--encoder-option ref=5）"
        )
    elif motion2 > 4.0:
        suggestions.append(f"motion2={motion2:.2f} (高動態) -> 動態場景品質不足，建議 CRF -2")

    # --- 無明顯問題但分數仍低 ---
    if not suggestions and vmaf_score < 70:
        suggestions.append("各 sub-metrics 無明顯異常，低分可能源於來源素材本身已有壓縮損失（generation loss）")

    return {
        "available": True,
        "vmaf": vmaf_score,
        "adm2": adm2,
        "vif_scale0": vif_s0,
        "vif_scale3": vif_s3,
        "motion2": motion2,
        "suggestions": suggestions,
    }


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
