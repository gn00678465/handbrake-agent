# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run tests (all)
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_cli_flags.py -v

# Run a single test class or case
uv run pytest tests/test_cli_flags.py::TestVmaf -v
uv run pytest tests/test_cli_flags.py::TestVmaf::test_vmaf_with_value -v

# Lint
uv run ruff check main.py cli/ tools/ tests/

# Format
uv run black main.py cli/ tools/ tests/

# Run the app (no need to activate venv)
uv run main.py video.mp4 --preview --vmaf --yes
uv run main.py run video.mp4
```

**All new CLI flag changes must pass the test suite in `tests/test_cli_flags.py`.**

## Architecture

### Entry Points

`main()` in `main.py` dispatches based on `sys.argv[1] == "run"`:

- **Legacy mode** (`_legacy_main`): default, supports all flags including `--batch`, `--auto-loop`, `--params-file`
- **Run subcommand** (`_run_main`): `hba run video.mp4` — runs Phase 1→2→3 workflow automatically

Both modes use `VideoTranscoder.process_video()` as the core processing unit.

### Modular Flag System (`cli/flags/`)

Each flag is an independent module with a single `add_to(parser, **kwargs)` function. Flags are context-aware via keyword arguments:

| Flag module | Notable kwargs |
|-------------|---------------|
| `vmaf.py` | `run_mode=True` changes nargs/default behaviour |
| `auto_loop.py` | `run_mode=True` requires a value; legacy uses optional `nargs='?'` |
| `preview.py` | `include_toggle=False` omits `--preview` (run subcommand only needs `--preview-duration`) |
| `model.py` | accepts `default=` to override the default model name |

`cli/flags/__init__.py` re-exports all flag modules so `main.py` imports them with `from cli.flags import vmaf, model, ...`.

### Processing Pipeline (`VideoTranscoder.process_video`)

Five sequential steps printed as `[1/5]`…`[5/5]`:

1. **Video info** — `ffprobe` via `tools/video_info.py`
2. **Parameters** — AI analysis via `tools/ai_analyzer.py` (GitHub Copilot SDK), or load from `--params-file`
3. **Transcode** — FFmpeg or HandBrake via `tools/transcoder.py` (tqdm progress bar driven by stderr/stdout)
4. **Quality verification** — VMAF (`tools/quality.py`, tqdm progress) or PSNR/SSIM
5. **Result** — size/compression report; in preview mode saves `params_*.json` if VMAF ≥ 85

### Run Workflow (`_run_workflow`)

Three phases with automatic cleanup:
- **Phase 1**: Iterates preview+VMAF up to `--auto-loop N` times (default 2); stops early if VMAF ≥ `VMAF_GOOD_THRESHOLD` (85)
- **Phase 2**: Full transcode with best params from Phase 1
- **Phase 3**: Deletes all preview files, vmaf JSONs, and params JSONs

### tqdm Usage

Progress bars are used only in two places:
- **Transcoding** (`tools/transcoder.py`): parses `time=` from ffmpeg stderr or `XX.XX %` from HandBrake stdout; jumps to 100% on completion
- **VMAF calculation** (`tools/quality.py`): same ffmpeg `time=` parsing pattern; jumps to 100% on completion

After the `while` read loop ends, always call `pbar.update(total - pbar.n)` before `process.wait()` to ensure 100% display on early exit.

### Key Constants

```python
# main.py
VMAF_GOOD_THRESHOLD = 85  # saves params and stops auto-loop early
```
