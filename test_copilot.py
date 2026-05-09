#!/usr/bin/env python3
"""
測試 GitHub Copilot SDK 整合

此腳本驗證 Copilot SDK 是否正確安裝並可以正常運作。
"""

import asyncio

from copilot import CopilotClient
from copilot.session import PermissionHandler


async def test_copilot_connection():
    """測試 Copilot SDK 連接"""
    print("🔄 測試 GitHub Copilot SDK 連接...")

    try:
        # 初始化客戶端
        client = CopilotClient()
        print("✓ Copilot 客戶端已創建")

        # 啟動客戶端
        await client.start()
        print("✓ Copilot 客戶端已啟動")

        # 創建會話
        session = await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model="claude-sonnet-4.5",
            streaming=False,
        )
        print("✓ 會話已創建")

        print("\n📤 發送測試訊息...")
        result = await session.send_and_wait("請用一句話說明 H.265 編碼的優勢。", timeout=120.0)
        final_content = ""
        if result is not None:
            content = getattr(getattr(result, "data", None), "content", None)
            if isinstance(content, str):
                final_content = content

        print("\n📨 收到回應：")
        print(f"{final_content}\n")

        # 清理資源
        await session.destroy()
        print("✓ 會話已銷毀")

        await client.stop()
        print("✓ Copilot 客戶端已停止")

        print("\n✅ 所有測試通過！GitHub Copilot SDK 運作正常。")
        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        print("\n故障排除建議：")
        print("1. 確認已安裝 github-copilot-sdk: pip install github-copilot-sdk")
        print("2. 確認已安裝 Copilot CLI: copilot --version")
        print("3. 確認已登入 Copilot: copilot login")
        print("4. 確認有有效的 GitHub Copilot 訂閱")
        return False


async def test_ai_analyzer():
    """測試 AI 分析器模組"""
    print("\n" + "=" * 60)
    print("🔄 測試 AI 影片分析器...")
    print("=" * 60)

    try:
        from tools.ai_analyzer import analyze_video

        # 模擬影片資訊
        test_video_info = {
            "format": "mp4",
            "duration": 120.5,
            "bit_rate": 5000000,
            "size": 75000000,
            "video": {
                "codec": "h264",
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "bit_rate": 4500000,
                "pix_fmt": "yuv420p",
            },
            "audio": {
                "codec": "aac",
                "sample_rate": 48000,
                "channels": 2,
                "bit_rate": 128000,
            },
        }

        file_size_mb = 71.5

        print("\n測試影片資訊：")
        print("  解析度: 1920x1080")
        print("  編碼: H.264")
        print("  時長: 120.5 秒")
        print("  檔案大小: 71.5 MB")

        print("\n📤 請求 AI 分析...")
        result = analyze_video(test_video_info, file_size_mb)

        print("\n📨 AI 建議參數：")
        print(f"  CRF: {result.get('recommended_crf')}")
        print(f"  Preset: {result.get('preset')}")
        print(f"  解析度: {result.get('resolution')}")
        print(f"  音訊位元率: {result.get('audio_bitrate')}")
        print(f"  預估壓縮: {result.get('estimated_size_reduction')}")
        print(f"  理由: {result.get('reasoning')}")

        print("\n✅ AI 分析器測試通過！")
        return True

    except Exception as e:
        print(f"\n❌ AI 分析器測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主測試函數"""
    print("=" * 60)
    print("GitHub Copilot SDK 整合測試")
    print("=" * 60)

    # 測試 1: 基本連接
    test1_passed = await test_copilot_connection()

    # 測試 2: AI 分析器
    test2_passed = await test_ai_analyzer()

    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"基本連接測試: {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"AI 分析器測試: {'✅ 通過' if test2_passed else '❌ 失敗'}")

    if test1_passed and test2_passed:
        print("\n🎉 所有測試通過！專案已成功遷移到 GitHub Copilot SDK。")
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤訊息。")


if __name__ == "__main__":
    asyncio.run(main())
