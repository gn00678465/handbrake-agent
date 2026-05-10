# Handoff: handbrake-agent `feat/config-flag` 分支

## TL;DR

`feat/config-flag` 分支加上 `--config` YAML 設定檔功能 + 一連串連鎖修正（cp950 編碼、Copilot SDK 0.3.0 API、VMAF Windows 路徑）。版本停在 **1.5.3**，global `hba` 已重裝、VMAF 已 end-to-end 跑通。本文撰寫當下尚未 push（後續以 PR #1 推進；此 handoff 為當時的歷史快照）。

## 目前狀態

- **Repo**: `D:\Projects-agents\handbrake-agent`
- **分支**: `feat/config-flag`（領先 `main` 9 commits）
- **版本**: 1.5.3（global `hba` 與 dev `.venv` 都已是這版）
- **測試**: `uv run pytest tests/ -q` 全綠，65 passed
- **Lint**: `uv run ruff check main.py cli/ tools/ tests/` 全綠

## 9 個 commit（完整歷史見 `git log main..HEAD`）

```
1582d75 chore: 更新版本至 1.5.3
f0cb0a5 fix(vmaf): 改用 cwd + 短檔名繞過 ffmpeg filter 的路徑 escape 困擾；版本回退至 1.5.2
e2162f7 fix(vmaf): Windows 路徑塞進 ffmpeg filter 導致 exit -22；同時把 stderr 帶進錯誤訊息
4a75840 fix(copilot): 適配 github-copilot-sdk 0.3.0 的破壞性 API 變更
640944c fix(config): 處理 YAML 1.1 把 yes/no 解析成 boolean 的歧義
b5333a0 chore: 更新版本至 1.5.1
da39019 docs(cli): cli_reference 與 hba/hba run CLI 文件加入 --config 說明
6c18c72 feat(config): 新增 --config flag 載入 YAML 設定檔與批次 inputs 清單
1704822 fix(encoding): subprocess 強制使用 UTF-8 解碼避免 Windows cp950 失敗
```

每個 commit message 內含完整 root cause + 修法說明，**不要重抄到這裡**，直接 `git show <hash>` 看。

## 下一步候選

依優先序：

1. **Push 並開 PR**
   - `git push -u origin feat/config-flag`
   - PR base: `main`
   - PR 標題建議：`feat(config): YAML 設定檔 + 連鎖環境修正（cp950 / Copilot SDK 0.3.0 / VMAF Windows 路徑）`
   - 9 commits 是合理的 PR 大小，不必 squash

2. **可選：清理歷史**
   - `e2162f7`（嘗試失敗的 escape）+ `f0cb0a5`（最終 cwd 修法）兩個 fix(vmaf) 講同一件事。技術上可以 squash 成一個，但留著也能反映問題排查過程。問使用者偏好。
   - 同樣 `b5333a0` chore bump 跟 `da39019` docs 是不是要互換順序，看使用者習慣（目前是 docs → chore → fix → ...）

3. **可選：補 hba_run_cli.md 是否要保留**
   - `da39019` 改了 `cli_reference.md` / `hba_cli.md` / `hba_run_cli.md` 三個文件
   - 使用者原本只說「hba_cli 文件」，是否包含 `hba_run_cli.md` 待確認。如果不要，`git revert` 那部分變更或在當前分支再 commit 一次。

## 環境陷阱（給下個 agent 注意）

- **Windows zh-TW**：subprocess `text=True` 不指定 encoding 會 fallback cp950，UTF-8 輸出會炸。已修，但**新增任何 subprocess.run/Popen 時都要記得加 `encoding="utf-8", errors="replace"`**（或 bytes 模式手動 decode）。
- **Global `hba` 跟 dev `.venv` 是分開的**：
  - Dev：`uv sync` 同步本 repo 的 `pyproject.toml`
  - Global：`uv tool install --reinstall --from D:\Projects-agents\handbrake-agent handbrake-agent`
  - **改完程式碼若沒重裝，使用者跑 `hba` 還是舊版**
- **PowerShell stdout buffer**：python 在 redirect 輸出時用 full buffering，crash 時 `print()` 可能會遺失。debug 印 log 可加 `$env:PYTHONUNBUFFERED='1'` 或在 python 端 `flush=True`。
- **PowerShell 終端字體**：常常會把 UTF-8 的中文輸出顯示成 mojibake。**這是顯示問題不是程式問題**，別當 bug 修。
- **不要碰的檔案**：`.gitignore`（agent 工具改的）、`.agents/`、`.claude/`、`apm.lock.yaml`、`apm.yml`。每次 `git add` 都要明確列檔名，避免污染 commit。

## 使用者偏好（從本 session 觀察到）

- Commit message: zh-TW + Conventional Commits，body 寫 root cause + 修法
- 版本 bump 規則：**修正驗證過再 bump**，且 bump 走獨立 `chore:` commit
- 過長的 traceback / log 喜歡實際執行驗證才相信「修好了」（不接受純猜測式修法）
- 直接、技術導向、討厭過度客套
- 偏好繁體中文回覆

## 建議下個 session 用的 skills

- 如果要 push + 開 PR：`cc-copilot-plugin:pull-request`（自動偵測預設分支、產 Conventional Commits 標題、依規模選模板）
- 如果使用者報新 bug：`superpowers:systematic-debugging` 或 `compound-engineering:ce-debug`
- 如果要新增功能：`superpowers:brainstorming` 先釐清再做
- 如果要寫 commit message：`cc-copilot-plugin:commit-message`

## 已知未解決事項

- 無。VMAF 已通過使用者實際驗證，版本已對齊到 1.5.3。
