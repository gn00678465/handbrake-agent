import argparse
from pathlib import Path
from typing import Dict, Any
from tools.video_info import get_video_info_ffprobe
from tools.transcoder import transcode_with_ffmpeg, transcode_with_handbrake
from tools.quality import calculate_vmaf, calculate_psnr_ssim, evaluate_quality, diagnose_vmaf_params
from tools.ai_analyzer import analyze_video

class VideoTranscoder:
    """影片轉碼器，整合 AI 分析與品質驗證"""
    
    def process_video(
        self,
        input_path: str,
        output_path: str = None,
        use_ffmpeg: bool = False,
        verify_quality: bool = True,
        quality_method: str = 'psnr_ssim',
        preview_mode: bool = False,
        preview_duration: int = 30,
        auto_confirm: bool = False,
        vmaf_feedback: Dict[str, Any] = None
    ):
        """
        完整的影片處理流程

        Args:
            input_path: 輸入影片路徑
            output_path: 輸出影片路徑
            use_ffmpeg: 使用 FFmpeg 而非 HandBrake
            verify_quality: 是否進行品質驗證
            quality_method: 品質驗證方法 ('vmaf' 或 'psnr_ssim')
            preview_mode: 預覽模式，只轉換部分影片
            preview_duration: 預覽模式的時長（秒）
        """
        
        input_file = Path(input_path)
        if not output_path:
            suffix = "_preview" if preview_mode else "_h265"
            output_path = input_file.parent / f"{input_file.stem}{suffix}{input_file.suffix}"

        mode_text = f"【預覽模式 - {preview_duration}秒】" if preview_mode else ""
        print(f"處理影片：{input_path} {mode_text}")
        print("=" * 60)
        
        # 1. 取得影片資訊
        print("\n[1/5] 取得影片資訊...")
        video_info = get_video_info_ffprobe(input_path)
        file_size_mb = input_file.stat().st_size / (1024 * 1024)
        
        # 2. LLM 分析
        print("\n[2/5] 使用 AI 分析最佳轉碼參數 (GitHub Copilot SDK)...")
        try:
            params = analyze_video(video_info, file_size_mb, vmaf_feedback)
        except Exception as e:
            print(f"AI 分析失敗: {e}")
            return
        
        print(f"\n建議參數：")
        print(f"  CRF: {params.get('recommended_crf')}")
        print(f"  Preset: {params.get('preset')}")
        print(f"  解析度: {params.get('resolution')}")
        print(f"  音訊位元率: {params.get('audio_bitrate')}")
        print(f"  預估壓縮: {params.get('estimated_size_reduction')}")
        print(f"  理由: {params.get('reasoning')}")
        
        # 3. 確認執行
        if auto_confirm:
            print("\n自動確認執行轉碼 (--yes)")
        else:
            try:
                confirm = input("\n是否執行轉碼？(y/n): ")
            except EOFError:
                confirm = 'y'
            if confirm.lower() != 'y':
                print("取消轉碼")
                return
        
        # 4. 執行轉碼
        transcode_text = f"[3/5] 執行轉碼（預覽前 {preview_duration} 秒）..." if preview_mode else "[3/5] 執行轉碼..."
        print(f"\n{transcode_text}")
        if use_ffmpeg:
            success = transcode_with_ffmpeg(
                input_path,
                str(output_path),
                params,
                duration_limit=preview_duration if preview_mode else None
            )
        else:
            success = transcode_with_handbrake(
                input_path,
                str(output_path),
                params,
                duration_limit=preview_duration if preview_mode else None
            )
        
        if not success:
            print("\n轉碼失敗！")
            return
        
        # 5. 品質驗證
        quality_scores = None
        if verify_quality:
            print("\n[4/5] 品質驗證...")
            try:
                if quality_method == 'vmaf':
                    quality_scores = calculate_vmaf(input_path, str(output_path))
                else:
                    quality_scores = calculate_psnr_ssim(input_path, str(output_path))

                evaluation = evaluate_quality(quality_scores)

                print("\n品質評估結果：")
                for detail in evaluation['details']:
                    print(f"  {detail}")
                print(f"  整體評價: {evaluation['overall']}")

                # VMAF 分數不佳時，從 vmaf_timestamp.json sub-metrics 給出參數調整建議
                if quality_method == 'vmaf' and quality_scores.get('vmaf', 100) < 70:
                    vmaf_json_path = quality_scores.get('_vmaf_json_path', '')
                    if vmaf_json_path:
                        diagnosis = diagnose_vmaf_params(vmaf_json_path)
                        if diagnosis['available'] and diagnosis['suggestions']:
                            print("\n[VMAF 診斷] 參數調整建議：")
                            for s in diagnosis['suggestions']:
                                print(f"  - {s}")
                            print(f"\n  下次執行加入：--vmaf-feedback \"{vmaf_json_path}\"")
                
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

    def batch_process_videos(
        self,
        folder_path: str,
        pattern: str = "*.mp4",
        use_ffmpeg: bool = False,
        verify_quality: bool = True,
        quality_method: str = 'psnr_ssim',
        preview_mode: bool = False,
        preview_duration: int = 30,
        auto_confirm: bool = False
    ):
        """批次處理資料夾中的影片"""
        folder = Path(folder_path)
        video_files = list(folder.glob(pattern))
        
        print(f"找到 {len(video_files)} 個影片檔案")
        
        for i, video_file in enumerate(video_files, 1):
            print(f"\n{'='*60}")
            print(f"處理第 {i}/{len(video_files)} 個影片")
            print(f"{'='*60}")
            
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
                    auto_confirm=auto_confirm
                )
            except Exception as e:
                print(f"處理失敗：{e}")

def main():
    """主程式入口點"""
    parser = argparse.ArgumentParser(
        description="AI 影片轉碼工具 (Copilot SDK 版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 基本使用
  %(prog)s video.mp4

  # 預覽模式（只轉換前 30 秒）
  %(prog)s video.mp4 --preview

  # 自訂預覽時長（60 秒）
  %(prog)s video.mp4 --preview --preview-duration 60

  # 使用 FFmpeg + 預覽
  %(prog)s video.mp4 --ffmpeg --preview

  # 批次處理 + 預覽模式
  %(prog)s ./videos/ --batch --preview
        """
    )
    parser.add_argument("input", help="輸入影片路徑或資料夾")
    parser.add_argument("--batch", action="store_true", help="批次處理模式")
    parser.add_argument("--ffmpeg", action="store_true", help="使用 FFmpeg 而非 HandBrake")
    parser.add_argument("--no-verify", action="store_true", help="停用品質驗證")
    parser.add_argument("--vmaf", action="store_true", help="使用 VMAF 驗證")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="預覽模式：只轉換影片開頭部分以快速測試參數（預設 30 秒）"
    )
    parser.add_argument(
        "--preview-duration",
        type=int,
        default=30,
        metavar="SECONDS",
        help="預覽模式的時長（秒），預設為 30 秒"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="自動確認執行轉碼，不需要手動輸入 y/n"
    )
    parser.add_argument(
        "--vmaf-feedback",
        metavar="VMAF_JSON",
        help="提供上次轉碼的 vmaf.json 路徑，讓 AI 依據品質指標調整參數建議"
    )

    args = parser.parse_args()

    transcoder = VideoTranscoder()

    method = 'vmaf' if args.vmaf else 'psnr_ssim'
    verify = not args.no_verify

    # 讀取 vmaf feedback 檔案（若有提供）
    vmaf_feedback = None
    if args.vmaf_feedback:
        import json as _json
        try:
            with open(args.vmaf_feedback, "r", encoding="utf-8") as f:
                vmaf_json = _json.load(f)
            vmaf_feedback = vmaf_json.get("pooled_metrics")
            if vmaf_feedback:
                print(f"[VMAF 反饋] 讀取 {args.vmaf_feedback}，AI 將依據品質指標調整參數")
            else:
                print(f"[VMAF 反饋] {args.vmaf_feedback} 中找不到 pooled_metrics，使用預設分析")
        except Exception as e:
            print(f"[VMAF 反饋] 無法讀取 {args.vmaf_feedback}: {e}，使用預設分析")

    if args.batch:
        transcoder.batch_process_videos(
            args.input,
            use_ffmpeg=args.ffmpeg,
            verify_quality=verify,
            quality_method=method,
            preview_mode=args.preview,
            preview_duration=args.preview_duration,
            auto_confirm=args.yes
        )
    else:
        transcoder.process_video(
            args.input,
            use_ffmpeg=args.ffmpeg,
            verify_quality=verify,
            quality_method=method,
            preview_mode=args.preview,
            preview_duration=args.preview_duration,
            auto_confirm=args.yes,
            vmaf_feedback=vmaf_feedback
        )

if __name__ == "__main__":
    main()
