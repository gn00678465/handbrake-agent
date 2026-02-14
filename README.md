# HandBrake Agent - AI 影片轉碼工具

使用 GitHub Copilot SDK 提供 AI 驅動的影片轉碼參數優化建議。

**版本：** 1.1.0
**狀態：** ✅ 生產就緒

---

## 目錄

- [功能特點](#功能特點)
- [快速開始](#快速開始-5-分鐘上手)
- [系統需求](#系統需求)
- [安裝](#安裝)
- [CLI 工具安裝](#-cli-工具安裝可選)
- [使用方法](#使用方法)
  - [run 子命令](#run-子命令一鍵完整工作流程)
- [專案結構](#專案結構)
- [套件管理](#套件管理-uv)
- [測試](#測試)
- [常見問題](#常見問題)
- [故障排除](#故障排除)
- [技術細節](#技術細節)
- [參考資料](#參考資料)

## 📚 其他文檔

- [NEW_FEATURES.md](NEW_FEATURES.md) - 新功能詳細說明（預覽模式 + CLI 工具化）
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速參考指南
- [demo_preview.py](demo_preview.py) - 預覽模式演示腳本

---

## 功能特點

- 🤖 **AI 參數優化**：使用 GitHub Copilot SDK (Claude Sonnet 4.5) 分析影片特性，自動建議最佳轉碼參數
- 📊 **品質驗證**：支援 VMAF、PSNR、SSIM 等品質評估指標
- ⚡ **多工具支援**：支援 FFmpeg 和 HandBrake 兩種轉碼工具
- 📦 **批次處理**：可批次處理資料夾中的多個影片
- 🎬 **預覽模式**：只轉換前 30 秒快速測試參數，大幅節省時間
- 🔧 **CLI 工具**：可安裝為全域命令，隨時隨地使用
- 🔒 **可重現建置**：使用 uv 套件管理器確保環境一致性
- 🚀 **快速安裝**：使用 uv 安裝速度提升 10-100x

---

## 快速開始（5 分鐘上手）

### 第 1 步：安裝依賴

```bash
# 使用 uv（推薦，更快速）
uv pip install -r requirements.lock

# 或使用傳統 pip
pip install -r requirements.txt
```

### 第 2 步：確認 Copilot CLI

```bash
# 檢查 Copilot CLI 是否已安裝
copilot --version

# 如果未登入，執行登入
copilot login
```

### 第 3 步：執行測試

```bash
# 測試 Copilot SDK 整合
python test_copilot.py
```

如果看到 `✅ 所有測試通過！`，表示設定成功！

### 第 4 步：轉碼影片

```bash
# 基本使用
python main.py your_video.mp4

# 預覽模式（只轉換前 30 秒，快速測試參數）⭐ 推薦
python main.py your_video.mp4 --preview

# 使用 FFmpeg（而非 HandBrake）
python main.py your_video.mp4 --ffmpeg

# 跳過品質驗證（更快）
python main.py your_video.mp4 --no-verify

# 批次處理
python main.py /path/to/videos/ --batch
```

### 第 5 步：安裝為全域命令（可選）

```bash
# 開發模式（類似 pnpm link）
uv pip install -e .

# 然後可以直接使用
handbrake-agent video.mp4 --preview
hba video.mp4 --preview  # 簡短別名

# 或使用 uv tool 全域安裝
uv tool install .
```

---

## 系統需求

### 必需工具

1. **Python 3.8+**（推薦 3.13）

2. **GitHub Copilot CLI**
   ```bash
   # 安裝參考: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli

   # 驗證安裝
   copilot --version
   ```

3. **FFmpeg**
   ```bash
   # Windows (使用 winget)
   winget install ffmpeg

   # macOS (使用 Homebrew)
   brew install ffmpeg

   # Linux (Ubuntu/Debian)
   sudo apt install ffmpeg
   ```

4. **HandBrake CLI**（可選，也可只使用 FFmpeg）
   ```bash
   # 下載地址: https://handbrake.fr/downloads.php
   ```

---

## 安裝

### 方法 1: 使用 uv（推薦，更快速）

#### 安裝 uv

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 驗證安裝
uv --version
```

#### 安裝專案依賴

```bash
# 使用鎖定文件（推薦，確保可重現性）
uv pip install -r requirements.lock

# 或使用簡化版本
uv pip install -r requirements.txt
```

**uv 優勢：**
- ⚡ 10-100x 更快的安裝速度
- 🔒 可重現的建置（requirements.lock）
- 🎯 更好的依賴解析
- 📦 完全兼容 pip

### 方法 2: 使用 pip（傳統方式）

```bash
pip install -r requirements.txt
```

### 完成安裝

確認 GitHub Copilot CLI 已登入：

```bash
copilot login
```

---

## 🔧 CLI 工具安裝（可選）

將 HandBrake Agent 安裝為全域命令，可以在任何地方使用。安裝後提供兩個等價命令：

- `handbrake-agent` — 完整命令名
- `hba` — 簡短別名

### 全域安裝（推薦）

使用 `uv tool` 安裝到獨立的全域環境，與系統 Python 完全隔離：

```bash
# 首次安裝
uv tool install .

# 驗證安裝
hba --version
# handbrake-agent 1.1.0

# 使用命令（任何目錄皆可）
hba video.mp4 --preview --vmaf --yes
handbrake-agent video.mp4 run
```

### 更新全域安裝

取得新版本後重新安裝：

```bash
# 拉取最新程式碼
git pull

# 重新安裝（覆蓋舊版本）
uv tool install --reinstall .

# 確認版本已更新
hba --version
```

> ⚠️ **若 `hba --version` 仍顯示舊版本**，表示 PATH 中存在另一個舊版執行檔（通常來自先前執行過 `uv pip install -e .`，安裝至系統 Python 的 Scripts 目錄）。
>
> **診斷方式：**
> ```powershell
> where hba
> # 若出現兩個路徑，例如：
> # C:\Users\<user>\AppData\Local\Programs\Python\Python313\Scripts\hba.exe  ← 舊版（優先）
> # C:\Users\<user>\.local\bin\hba.exe                                        ← uv tool 新版
> ```
>
> **解決方式（PowerShell）：**
> ```powershell
> Remove-Item "$env:LOCALAPPDATA\Programs\Python\Python313\Scripts\hba.exe"
> Remove-Item "$env:LOCALAPPDATA\Programs\Python\Python313\Scripts\handbrake-agent.exe"
> ```
> 移除後重開終端機，再次執行 `hba --version` 確認。

### 開發模式安裝（適合修改源碼）

安裝為可編輯模式，修改代碼後立即生效，無需重新安裝：

```bash
uv pip install -e .

# 現在可以直接使用命令
hba --help
```

> ⚠️ **注意**：`uv pip install -e .` 會將 `hba` / `handbrake-agent` 安裝至系統 Python 的 Scripts 目錄。若之後改用 `uv tool install .` 進行全域安裝，請先手動移除 Scripts 目錄中的舊版執行檔，避免 PATH 衝突（參見上方「更新全域安裝」的注意事項）。

### 卸載

```bash
uv tool uninstall handbrake-agent
```

### 使用 uvx（免安裝，臨時執行）

```bash
uvx --from . handbrake-agent video.mp4 --preview
```

---

## 使用方法

### 基本使用

轉碼單個影片：
```bash
python main.py input_video.mp4

# 或使用全域命令（安裝後）
handbrake-agent input_video.mp4
hba input_video.mp4  # 簡短別名
```

### 🎬 預覽模式（推薦用於測試）

預覽模式只轉換影片開頭部分，讓你快速測試參數效果：

```bash
# 預覽模式（預設 30 秒）
python main.py input_video.mp4 --preview

# 自訂預覽時長（60 秒）
python main.py input_video.mp4 --preview --preview-duration 60

# 預覽 + FFmpeg
python main.py input_video.mp4 --preview --ffmpeg

# 預覽 + 跳過驗證（最快）
python main.py input_video.mp4 --preview --no-verify

# 批次預覽
python main.py ./videos/ --batch --preview
```

**預覽模式優勢：**
- ⚡ **快速測試**：30 秒即可看到效果，無需等待完整轉碼
- 🎯 **精確調整**：根據預覽結果調整參數
- 💾 **節省空間**：預覽檔案很小
- 🔄 **迭代優化**：快速測試不同參數組合

**推薦工作流程：**
1. 使用 `--preview` 測試參數
2. 檢查預覽結果品質和壓縮率
3. 滿意後移除 `--preview` 進行完整轉碼

### 進階選項

```bash
# 使用 FFmpeg 而非 HandBrake
uv run main.py input_video.mp4 --ffmpeg

# 停用品質驗證（加快處理速度）
uv run main.py input_video.mp4 --no-verify

# 啟用 VMAF 品質驗證（逐幀精確）
uv run main.py input_video.mp4 --vmaf

# 啟用 VMAF 並設定取樣間隔（每 5 幀取樣，速度約 5x，誤差 ±1-2 分）
uv run main.py input_video.mp4 --vmaf 5

# 批次處理資料夾中的所有影片
uv run main.py /path/to/videos/ --batch

# 自動確認（不需要手動輸入 y/n）
uv run main.py input.mp4 --yes

# 指定 AI 模型
uv run main.py input.mp4 --model gpt-4o

# 附加自訂 prompt 引導 AI 分析
uv run main.py input.mp4 --prompt "這是動畫內容，優先保留色彩純度"

# 非互動式執行（CI/腳本環境適用）
uv run main.py input.mp4 --preview --ffmpeg --no-verify --yes

# AI 參數精調：提供上次的 vmaf.json，讓 AI 依品質指標調整參數
uv run main.py input.mp4 --preview --yes --vmaf-feedback vmaf.json

# 載入先前儲存的 params.json，略過 AI 分析直接轉碼
uv run main.py input.mp4 --params-file params_20260214_120000.json --yes

# 自動迭代優化（最多 3 次 preview + VMAF，自動停止）
uv run main.py input.mp4 --auto-loop --preview --vmaf --yes

# 指定最多迭代 2 次
uv run main.py input.mp4 --auto-loop 2 --preview --vmaf --yes
```

### 完整參數說明

```
uv run main.py --help

positional arguments:
  input                      輸入影片路徑或資料夾

options:
  --batch                    批次處理模式
  --ffmpeg                   使用 FFmpeg 而非 HandBrake
  --no-verify                停用品質驗證
  --vmaf [N]                 啟用 VMAF 品質驗證
                               不帶數字：N=1，逐幀精確
                               --vmaf 5：每 5 幀取樣，速度 ~5x，誤差 ±1-2 分
  --preview                  預覽模式：只轉換影片開頭部分
                               （vmaf json 與 params 僅在此模式下保留）
  --preview-duration SECONDS 預覽模式的時長（秒，預設 30 秒）
  --yes, -y                  自動確認執行轉碼，不需要手動輸入 y/n
  --vmaf-feedback VMAF_JSON  提供上次轉碼的 vmaf.json，讓 AI 依品質指標調整參數建議
  --model MODEL              指定 AI 模型（預設：gpt5-mini）
  --auto-loop [N]            自動連續執行 preview + VMAF 迭代
                               不帶數字：預設執行 3 次
                               --auto-loop 2：最多執行 2 次
  --prompt TEXT, -p TEXT     附加自訂提示詞，會加在 AI 分析 prompt 後面
  --params-file PARAMS_JSON  載入先前儲存的 params.json，略過 AI 分析
```

### run 子命令（一鍵完整工作流程）

`run` 子命令整合三個階段，適合直接得到最終結果：

**Phase 1**：自動迭代 preview + VMAF，找到最佳參數
**Phase 2**：使用最佳參數進行完整轉檔 + 品質驗證
**Phase 3**：清理所有暫存檔（preview、vmaf json、params json）

```bash
# 最簡用法（預設 2 次迭代）
uv run main.py run video.mp4

# 使用全域命令
hba run video.mp4

# 指定 VMAF 取樣間隔（加速驗證）
hba run video.mp4 --vmaf 5

# 指定最多迭代次數
hba run video.mp4 --auto-loop 3

# 組合使用
hba run video.mp4 --vmaf 5 --model gpt-4o --prompt "優先保留細節"
```

```
uv run main.py run --help

positional arguments:
  input                      輸入影片路徑

options:
  --ffmpeg                   使用 FFmpeg 而非 HandBrake
  --vmaf [N]                 VMAF 取樣間隔（不帶數字=1 逐幀；--vmaf 5 每 5 幀）
  --auto-loop N              Preview 迭代次數（預設 2）
  --preview-duration SECONDS 預覽時長（秒，預設 30 秒）
  --model MODEL              指定 AI 模型（預設：gpt5-mini）
  --prompt TEXT, -p TEXT     附加自訂提示詞
```

### 工作流程

1. **影片分析** → 使用 ffprobe 取得影片詳細資訊
2. **AI 建議** → 透過 GitHub Copilot SDK 分析並建議最佳參數
3. **使用者確認** → 顯示建議參數，等待使用者確認
4. **執行轉碼** → 使用選定的工具（FFmpeg 或 HandBrake）進行轉碼
5. **品質驗證** → 計算轉碼後影片的品質指標
6. **結果報告** → 顯示壓縮率和品質評估結果

### AI 參數精調工作流程（`--vmaf-feedback`）

當 VMAF 分數不佳時，可將 `vmaf.json` 回饋給 AI，讓它依據 sub-metrics 自動調整參數：

```bash
# 第一輪：使用預設參數轉碼並產生 vmaf.json
hba video.mp4 --preview --vmaf --yes

# 查看 VMAF 診斷建議（分數 < 70 時自動顯示）
# 範例輸出：
#   [VMAF 診斷] 參數調整建議：
#     - VIF-scale0=0.644 -> 輕度 blocking/banding，建議 CRF 降低 2-3
#     - ADM2=0.878 -> 輕度邊緣模糊，建議改用 slow 或 slower preset

# 第二輪：帶入 vmaf.json，AI 自動依指標調整參數
hba video.mp4 --preview --vmaf --yes --vmaf-feedback vmaf.json

# 確認改善後，移除 --preview 進行完整轉碼
hba video.mp4 --vmaf --yes --vmaf-feedback vmaf.json

# 或直接使用 run 子命令（自動完成以上所有步驟）
hba run video.mp4 --vmaf 5
```

**AI 依據 VMAF sub-metrics 的調整邏輯：**

| Sub-metric | 閾值 | 問題 | AI 調整方向 |
|-----------|------|------|------------|
| VIF scale0 | < 0.70 | 方塊感／色帶 | CRF 降低 2-3 |
| ADM2 | < 0.88 | 邊緣模糊 | 改用 slow/slower preset |
| ADM scale3 | < 0.85 | 細部細節損失 | slower preset 或 CRF -2 |
| motion2 | > 4.0 | 高動態場景 | CRF -2 + slower preset |

未提供 `--vmaf-feedback` 時，行為與原本完全相同，使用影片資訊進行預設分析。

---

## 專案結構

```
handbrake-agent/
├── 核心程式
│   ├── main.py                  # 主程式入口
│   └── tools/                   # 工具模組
│       ├── __init__.py
│       ├── video_info.py        # 影片資訊提取（ffprobe）
│       ├── transcoder.py        # 轉碼工具（FFmpeg/HandBrake）
│       ├── quality.py           # 品質評估（VMAF/PSNR/SSIM）
│       └── ai_analyzer.py       # AI 分析（GitHub Copilot SDK）
│
├── 配置文件
│   ├── pyproject.toml           # 專案元數據和依賴（uv）
│   ├── requirements.txt         # 簡化依賴列表（pip 兼容）
│   ├── requirements.lock        # 鎖定的完整依賴樹（uv）
│   └── .python-version          # Python 版本規範
│
├── 測試
│   └── test_copilot.py          # Copilot SDK 整合測試
│
└── 文檔
    └── README.md                # 本文件
```

---

## 套件管理 (uv)

本專案使用 **uv** 作為推薦的 Python 套件管理器，用 Rust 編寫，提供極快的安裝速度。

### 為什麼選擇 uv？

- ⚡ **10-100x 更快**的套件安裝速度
- 🔒 **可重現的建置**：使用 lock 檔案確保一致性
- 🎯 **更好的依賴解析**：避免衝突
- 📦 **完全兼容 pip**：可以替代 pip 使用
- 🚀 **零配置**：開箱即用

### 常用命令

#### 安裝依賴

```bash
# 基本安裝
uv pip install -r requirements.txt

# 使用鎖定文件（推薦，確保可重現性）
uv pip install -r requirements.lock

# 從 pyproject.toml 安裝
uv pip install -e .
```

#### 更新依賴

```bash
# 更新所有套件到最新版本
uv pip install --upgrade -r requirements.txt

# 重新生成 lock 文件
uv pip compile pyproject.toml -o requirements.lock

# 更新特定套件
uv pip install --upgrade github-copilot-sdk
```

#### 查看已安裝套件

```bash
# 列出所有套件
uv pip list

# 查看套件資訊
uv pip show github-copilot-sdk

# 檢查套件版本
uv pip list | grep copilot
```

#### 建立虛擬環境

```bash
# 建立虛擬環境
uv venv

# 啟動虛擬環境（Windows）
.venv\Scripts\activate

# 啟動虛擬環境（macOS/Linux）
source .venv/bin/activate

# 在虛擬環境中安裝依賴
uv pip install -r requirements.lock
```

### 性能比較

實際測試（本專案，8 個套件）：

| 操作 | pip | uv | 速度提升 |
|------|-----|----|----|
| 安裝依賴 | ~5s | ~0.5s | **10x** ⚡ |
| 重新安裝 | ~5s | ~0.1s | **50x** ⚡ |
| 依賴解析 | ~3s | ~0.3s | **10x** ⚡ |

### 向後兼容性

✅ **完全兼容 pip**

如果不想使用 uv，仍然可以使用傳統的 pip：

```bash
pip install -r requirements.txt
```

所有功能保持不變。

---

## 測試

### 執行測試套件

```bash
# Copilot SDK 整合測試
python test_copilot.py
```

### 測試內容

測試腳本會驗證：

1. ✅ Copilot SDK 基本連接
2. ✅ 會話創建和管理
3. ✅ 事件處理機制
4. ✅ AI 分析器功能
5. ✅ 錯誤處理和容錯

### 預期輸出

```
===========================================================
GitHub Copilot SDK 整合測試
===========================================================
🔄 測試 GitHub Copilot SDK 連接...
✓ Copilot 客戶端已創建
✓ Copilot 客戶端已啟動
✓ 會話已創建

📤 發送測試訊息...

📨 收到回應：
[AI 的回應內容...]

✓ 會話已銷毀
✓ Copilot 客戶端已停止

✅ 所有測試通過！GitHub Copilot SDK 運作正常。
```

---

## 常見問題

### Q: 為什麼選擇 GitHub Copilot SDK？

**A:** GitHub Copilot SDK 提供：
- 統一的 AI 模型存取介面
- 自動的生命週期管理
- 內建工具呼叫支援
- 更好的開發體驗
- 無需管理 API Key（使用現有的 Copilot 訂閱）

### Q: 品質驗證會花很長時間嗎？

**A:**
- **PSNR/SSIM**：通常較快（10-30 秒，取決於影片長度）
- **VMAF**：較慢但更準確（1-5 分鐘）
- 可使用 `--no-verify` 跳過驗證以加快處理速度

### Q: 如何選擇 FFmpeg 或 HandBrake？

**A:**
- **HandBrake**（預設）：專為影片轉碼優化，參數調整更直觀
- **FFmpeg**：更通用且功能更多，支援更多格式和選項
- 建議先試用 HandBrake，如遇問題可改用 `--ffmpeg`

### Q: 需要 GitHub Copilot 訂閱嗎？

**A:** 是的，需要有效的 GitHub Copilot 訂閱（Pro, Pro+, Business 或 Enterprise）。

### Q: 是否必須使用 uv？

**A:** 不是必須的。uv 是推薦選項，但專案完全支援傳統的 `pip install -r requirements.txt`。

### Q: 支援哪些影片格式？

**A:** 支援所有 FFmpeg 支援的格式，包括但不限於：MP4, MKV, AVI, MOV, WMV, FLV 等。

---

## 故障排除

### Copilot SDK 連接失敗

```bash
# 重新登入
copilot login

# 檢查版本
copilot --version

# 確認 Copilot 服務狀態
copilot --help
```

### FFmpeg 未找到

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# 驗證安裝
ffmpeg -version
```

### Python 模組錯誤

```bash
# 重新安裝依賴
pip install -r requirements.txt --force-reinstall

# 或使用 uv
uv pip install -r requirements.lock --reinstall
```

### HandBrake CLI 未找到

```bash
# 下載並安裝 HandBrake CLI
# https://handbrake.fr/downloads.php

# 或使用 FFmpeg 替代
python main.py input.mp4 --ffmpeg
```

### 測試失敗

```bash
# 確認所有依賴已安裝
uv pip list

# 確認 Copilot CLI 已登入
copilot login

# 重新執行測試
python test_copilot.py
```

### 錯誤：`ModuleNotFoundError: No module named 'copilot'`

**解決方案：**
```bash
# 安裝 GitHub Copilot SDK
pip install github-copilot-sdk

# 或使用 uv
uv pip install github-copilot-sdk
```

### 錯誤：`Connection refused` 或 `CLI not found`

**解決方案：**
```bash
# 確認 Copilot CLI 已安裝
copilot --version

# 重新登入
copilot login
```

---

## 技術細節

### 核心依賴

```
github-copilot-sdk==0.1.23      # AI 分析引擎
pydantic==2.12.5                # 數據驗證
typing-extensions==4.15.0       # 類型提示擴展
```

### GitHub Copilot SDK 整合

專案使用 GitHub Copilot SDK Python 客戶端進行 AI 分析：

```python
from copilot import CopilotClient

# 初始化客戶端（無需 API key）
client = CopilotClient()
await client.start()

# 創建對話會話
session = await client.create_session({
    "model": "claude-sonnet-4.5",
    "streaming": False,
})

# 發送分析請求
await session.send({"prompt": "分析影片並建議參數..."})
```

### AI 參數優化邏輯

AI 會根據以下因素建議參數：

- **解析度**：影響 CRF 值選擇
  - 高清（1080p+）建議 CRF 20-24
  - 標清（720p-）建議 CRF 22-26

- **原始位元率**：判斷是否需要降低解析度
  - 位元率過低時建議降低解析度以保持品質

- **影片類型**：不同內容類型需要不同的品質設定
  - 動畫、卡通可使用更高的 CRF
  - 實拍影片需要更低的 CRF 保持細節

- **音訊配置**：多聲道需要更高的音訊位元率
  - 立體聲建議 128k-192k
  - 多聲道建議 192k-256k

### 品質評估指標

#### VMAF（Video Multimethod Assessment Fusion）
- Netflix 開發的視覺品質評估工具
- 分數範圍：0-100（越高越好）
- 評級：
  - ≥95：優秀（幾乎無損）
  - ≥85：良好（高品質）
  - ≥70：可接受（中等品質）
  - <70：較差（低品質）

#### PSNR（Peak Signal-to-Noise Ratio）
- 峰值信噪比，單位 dB
- 評級：
  - ≥40 dB：優秀
  - ≥35 dB：良好
  - ≥30 dB：可接受
  - <30 dB：較差

#### SSIM（Structural Similarity Index）
- 結構相似性指數
- 分數範圍：0-1（越高越好）
- 評級：
  - ≥0.95：優秀
  - ≥0.90：良好
  - ≥0.80：可接受
  - <0.80：較差

---

## 參考資料

### 官方文檔

- [GitHub Copilot SDK](https://github.com/github/copilot-sdk) - SDK 主要倉庫
- [Python SDK 文檔](https://github.com/github/copilot-sdk/blob/main/python/README.md) - Python 特定文檔
- [Copilot CLI 文檔](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli) - CLI 使用指南
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html) - FFmpeg 官方文檔
- [HandBrake Documentation](https://handbrake.fr/docs/) - HandBrake 官方文檔
- [VMAF](https://github.com/Netflix/vmaf) - Netflix VMAF 專案

### 工具資源

- [uv 官方文檔](https://docs.astral.sh/uv/) - uv 套件管理器文檔
- [uv GitHub](https://github.com/astral-sh/uv) - uv 原始碼倉庫
- [從 pip 遷移到 uv](https://docs.astral.sh/uv/guides/migration/) - 遷移指南

---

## 授權

MIT License

---

## 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發環境設定

```bash
# 1. Fork 並克隆專案
git clone <your-fork-url>
cd handbrake-agent

# 2. 建立虛擬環境
uv venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 3. 安裝開發依賴
uv pip install -r requirements.lock

# 4. 執行測試
python test_copilot.py
```

---

## 致謝

- **GitHub Copilot SDK** - 提供強大的 AI 能力
- **FFmpeg** - 影片處理的瑞士軍刀
- **HandBrake** - 優秀的影片轉碼工具
- **uv** - 現代化的 Python 套件管理器

---

**最後更新：** 2026-02-14
**版本：** 1.1.0
**狀態：** ✅ 生產就緒
