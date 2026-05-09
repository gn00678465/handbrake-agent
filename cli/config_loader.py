"""YAML 設定檔載入與合併。

提供：
- load_config(path): 讀檔、解析 YAML、回傳 {"settings": {...}, "inputs": [...]}。
- merge_with_args(args, settings, parser, argv=None): 把 settings 合併到 args，
  遵循「CLI > 檔案 > 預設」。CLI 顯式給定的 flag 不會被 config 覆寫。

設計重點：
- argparse 的 args 即使使用者沒給 flag 也會帶預設值，因此光看 args 屬性無法分辨
  「使用者顯式給了預設值」與「使用者沒給」。本模組改以 sys.argv 是否含對應 option
  字串為判斷依據。
- inputs 是特殊欄位，不對應任何 argparse dest，由呼叫端自行使用。
- 不在白名單內的 key 印警告但不擋執行（例如 yaml 內出現過時或拼錯的 key）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

ALLOWED_KEYS = {
    "model",
    "prompt",
    "ffmpeg",
    "vmaf",
    "vmaf_feedback",
    "preview",
    "preview_duration",
    "yes",
    "auto_loop",
    "params_file",
    "no_verify",
}

INPUTS_KEY = "inputs"


def load_config(path: str) -> Dict[str, Any]:
    """讀取 YAML 設定檔。

    Returns:
        {"settings": {...}, "inputs": [...]}。
        settings 僅包含 ALLOWED_KEYS 內的 key；inputs 為字串清單（可能空）。

    Raises:
        FileNotFoundError: 檔案不存在。
        ValueError: YAML 解析失敗、頂層非 mapping，或 inputs 非清單。
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"設定檔不存在：{path}")

    try:
        with p.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 解析失敗：{e}") from e

    if raw is None:
        return {"settings": {}, "inputs": []}

    if not isinstance(raw, dict):
        raise ValueError(f"設定檔頂層必須是 mapping，目前是 {type(raw).__name__}")

    settings: Dict[str, Any] = {}
    for key, value in raw.items():
        # YAML 1.1 將 yes/no/on/off 視為 boolean，未加引號的 `yes:` 會被解析為 `True:`。
        # 自動轉回字串 key 並提示加引號，避免使用者面對「未知 key 'True'」這種無從 debug 的訊息。
        if isinstance(key, bool):
            original_repr = repr(key)
            key = "yes" if key else "no"
            print(
                f"[Config] 提示：YAML 將 {original_repr} 解析為 boolean，"
                f'已自動視為 "{key}"。建議在 YAML 中加引號（例如 "{key}": true）以避免歧義。'
            )
        if key == INPUTS_KEY:
            continue
        if key in ALLOWED_KEYS:
            settings[key] = value
        else:
            print(f"[Config] 警告：忽略未知 key '{key}'")

    inputs_raw = raw.get(INPUTS_KEY, []) or []
    if not isinstance(inputs_raw, list):
        raise ValueError(f"inputs 必須是清單，目前是 {type(inputs_raw).__name__}")
    inputs: List[str] = []
    for i, item in enumerate(inputs_raw):
        if not isinstance(item, str):
            raise ValueError(f"inputs[{i}] 必須是字串，目前是 {type(item).__name__}")
        inputs.append(item)

    return {"settings": settings, "inputs": inputs}


def _build_dest_to_options(parser) -> Dict[str, List[str]]:
    """從 parser 取得 dest → option_strings 對應表。"""
    mapping: Dict[str, List[str]] = {}
    for action in parser._actions:
        if action.option_strings:
            mapping[action.dest] = list(action.option_strings)
    return mapping


def _cli_provided(dest: str, dest_to_options: Dict[str, List[str]], argv: List[str]) -> bool:
    """檢查使用者是否在 argv 中顯式給定該 flag。"""
    for opt in dest_to_options.get(dest, []):
        for tok in argv:
            if tok == opt or tok.startswith(opt + "="):
                return True
    return False


def merge_with_args(
    args,
    settings: Dict[str, Any],
    parser,
    argv: Optional[List[str]] = None,
) -> List[str]:
    """把 settings 合併到 args（CLI 已給的 flag 不覆寫）。

    args 會被原地修改。

    Returns:
        被實際套用的 key 列表，方便呼叫端列印 log。
    """
    if argv is None:
        argv = sys.argv[1:]
    dest_to_options = _build_dest_to_options(parser)

    applied: List[str] = []
    for key, value in settings.items():
        if not hasattr(args, key):
            print(f"[Config] 警告：args 中找不到屬性 '{key}'，這個 flag 可能未在當前模式註冊")
            continue
        if _cli_provided(key, dest_to_options, argv):
            continue
        setattr(args, key, value)
        applied.append(key)
    return applied
