# `hba run` CLI Help

```text
usage: hba run [-h] [--ffmpeg] [--vmaf [N]] [--auto-loop N]
               [--preview-duration SECONDS] [--model MODEL] [--prompt TEXT]
               [--params-file PARAMS_JSON] [--config CONFIG_YAML] [--version]
               [input]

完整工作流程：自動迭代取得最佳參數 -> 完整轉檔 -> 品質驗證 -> 清理暫存檔

positional arguments:
  input                 輸入影片路徑（搭配 --config + inputs: 時可省略）

options:
  -h, --help            show this help message and exit
  --ffmpeg              使用 FFmpeg 而非 HandBrake
  --vmaf [N]            VMAF 取樣間隔（預設 N=1 逐幀計算；--vmaf 5 每 5 幀取樣一次，提升 ~5x，推薦值 5-10）。
  --auto-loop N         Preview 迭代次數（預設 2）。
  --preview-duration SECONDS
                        預覽模式的時長（秒），預設 30 秒。
  --model MODEL         指定的 Copilot SDK 使用的 AI 模式（預設：gpt-5-mini）
  --prompt, -p TEXT     使用者自訂的提示詞，將附加在 AI 分析 prompt 後面
  --params-file PARAMS_JSON
                        輸入已有的 params.json，若提供則跳過 Phase 1 迭代
  --config CONFIG_YAML  載入 YAML 設定檔，可指定共用 flag 設定與 inputs 批次清單；CLI flag
                        仍會覆寫檔案值
  --version, -V         show program's version number and exit

範例:
  hba run video.mp4
  hba run video.mp4 --vmaf 5
  hba run video.mp4 --auto-loop 3
  hba run video.mp4 --vmaf 5 --model gpt-4o --prompt "優先保留細節"
  hba run --config docs/example/config.example.yaml
```

## `--config` 補充說明

`hba run` 與 legacy 模式共用同一份 YAML 結構：頂層 key 對應 CLI 長 flag（破折號改底線），
`inputs:` 為批次清單。當 `inputs:` 含多個檔案時，`hba run` 會對每一個檔案各自跑一次完整
的 Phase 1 → 2 → 3 工作流程。

優先序為「**CLI > 檔案 > 預設**」。

範例設定檔：[`docs/example/config.example.yaml`](example/config.example.yaml)
