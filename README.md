# HandBrake Agent - AI 影片轉碼工具

使用 GitHub Copilot SDK 提供 AI 驅動的影片轉碼參數優化建議，專為高品質、高效率轉碼設計。

**版本：** 1.5.0
**狀態：** ✅ 生產就緒
**更新：** 2026-05-09

---

## 目錄

- [功能特點](#功能特點)
- [快速開始](#快速開始-5-分鐘上手)
- [系統需求](#系統需求)
- [安裝](#安裝)
- [CLI 工具安裝](#-cli-工具安裝可選)
- [使用方法](#使用方法)
  - [🎬 預覽模式 (Smart Preview)](#-預覽模式-smart-preview-推薦用於測試)
  - [🚀 run 子命令 (一鍵完整工作流程)](#-run-子命令一鍵完整工作流程)
- [專案結構](#專案結構)
- [套件管理 (uv)](#套件管理-uv)
- [測試](#測試)
- [常見問題](#常見問題)
- [技術細節](#技術細節)
- [參考資料](#參考資料)

## 📚 其他文檔

- [docs/cli_reference.md](docs/cli_reference.md) - 完整的 CLI 參數參考指南
- [docs/hba_cli.md](docs/hba_cli.md) - `hba` CLI 指令詳細幫助
- [docs/hba_run_cli.md](docs/hba_run_cli.md) - `hba run` 指令詳細幫助
- [AGENTS.md](AGENTS.md) - Agent 開發與架構說明

---

## 功能特點

- 🤖 **AI 參數優化**：使用 GitHub Copilot SDK (Claude 3.5 Sonnet / gpt-5-mini) 分析影片特性，自動建議最佳轉碼參數
- 📊 **品質驗證**：支援 VMAF、PSNR、SSIM 等品質評估指標，並支援 **VMAF 取樣間隔** 以提升 5x 驗證速度
- ⚡ **極速預覽 (Smart Preview)**：自動跳過音訊處理並採用多段切割技術，比完整轉碼快 30-50x，比一般預覽快 3x
- 🔄 **自動迭代優化**：支援 `auto-loop` 模式，自動執行「分析 -> 預覽 -> 品質驗證 -> 參數精調」的閉環優化
- 📦 **批次處理**：可批次處理資料夾中的多個影片
- 📝 **YAML 設定檔**：使用 `--config` 載入共用 flag 設定與 inputs 批次清單，範例見 [`docs/example/config.example.yaml`](docs/example/config.example.yaml)
- 🔧 **CLI 工具化**：可安裝為全域命令，提供 `handbrake-agent` 與 `hba` 雙重入口
- 🔒 **可重現建置**：使用 uv 套件管理器確保環境一致性與極速安裝

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
# 檢查 Copilot CLI 是否已安裝並登入
copilot login
```

### 第 3 步：一鍵自動優化並轉碼

```bash
# 使用 run 子命令：自動尋找最佳參數並完成最終轉碼
uv run main.py run your_video.mp4 --vmaf 5
```

---

## 系統需求

### 必需工具

1. **Python 3.8+**（推薦 3.13）
2. **GitHub Copilot CLI** (需要有效訂閱)
3. **FFmpeg** (推薦，必備於 VMAF 驗證)
4. **HandBrake CLI** (選用，可改用 `--ffmpeg` 使用內建 FFmpeg 轉碼)

---

## 安裝

### 方法 1: 使用 uv（推薦，最快方式）

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝依賴
uv pip install -r requirements.lock
```

---

## 🔧 CLI 工具安裝（可選）

將 HandBrake Agent 安裝為全域命令，可以在任何目錄下使用 `hba` 或 `handbrake-agent`。

### 全域安裝

```bash
# 使用 uv tool 全域安裝
uv tool install .

# 驗證安裝
hba --version
# handbrake-agent 1.4.0
```

### 更新全域安裝

```bash
git pull
uv tool install --reinstall .
```

---

## 使用方法

### 🎬 預覽模式 (Smart Preview) ⭐️ 推薦

預覽模式是本工具的核心競爭力，能讓你在數秒內驗證 AI 建議的參數：

```bash
# 基礎預覽（預設 30 秒，自動產生 params.json 與 vmaf.json）
hba input.mp4 --preview --vmaf

# 指定 VMAF 取樣間隔（每 5 幀取樣一次，大幅加速驗證）
hba input.mp4 --preview --vmaf 5

# 帶入上次的 VMAF 指標進行 AI 參數精調 (AI Feedback Loop)
hba input.mp4 --preview --vmaf --vmaf-feedback vmaf.json --yes
```

**Smart Preview 優勢：**
- **音訊跳過**：預覽時自動排除音訊編碼，節省大量 CPU 資源
- **多段取樣**：自動從影片的前、中、後段提取片段，確保參數對整部影片有效
- **指標驅動**：AI 會讀取 VMAF sub-metrics (VIF/ADM) 來調整 CRF 或 Preset

### 🚀 run 子命令 (一鍵完整工作流程)

如果你不想手動執行多次預覽，請直接使用 `run` 子命令。它會自動執行以下流程：
1. **Phase 1**：自動迭代 (Auto-loop) 預覽尋找最佳 VMAF 分數的參數
2. **Phase 2**：使用最終確定的參數進行完整轉檔
3. **Phase 3**：品質複驗與暫存檔清理

```bash
# 預設執行 2 次迭代優化後直接轉碼
hba run video.mp4

# 指定迭代次數與 VMAF 取樣速度
hba run video.mp4 --auto-loop 3 --vmaf 5

# 【新功能】帶入已知最佳參數檔，直接跳過 Phase 1 進入轉檔流程
hba run video.mp4 --params-file "params_20260223.json"
```

### 其他進階選項

```bash
# 使用 FFmpeg 核心
hba input.mp4 --ffmpeg

# 批次處理
hba ./videos/ --batch --preview

# 自動迭代測試（不進行最終轉碼，僅找出最佳參數）
hba input.mp4 --auto-loop 3 --preview --vmaf 5 --yes

# 附加自訂要求
hba input.mp4 --prompt "這是動畫內容，請優先保留線條清晰度"
```

---

## 專案結構

- `main.py`：主程式入口與 CLI 邏輯
- `tools/video_info.py`：使用 ffprobe 提取影片元數據
- `tools/ai_analyzer.py`：與 GitHub Copilot SDK (AI) 互動，根據影片資訊與 VMAF 指標產出參數建議
- `tools/transcoder.py`：封裝 FFmpeg 與 HandBrake 轉碼邏輯
- `tools/quality.py`：計算 VMAF、PSNR、SSIM 等品質數據
- `docs/cli_reference.md`：詳細的 CLI 指令參考

---

## 套件管理 (uv)

本專案深度整合 **uv**，它是用 Rust 編寫的現代化 Python 套件管理器。

- **極速安裝**：比 pip 快 10-100 倍
- **環境一致性**：透過 `requirements.lock` 確保所有機器上的依賴版本一致
- **工具管理**：使用 `uv tool` 輕鬆管理全域 CLI 工具

---

## 常見問題

### Q: 為什麼預覽模式沒有聲音？
**A:** 這是為了最大化轉碼速度。預覽模式 (Smart Preview) 的目的是驗證「視訊品質」與「壓縮率」。在完整轉碼模式下會保留所有音訊。

### Q: VMAF 分數要多少才算好？
**A:** 一般建議 VMAF > 90 (高品質) 或 VMAF > 95 (視覺無損)。若分數低於 70，工具會自動提供診斷建議。

### Q: 我可以指定 AI 模型嗎？
**A:** 可以，透過 `--model` 參數。目前支援 `gpt-5-mini` (預設)、`gpt-4o`、`claude-3.5-sonnet` 等。

---

## 技術細節

### AI 參數精調邏輯 (Feedback Loop)

當您使用 `--vmaf-feedback` 或 `run` 子命令時，AI 會分析 VMAF 的子指標：
- **VIF (Visual Information Fidelity)**：低於 0.70 代表有方塊感，AI 會建議降低 CRF。
- **ADM (Detail Loss)**：低於 0.88 代表細節遺失，AI 會建議改用更慢的 Preset。

---

## 授權

MIT License