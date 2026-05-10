"""cli/config_loader.py 的單元測試"""

import argparse
import textwrap

import pytest

from cli.config_loader import ALLOWED_KEYS, load_config, merge_with_args
from cli.flags import (
    auto_loop,
    config,
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


def write_yaml(tmp_path, content: str):
    p = tmp_path / "cfg.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)


def make_full_parser() -> argparse.ArgumentParser:
    """還原 _legacy_main 的 parser，確保 dest 與真實 CLI 對齊"""
    p = argparse.ArgumentParser()
    p.add_argument("input", nargs="?")
    config.add_to(p)
    ffmpeg.add_to(p)
    verify.add_to(p)
    vmaf.add_to(p)
    preview.add_to(p)
    yes.add_to(p)
    vmaf_feedback.add_to(p)
    model.add_to(p)
    auto_loop.add_to(p)
    prompt.add_to(p)
    params_file.add_to(p)
    return p


# ── load_config ───────────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_settings_only(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """\
            model: gpt-4o
            vmaf: 3
            ffmpeg: true
            """,
        )
        cfg = load_config(path)
        assert cfg["settings"] == {"model": "gpt-4o", "vmaf": 3, "ffmpeg": True}
        assert cfg["inputs"] == []

    def test_inputs_only(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """\
            inputs:
              - a.mp4
              - b.mp4
            """,
        )
        cfg = load_config(path)
        assert cfg["settings"] == {}
        assert cfg["inputs"] == ["a.mp4", "b.mp4"]

    def test_settings_and_inputs(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """\
            model: gpt-5-mini
            inputs:
              - x.mp4
            """,
        )
        cfg = load_config(path)
        assert cfg["settings"] == {"model": "gpt-5-mini"}
        assert cfg["inputs"] == ["x.mp4"]

    def test_empty_file(self, tmp_path):
        path = write_yaml(tmp_path, "")
        cfg = load_config(path)
        assert cfg == {"settings": {}, "inputs": []}

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nope.yaml"))

    def test_invalid_yaml_raises(self, tmp_path):
        path = write_yaml(tmp_path, "model: [unclosed\n")
        with pytest.raises(ValueError, match="YAML 解析失敗"):
            load_config(path)

    def test_top_level_not_mapping(self, tmp_path):
        path = write_yaml(tmp_path, "- a\n- b\n")
        with pytest.raises(ValueError, match="頂層必須是 mapping"):
            load_config(path)

    def test_inputs_not_list(self, tmp_path):
        path = write_yaml(tmp_path, "inputs: not_a_list\n")
        with pytest.raises(ValueError, match="inputs 必須是清單"):
            load_config(path)

    def test_inputs_item_not_string(self, tmp_path):
        path = write_yaml(
            tmp_path,
            """\
            inputs:
              - a.mp4
              - 123
            """,
        )
        with pytest.raises(ValueError, match=r"inputs\[1\] 必須是字串"):
            load_config(path)

    def test_unknown_key_warns_and_skips(self, tmp_path, capsys):
        path = write_yaml(
            tmp_path,
            """\
            model: gpt-4o
            unknown_flag: hello
            """,
        )
        cfg = load_config(path)
        out = capsys.readouterr().out
        assert "未知 key 'unknown_flag'" in out
        assert "unknown_flag" not in cfg["settings"]
        assert cfg["settings"]["model"] == "gpt-4o"

    def test_yaml_yes_unquoted_remaps_to_string_key(self, tmp_path, capsys):
        """YAML 1.1 把 `yes:` 解析為 boolean True；loader 應自動轉回字串 'yes' 並提示。"""
        path = write_yaml(
            tmp_path,
            """\
            yes: true
            """,
        )
        cfg = load_config(path)
        out = capsys.readouterr().out
        assert "yes" in cfg["settings"]
        assert cfg["settings"]["yes"] is True
        assert "解析為 boolean" in out
        assert '"yes": true' in out  # 提示訊息包含建議寫法

    def test_yaml_quoted_yes_works_directly(self, tmp_path, capsys):
        """加引號的 `"yes":` 不會被當 boolean，直接通過白名單。"""
        path = write_yaml(
            tmp_path,
            """\
            "yes": true
            """,
        )
        cfg = load_config(path)
        out = capsys.readouterr().out
        assert cfg["settings"] == {"yes": True}
        assert "解析為 boolean" not in out  # 不該觸發提示

    def test_yaml_no_unquoted_remaps_to_no(self, tmp_path, capsys):
        """`no:` (False) 也會被自動轉回 'no'，雖然不是白名單 key 仍會繼續走未知 key 警告。"""
        path = write_yaml(
            tmp_path,
            """\
            no: true
            """,
        )
        cfg = load_config(path)
        out = capsys.readouterr().out
        assert cfg["settings"] == {}  # 'no' 不在白名單
        assert "解析為 boolean" in out
        assert "未知 key 'no'" in out

    def test_allowed_keys_snapshot(self):
        """白名單變動時測試會直接顯示出來，避免無聲漂移"""
        assert ALLOWED_KEYS == {
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


# ── merge_with_args ───────────────────────────────────────────────────────────


class TestMergeWithArgs:
    def test_applies_when_cli_absent(self):
        p = make_full_parser()
        args = p.parse_args([])
        applied = merge_with_args(args, {"vmaf": 3, "model": "gpt-4o"}, p, argv=[])
        assert args.vmaf == 3
        assert args.model == "gpt-4o"
        assert set(applied) == {"vmaf", "model"}

    def test_cli_long_flag_overrides(self):
        p = make_full_parser()
        argv = ["--vmaf", "1"]
        args = p.parse_args(argv)
        applied = merge_with_args(args, {"vmaf": 5, "model": "gpt-4o"}, p, argv=argv)
        assert args.vmaf == 1  # CLI 贏
        assert args.model == "gpt-4o"  # CLI 沒給，採用檔案
        assert "vmaf" not in applied
        assert "model" in applied

    def test_cli_short_flag_overrides(self):
        p = make_full_parser()
        argv = ["-y"]
        args = p.parse_args(argv)
        merge_with_args(args, {"yes": False}, p, argv=argv)
        assert args.yes is True  # -y 已給，不被檔案蓋掉

    def test_equals_form_recognised(self):
        p = make_full_parser()
        argv = ["--model=gpt-4o"]
        args = p.parse_args(argv)
        merge_with_args(args, {"model": "gpt-5-mini"}, p, argv=argv)
        assert args.model == "gpt-4o"

    def test_silently_skip_missing_dest(self, capsys):
        """settings 內含 args 沒有的屬性時靜默跳過（不噴警告）。

        實務情境：hba run parser 沒註冊 preview / yes / no_verify 等 dest，
        若 YAML 同時給 legacy 與 run 共用，缺席的 key 應被靜默忽略，
        否則 run 模式會被大量「未在當前模式註冊」警告淹沒。
        """
        p = make_full_parser()
        args = p.parse_args([])
        merge_with_args(args, {"some_phantom_dest": True}, p, argv=[])
        out = capsys.readouterr().out
        assert out == ""
        assert not hasattr(args, "some_phantom_dest")

    def test_no_verify_via_config(self):
        p = make_full_parser()
        args = p.parse_args([])
        merge_with_args(args, {"no_verify": True}, p, argv=[])
        assert args.no_verify is True

    def test_preview_duration_default_overridden(self):
        """argparse 預設 preview_duration=30，檔案應能改成其他值"""
        p = make_full_parser()
        args = p.parse_args([])
        assert args.preview_duration == 30  # 預設
        merge_with_args(args, {"preview_duration": 60}, p, argv=[])
        assert args.preview_duration == 60

    def test_preview_duration_cli_explicit_default_wins(self):
        """使用者顯式給預設值（30）也算 CLI 給定，檔案不應蓋"""
        p = make_full_parser()
        argv = ["--preview-duration", "30"]
        args = p.parse_args(argv)
        merge_with_args(args, {"preview_duration": 60}, p, argv=argv)
        assert args.preview_duration == 30
