# `hba` CLI Help

```text
usage: main.py [-h] [--batch] [--ffmpeg] [--no-verify] [--vmaf [N]]
               [--preview] [--preview-duration SECONDS] [--yes]
               [--vmaf-feedback VMAF_JSON] [--model MODEL] [--auto-loop [N]]
               [--prompt TEXT] [--params-file PARAMS_JSON] [--version]
               input

AI 影片轉碼工具 (Copilot SDK 版)

positional arguments:
  input                 輸入影片路徑或資料夾路徑

options:
  -h, --help            show this help message and exit
  --batch               批次處理資料夾
  --ffmpeg              使用 FFmpeg 而非 HandBrake
  --no-verify           停用品質驗證
  --vmaf [N]            啟用 VMAF 品質驗證。可選參數 N 為取樣步長（預設 N=1，即每幀計算）；--vmaf 5 表示每 5 幀取樣一次（速度提升
                        ~5x），推薦值 5-10。
  --preview             預覽模式：僅轉碼影片前段（預設 30 秒），保留 vmaf json 與 params 供後續參考。
  --preview-duration SECONDS
                        預覽模式的時長（秒），預設 30 秒。
  --yes, -y             自動確認執行轉碼，不詢問 y/n
  --vmaf-feedback VMAF_JSON
                        傳入先前產出的 vmaf.json 檔案，讓 AI 根據數據微調參數建議
  --model MODEL         指定的 Copilot SDK 使用的 AI 模式（預設：gpt-5-mini）
  --auto-loop [N]       自動執行多次「分析 -> 預覽 -> vmaf」迭代。預設 N=3 次；--auto-loop 2
                        即執行 2 次。
  --prompt, -p TEXT     使用者自訂的提示詞，將附加在 AI 分析 prompt 後面
  --params-file PARAMS_JSON
                        輸入已有的 params.json，略過 AI 分析直接使用指定參數
  --version, -V         show program's version number and exit

範例:
  # 基本使用
  main.py video.mp4

  # 預覽模式（僅轉碼前 30 秒，儲存 vmaf json 與 params）
  main.py video.mp4 --preview --vmaf

  # 完整工作流程（自動迭代 + 轉檔 + 清理）
  main.py run video.mp4

  # 使用 FFmpeg + 預覽
  main.py video.mp4 --ffmpeg --preview

  # 批次處理 + 預覽模式
  main.py ./videos/ --batch --preview
```
