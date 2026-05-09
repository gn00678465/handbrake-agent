# HandBrake Agent CLI 參考文件

`handbrake-agent` (hba) 是一個由 AI 驅動的影片轉碼工具，整合了 GitHub Copilot SDK、FFmpeg 與 HandBrake。

## 主要指令用法

```bash
hba [input] [options]
# 或使用子命令 run
hba run [input] [options]
```

### 1. 基礎轉碼模式 (Legacy Mode)

這是預設的模式，使用者可以針對單一檔案或資料夾進行處理。

**用法：**
`python main.py [input] [options]`

**參數說明：**

| 參數 | 說明 |
| :--- | :--- |
| `input` | 輸入影片路徑或資料夾路徑。搭配 `--config` 且檔案內含 `inputs:` 時可省略。 |
| `--batch` | 批次處理資料夾中的影片。 |
| `--config CONFIG_YAML` | 載入 YAML 設定檔（共用 flag 設定 + `inputs:` 批次清單）。CLI flag 優先於檔案；範例見 [`docs/example/config.example.yaml`](example/config.example.yaml)。 |
| `--ffmpeg` | 使用 FFmpeg 進行轉碼（預設使用 HandBrake）。 |
| `--no-verify` | 停用品質驗證（PSNR/SSIM/VMAF）。 |
| `--vmaf [N]` | 啟用 VMAF 品質驗證。`N` 為取樣間隔（預設 1）。例如 `--vmaf 5` 表示每 5 幀取樣一次（速度提升 ~5x）。 |
| `--preview` | 預覽模式：僅轉碼影片前段（預設 30 秒），保留 VMAF JSON 與參數供後續參考。 |
| `--preview-duration SECONDS` | 設定預覽模式的秒數（預設 30 秒）。 |
| `--yes`, `-y` | 自動確認執行轉碼，不詢問 y/n。 |
| `--vmaf-feedback VMAF_JSON` | 傳入先前預覽產生的 VMAF JSON 檔案，讓 AI 根據品質數據調整參數。 |
| `--model MODEL` | 指定要使用的 AI 模型（預設：`gpt-5-mini`）。 |
| `--auto-loop [N]` | 自動執行多次「預覽 + VMAF」迭代以尋找最佳參數。預設迭代 3 次。 |
| `--prompt`, `-p TEXT` | 提供給 AI 的額外提示詞（例如：「優先保留暗部細節」）。 |
| `--params-file PARAMS_JSON` | 直接載入預存的參數檔（JSON），略過 AI 分析。 |
| `--version`, `-V` | 顯示程式版本號。 |

---

### 2. 自動化工作流程 (Run Subcommand)

`run` 子命令提供完整的自動化流程：**自動迭代預覽尋找最佳參數 → 完整轉檔 → 品質驗證 → 清理暫存檔**。

**用法：**
`hba run [input] [options]`

**參數說明：**

| 參數 | 說明 |
| :--- | :--- |
| `input` | 輸入影片路徑。搭配 `--config` 且檔案內含 `inputs:` 時可省略。 |
| `--ffmpeg` | 使用 FFmpeg 進行轉碼。 |
| `--vmaf [N]` | VMAF 取樣間隔（預設 1）。 |
| `--auto-loop N` | 設定預覽迭代次數（預設 2）。 |
| `--preview-duration SECONDS` | 預覽秒數（預設 30 秒）。 |
| `--model MODEL` | 指定 AI 模型。 |
| `--prompt`, `-p TEXT` | 額外提示詞。 |
| `--params-file PARAMS_JSON` | 直接載入預存參數檔（JSON），若提供則跳過 Phase 1 迭代。 |
| `--config CONFIG_YAML` | 載入 YAML 設定檔（共用 flag 設定 + `inputs:` 批次清單）。CLI flag 優先於檔案；範例見 [`docs/example/config.example.yaml`](example/config.example.yaml)。 |

---

## 使用範例

### 基本使用
```bash
hba video.mp4
```

### 預覽模式（快速驗證參數）
```bash
hba video.mp4 --preview --vmaf
```

### 完整自動化流程（推薦）
```bash
hba run video.mp4 --vmaf 5 --auto-loop 3
```

### 批次處理資料夾
```bash
hba ./my_videos/ --batch --preview
```

### 指定 AI 模型與自訂要求
```bash
hba run video.mp4 --model gpt-4o --prompt "這部影片雜訊較多，請適度去噪並保持清晰度"
```

### 使用 YAML 設定檔（含批次 inputs）
```bash
# 把共用設定與影片清單寫進一個檔案，一次跑完
hba --config my_jobs.yaml

# 也可只把設定抽出來，搭配單檔 input 使用
hba video.mp4 --config defaults.yaml

# CLI flag 永遠優先：檔案內 vmaf: 5 + CLI --vmaf 1 → 以 1 為準
hba video.mp4 --config defaults.yaml --vmaf 1

# run 子命令同樣支援
hba run --config my_jobs.yaml
```

範例設定檔位於 [`docs/example/config.example.yaml`](example/config.example.yaml)。
頂層 key 對應 CLI 長 flag（破折號改底線，例如 `--auto-loop` → `auto_loop`），
不在白名單內的 key 會被忽略並印警告。
