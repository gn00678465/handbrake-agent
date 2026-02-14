import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from tqdm import tqdm

from cli.flags import (
    auto_loop,
    batch,
    ffmpeg,
    model,
    params_file,
    preview,
    prompt,
    verify,
    vmaf,
    vmaf_feedback,
    yes,
)
from tools.ai_analyzer import analyze_video
from tools.quality import (
    calculate_psnr_ssim,
    calculate_vmaf,
    diagnose_vmaf_params,
    evaluate_quality,
)
from tools.transcoder import transcode_with_ffmpeg, transcode_with_handbrake
from tools.video_info import get_video_info_ffprobe

VMAF_GOOD_THRESHOLD = 85  # VMAF 達到此分數視為品質良好，儲存參數並提前停止 auto-loop


class VideoTranscoder:
    """影片轉碼器，整合 AI 分析與品質驗證"""

    def process_video(
        self,
        input_path: str,
        output_path: str = None,
        use_ffmpeg: bool = False,
        verify_quality: bool = True,
        quality_method: str = "psnr_ssim",
        preview_mode: bool = False,
        preview_duration: int = 30,
        auto_confirm: bool = False,
        vmaf_feedback: Dict[str, Any] = None,
        model: str = "gpt5-mini",
        extra_prompt: str = None,
        params_override: Dict[str, Any] = None,
        vmaf_subsample: int = 1,
    ) -> Dict[str, Any]:
        """
        完整的影片處理流程

        Args:
            input_path: 輸入影片路徑
            output_path: 輸出影片路徑
            use_ffmpeg: 使用 FFmpeg 而非 HandBrake
            verify_quality: 是否進行品質驗證
            quality_method: 品質驗證方法 ('vmaf' 或 'psnr_ssim')
            preview_mode: 預覽模式，只轉換部分影片（vmaf json 與 params 僅在此模式下保留）
            preview_duration: 預覽模式的時長（秒）
            auto_confirm: 自動確認轉碼
            vmaf_feedback: VMAF 反饋資料
            model: Copilot SDK 使用的 AI 模型名稱
            extra_prompt: 使用者自訂的額外提示詞
            params_override: 直接指定轉碼參數，略過 AI 分析
            vmaf_subsample: VMAF 取樣間隔（每 N 幀計算一次）

        Returns:
            包含處理結果的字典（含 vmaf_json_path、params、params_path 等）
        """
        input_file = Path(input_path)
        if not output_path:
            suffix = "_preview" if preview_mode else "_h265"
            output_path = input_file.parent / f"{input_file.stem}{suffix}{input_file.suffix}"

        mode_text = f"【預覽模式 - {preview_duration}秒】" if preview_mode else ""
        print(f"\n處理影片：{input_path} {mode_text}")
        print("=" * 60)

        # 1. 取得影片資訊
        print("\n[1/5] 取得影片資訊...")
        video_info = get_video_info_ffprobe(input_path)
        file_size_mb = input_file.stat().st_size / (1024 * 1024)

        # 2. 參數取得：使用覆寫參數或 AI 分析
        if params_override:
            print("\n[2/5] 使用指定參數（略過 AI 分析）...")
            params = params_override
        else:
            print(f"\n[2/5] 使用 AI 分析最佳轉碼參數（模型：{model}）...")
            if extra_prompt:
                print(f"  附加 prompt: {extra_prompt[:60]}{'...' if len(extra_prompt) > 60 else ''}")
            try:
                params = analyze_video(video_info, file_size_mb, vmaf_feedback, model=model, extra_prompt=extra_prompt)
            except Exception as e:
                print(f"AI 分析失敗: {e}")
                return {}

        print("\n使用參數：")
        print(f"  CRF: {params.get('recommended_crf')}")
        print(f"  Preset: {params.get('preset')}")
        print(f"  解析度: {params.get('resolution')}")
        print("  音訊: copy（不重新編碼）")
        print(f"  預估壓縮: {params.get('estimated_size_reduction')}")
        print(f"  理由: {params.get('reasoning')}")

        # 3. 確認執行
        if auto_confirm:
            print("\n自動確認執行轉碼")
        else:
            try:
                confirm = input("\n是否執行轉碼？(y/n): ")
            except EOFError:
                confirm = "y"
            if confirm.lower() != "y":
                print("取消轉碼")
                return {}

        # 4. 執行轉碼
        transcode_text = f"[3/5] 執行轉碼（預覽前 {preview_duration} 秒）..." if preview_mode else "[3/5] 執行轉碼..."
        print(f"\n{transcode_text}")
        if use_ffmpeg:
            success = transcode_with_ffmpeg(
                input_path, str(output_path), params, duration_limit=preview_duration if preview_mode else None
            )
        else:
            success = transcode_with_handbrake(
                input_path, str(output_path), params, duration_limit=preview_duration if preview_mode else None
            )

        if not success:
            print("\n轉碼失敗！")
            return {}

        # 5. 品質驗證
        quality_scores = None
        vmaf_json_path = None
        if verify_quality:
            print("\n[4/5] 品質驗證...")
            try:
                if quality_method == "vmaf":
                    quality_scores = calculate_vmaf(input_path, str(output_path), n_subsample=vmaf_subsample)
                    vmaf_json_path = quality_scores.get("_vmaf_json_path", "") if quality_scores else None
                else:
                    quality_scores = calculate_psnr_ssim(input_path, str(output_path))

                evaluation = evaluate_quality(quality_scores)
                print("\n品質評估結果：")
                for detail in evaluation["details"]:
                    print(f"  {detail}")
                print(f"  整體評價: {evaluation['overall']}")

                # VMAF 診斷（在清理前執行，此時 vmaf json 仍存在）
                if quality_method == "vmaf" and vmaf_json_path:
                    if quality_scores.get("vmaf", 100) < 70:
                        diagnosis = diagnose_vmaf_params(vmaf_json_path)
                        if diagnosis["available"] and diagnosis["suggestions"]:
                            print("\n[VMAF 診斷] 參數調整建議：")
                            for s in diagnosis["suggestions"]:
                                print(f"  - {s}")
                            if preview_mode:
                                print(f'\n  下次執行加入：--vmaf-feedback "{vmaf_json_path}"')

            except Exception as e:
                print(f"\n品質驗證失敗: {e}")

        # 6. 顯示結果
        output_file = Path(output_path)
        new_size_mb = output_file.stat().st_size / (1024 * 1024)
        reduction = ((file_size_mb - new_size_mb) / file_size_mb) * 100

        print("\n" + "=" * 60)
        print("[5/5] 轉碼完成！")
        print(f"原始大小: {file_size_mb:.2f} MB")
        print(f"新檔大小: {new_size_mb:.2f} MB")
        print(f"壓縮率: {reduction:.1f}%")
        print(f"輸出檔案: {output_path}")

        # 7. 依 preview_mode 決定是否保留 vmaf json 與儲存 params
        params_path = None
        vmaf_score = (quality_scores or {}).get("vmaf", 0)

        if preview_mode:
            # 預覽模式：VMAF ≥ VMAF_GOOD_THRESHOLD 時儲存參數檔
            if vmaf_score >= VMAF_GOOD_THRESHOLD:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                params_path = str(Path(input_path).parent / f"params_{timestamp}.json")
                try:
                    with open(params_path, "w", encoding="utf-8") as f:
                        json.dump(params, f, ensure_ascii=False, indent=2)
                    print(f"\n✅ VMAF {vmaf_score:.2f} 達到 {VMAF_GOOD_THRESHOLD} 分，參數已儲存：{params_path}")
                    print(f'   套用至完整影片：python main.py {input_path} --params-file "{params_path}"')
                except Exception as e:
                    print(f"[WARN] 儲存參數失敗: {e}")
                    params_path = None
            # preview mode：vmaf_json_path 保留，供下一輪 feedback 使用
        else:
            # 完整轉檔模式：刪除 vmaf json（不需要保留）
            if vmaf_json_path:
                try:
                    Path(vmaf_json_path).unlink(missing_ok=True)
                except Exception:
                    pass
            vmaf_json_path = None

        return {
            "vmaf_json_path": vmaf_json_path,
            "quality_scores": quality_scores,
            "output_path": str(output_path),
            "params": params,
            "params_path": params_path,
        }

    def batch_process_videos(
        self,
        folder_path: str,
        pattern: str = "*.mp4",
        use_ffmpeg: bool = False,
        verify_quality: bool = True,
        quality_method: str = "psnr_ssim",
        preview_mode: bool = False,
        preview_duration: int = 30,
        auto_confirm: bool = False,
        model: str = "gpt5-mini",
        extra_prompt: str = None,
    ):
        """批次處理資料夾中的影片"""
        folder = Path(folder_path)
        video_files = list(folder.glob(pattern))

        print(f"找到 {len(video_files)} 個影片檔案")

        for video_file in tqdm(video_files, desc="批次處理", unit="個", dynamic_ncols=True):
            output_path = video_file.parent / "converted" / f"{video_file.stem}_h265{video_file.suffix}"
            output_path.parent.mkdir(exist_ok=True)

            try:
                self.process_video(
                    str(video_file),
                    str(output_path),
                    use_ffmpeg=use_ffmpeg,
                    verify_quality=verify_quality,
                    quality_method=quality_method,
                    preview_mode=preview_mode,
                    preview_duration=preview_duration,
                    auto_confirm=auto_confirm,
                    model=model,
                    extra_prompt=extra_prompt,
                )
            except Exception as e:
                tqdm.write(f"處理失敗：{e}")


def _run_workflow(args):
    """
    完整工作流程：
      Phase 1 - Auto-loop preview + VMAF 取得最佳參數
      Phase 2 - 使用最佳參數完整轉檔 + 品質驗證
      Phase 3 - 清理 preview、params、vmaf json 暫存檔案
    """
    transcoder = VideoTranscoder()
    input_path = Path(args.input)
    vmaf_subsample = args.vmaf if args.vmaf is not None else 1
    max_loop = args.auto_loop  # 預設 2

    # 追蹤需清理的暫存檔
    preview_files: list = []
    vmaf_json_files: list = []
    params_json_files: list = []

    # ── Phase 1: Auto-loop preview ──────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"[Run] Phase 1: 自動迭代尋找最佳參數（最多 {max_loop} 次）")
    print(f"{'=' * 60}")

    current_vmaf_json = None
    best_params = None

    for iteration in range(1, max_loop + 1):
        print(f"\n[Run] 第 {iteration}/{max_loop} 次迭代")

        # 讀取上一輪的 VMAF 反饋
        loop_vmaf_feedback = None
        if current_vmaf_json:
            try:
                with open(current_vmaf_json, "r", encoding="utf-8") as f:
                    vmaf_data = json.load(f)
                loop_vmaf_feedback = vmaf_data.get("pooled_metrics")
            except Exception as e:
                print(f"[Run] 無法讀取 VMAF 反饋: {e}")

        result = (
            transcoder.process_video(
                args.input,
                use_ffmpeg=args.ffmpeg,
                verify_quality=True,
                quality_method="vmaf",
                preview_mode=True,
                preview_duration=args.preview_duration,
                auto_confirm=True,
                vmaf_feedback=loop_vmaf_feedback,
                model=args.model,
                extra_prompt=getattr(args, "prompt", None),
                vmaf_subsample=vmaf_subsample,
            )
            or {}
        )

        # 追蹤此輪產生的暫存檔
        out = result.get("output_path")
        if out and Path(out).exists():
            preview_files.append(out)

        vj = result.get("vmaf_json_path")
        if vj:
            vmaf_json_files.append(vj)
            current_vmaf_json = vj

        pj = result.get("params_path")
        if pj:
            params_json_files.append(pj)

        # 持續更新最佳參數（取最後一輪的 AI 建議）
        if result.get("params"):
            best_params = result["params"]

        loop_vmaf = (result.get("quality_scores") or {}).get("vmaf", 0)
        print(f"\n[Run] 第 {iteration} 次 VMAF: {loop_vmaf:.2f}")

        if loop_vmaf >= VMAF_GOOD_THRESHOLD:
            print(f"[Run] VMAF {loop_vmaf:.2f} 已達目標 {VMAF_GOOD_THRESHOLD}，停止迭代")
            break

    if not best_params:
        print("[Run] 無法取得轉碼參數，中止工作流程")
        return

    # ── Phase 2: 完整轉檔 ───────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("[Run] Phase 2: 使用最佳參數進行完整轉檔")
    print(f"{'=' * 60}")

    # 若 Phase 1 有儲存 params_file（VMAF ≥ {VMAF_GOOD_THRESHOLD}），從檔案讀取以確認參數正確寫入
    # 否則直接使用記憶體中的 best_params
    params_for_phase2 = best_params
    if params_json_files:
        try:
            with open(params_json_files[-1], "r", encoding="utf-8") as f:
                params_for_phase2 = json.load(f)
            print(f"[Run] 讀取已驗證參數：{params_json_files[-1]}")
            print(f"  CRF: {params_for_phase2.get('recommended_crf')}  Preset: {params_for_phase2.get('preset')}")
        except Exception as e:
            print(f"[Run] 無法讀取參數檔，使用記憶體中的參數: {e}")

    output_path = str(input_path.parent / f"{input_path.stem}_h265{input_path.suffix}")

    final_result = (
        transcoder.process_video(
            args.input,
            output_path,
            use_ffmpeg=args.ffmpeg,
            verify_quality=True,
            quality_method="vmaf",
            preview_mode=False,  # 完整轉檔：不保留 vmaf json / params
            auto_confirm=True,
            model=args.model,
            extra_prompt=getattr(args, "prompt", None),
            params_override=params_for_phase2,
            vmaf_subsample=vmaf_subsample,
        )
        or {}
    )

    # ── Phase 3: 清理暫存檔案 ───────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("[Run] Phase 3: 清理暫存檔案")
    print(f"{'=' * 60}")

    for f in preview_files + vmaf_json_files + params_json_files:
        try:
            p = Path(f)
            if p.exists():
                p.unlink()
                print(f"  已刪除: {f}")
        except Exception as e:
            print(f"  [WARN] 無法刪除 {f}: {e}")

    # ── 完成摘要 ─────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("[Run] 工作流程完成！")
    print(f"[Run] 輸出檔案: {output_path}")
    final_vmaf = (final_result.get("quality_scores") or {}).get("vmaf", 0)
    if final_vmaf:
        print(f"[Run] 最終品質 VMAF: {final_vmaf:.2f}")
    print(f"{'=' * 60}")


def _run_main():
    """'run' 子命令的入口點"""
    parser = argparse.ArgumentParser(
        description="完整工作流程：自動迭代取得最佳參數 → 完整轉檔 → 品質驗證 → 清理暫存檔",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="hba run",
        epilog="""
範例:
  %(prog)s video.mp4
  %(prog)s video.mp4 --vmaf 5
  %(prog)s video.mp4 --auto-loop 3
  %(prog)s video.mp4 --vmaf 5 --model gpt-4o --prompt "優先保留細節"
        """,
    )
    parser.add_argument("input", help="輸入影片路徑")
    ffmpeg.add_to(parser)
    vmaf.add_to(parser, run_mode=True)
    auto_loop.add_to(parser, run_mode=True)
    preview.add_to(parser, include_toggle=False)
    model.add_to(parser)
    prompt.add_to(parser)
    args = parser.parse_args()
    _run_workflow(args)


def _legacy_main():
    """原有指令入口點"""
    parser = argparse.ArgumentParser(
        description="AI 影片轉碼工具 (Copilot SDK 版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 基本使用
  %(prog)s video.mp4

  # 預覽模式（只轉換前 30 秒，儲存 vmaf json 與 params）
  %(prog)s video.mp4 --preview --vmaf

  # 完整工作流程（自動迭代 + 轉檔 + 清理）
  %(prog)s run video.mp4

  # 使用 FFmpeg + 預覽
  %(prog)s video.mp4 --ffmpeg --preview

  # 批次處理 + 預覽模式
  %(prog)s ./videos/ --batch --preview
        """,
    )
    parser.add_argument("input", help="輸入影片路徑或資料夾")
    batch.add_to(parser)
    ffmpeg.add_to(parser)
    verify.add_to(parser)
    vmaf.add_to(parser)
    preview.add_to(parser)
    yes.add_to(parser)
    vmaf_feedback.add_to(parser)
    model.add_to(parser)
    auto_loop.add_to(parser)
    prompt.add_to(parser)
    params_file.add_to(parser)
    args = parser.parse_args()

    transcoder = VideoTranscoder()
    method = "vmaf" if args.vmaf is not None else "psnr_ssim"
    do_verify = not args.no_verify
    vmaf_subsample = args.vmaf if args.vmaf is not None else 1

    # 讀取 --params-file
    params_override = None
    if args.params_file:
        try:
            with open(args.params_file, "r", encoding="utf-8") as f:
                params_override = json.load(f)
            print(f"[Params] 載入參數檔案：{args.params_file}")
            print(f"  CRF: {params_override.get('recommended_crf')}  Preset: {params_override.get('preset')}")
        except Exception as e:
            print(f"[Params] 無法讀取 {args.params_file}: {e}，改用 AI 分析")

    # 讀取 --vmaf-feedback
    feedback_data = None
    if args.vmaf_feedback:
        try:
            with open(args.vmaf_feedback, "r", encoding="utf-8") as f:
                vmaf_json = json.load(f)
            feedback_data = vmaf_json.get("pooled_metrics")
            if feedback_data:
                print(f"[VMAF 反饋] 讀取 {args.vmaf_feedback}，AI 將依品質指標調整參數")
            else:
                print(f"[VMAF 反饋] {args.vmaf_feedback} 中找不到 pooled_metrics，使用預設分析")
        except Exception as e:
            print(f"[VMAF 反饋] 無法讀取 {args.vmaf_feedback}: {e}，使用預設分析")

    if args.auto_loop is not None:
        # --auto-loop 模式：自動連續執行 preview + VMAF
        max_iterations = args.auto_loop
        print(f"\n[Auto Loop] 啟動自動迭代模式，最多執行 {max_iterations} 次")
        print("[Auto Loop] 每次均以 preview 模式 + VMAF 驗證執行")
        print("=" * 60)

        current_vmaf_json = args.vmaf_feedback if args.vmaf_feedback else None

        for iteration in range(1, max_iterations + 1):
            print(f"\n{'=' * 60}")
            print(f"[Auto Loop] 第 {iteration}/{max_iterations} 次迭代")
            print(f"{'=' * 60}")

            loop_vmaf_feedback = None
            if current_vmaf_json:
                try:
                    with open(current_vmaf_json, "r", encoding="utf-8") as f:
                        vmaf_json_data = json.load(f)
                    loop_vmaf_feedback = vmaf_json_data.get("pooled_metrics")
                    if loop_vmaf_feedback:
                        print(f"[Auto Loop] 使用 VMAF 反饋: {current_vmaf_json}")
                    else:
                        print(f"[Auto Loop] {current_vmaf_json} 中找不到 pooled_metrics，跳過反饋")
                except Exception as e:
                    print(f"[Auto Loop] 無法讀取 VMAF 反饋: {e}")

            result = (
                transcoder.process_video(
                    args.input,
                    use_ffmpeg=args.ffmpeg,
                    verify_quality=True,
                    quality_method="vmaf",
                    preview_mode=True,
                    preview_duration=args.preview_duration,
                    auto_confirm=args.yes,
                    vmaf_feedback=loop_vmaf_feedback,
                    model=args.model,
                    extra_prompt=args.prompt,
                    vmaf_subsample=vmaf_subsample,
                )
                or {}
            )

            new_vmaf_path = result.get("vmaf_json_path")
            if new_vmaf_path:
                current_vmaf_json = new_vmaf_path
                print(f"\n[Auto Loop] 第 {iteration} 次完成，vmaf.json: {current_vmaf_json}")
            else:
                print(f"\n[Auto Loop] 第 {iteration} 次完成，未取得 vmaf.json")

            loop_vmaf = (result.get("quality_scores") or {}).get("vmaf", 0)
            if loop_vmaf >= VMAF_GOOD_THRESHOLD:
                print(f"\n[Auto Loop] VMAF {loop_vmaf:.2f} 已達目標 {VMAF_GOOD_THRESHOLD}，提前停止迭代")
                if result.get("params_path"):
                    print(f"[Auto Loop] 最佳參數已儲存：{result['params_path']}")
                break

        print("\n[Auto Loop] 迭代完成")
        print(f"{'=' * 60}")

    elif args.batch:
        transcoder.batch_process_videos(
            args.input,
            use_ffmpeg=args.ffmpeg,
            verify_quality=do_verify,
            quality_method=method,
            preview_mode=args.preview,
            preview_duration=args.preview_duration,
            auto_confirm=args.yes,
            model=args.model,
            extra_prompt=args.prompt,
        )
    else:
        transcoder.process_video(
            args.input,
            use_ffmpeg=args.ffmpeg,
            verify_quality=do_verify,
            quality_method=method,
            preview_mode=args.preview,
            preview_duration=args.preview_duration,
            auto_confirm=args.yes,
            vmaf_feedback=feedback_data,
            model=args.model,
            extra_prompt=args.prompt,
            params_override=params_override,
            vmaf_subsample=vmaf_subsample,
        )


def main():
    """主程式入口點，支援 'run' 子命令"""
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        # 移除 'run'，讓 _run_main 的 parser 只看到後面的參數
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        _run_main()
    else:
        _legacy_main()


if __name__ == "__main__":
    main()
