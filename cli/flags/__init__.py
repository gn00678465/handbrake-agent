"""CLI flags 模組，每個 flag 對應一個獨立檔案。

使用方式：
    from cli.flags import ffmpeg, vmaf, model, prompt
    ffmpeg.add_to(parser)
    vmaf.add_to(parser, run_mode=True)
"""

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

__all__ = [
    "auto_loop",
    "batch",
    "ffmpeg",
    "model",
    "params_file",
    "preview",
    "prompt",
    "verify",
    "vmaf",
    "vmaf_feedback",
    "yes",
]
