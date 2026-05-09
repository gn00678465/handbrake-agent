"""cli/flags 各個 flag 模組的單元測試"""

import argparse

import pytest

from cli.flags import (
    auto_loop,
    batch,
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


def make_parser() -> argparse.ArgumentParser:
    """建立一個乾淨的測試用 parser"""
    return argparse.ArgumentParser()


# ── config ────────────────────────────────────────────────────────────────────


class TestConfig:
    def test_default_is_none(self):
        p = make_parser()
        config.add_to(p)
        args = p.parse_args([])
        assert args.config is None

    def test_set_path(self):
        p = make_parser()
        config.add_to(p)
        args = p.parse_args(["--config", "foo.yaml"])
        assert args.config == "foo.yaml"


# ── batch ─────────────────────────────────────────────────────────────────────


class TestBatch:
    def test_add_to_registers_flag(self):
        p = make_parser()
        batch.add_to(p)
        args = p.parse_args([])
        assert args.batch is False

    def test_flag_sets_true(self):
        p = make_parser()
        batch.add_to(p)
        args = p.parse_args(["--batch"])
        assert args.batch is True


# ── ffmpeg ────────────────────────────────────────────────────────────────────


class TestFfmpeg:
    def test_add_to_registers_flag(self):
        p = make_parser()
        ffmpeg.add_to(p)
        args = p.parse_args([])
        assert args.ffmpeg is False

    def test_flag_sets_true(self):
        p = make_parser()
        ffmpeg.add_to(p)
        args = p.parse_args(["--ffmpeg"])
        assert args.ffmpeg is True


# ── verify ────────────────────────────────────────────────────────────────────


class TestVerify:
    def test_add_to_registers_flag(self):
        p = make_parser()
        verify.add_to(p)
        args = p.parse_args([])
        assert args.no_verify is False

    def test_flag_sets_true(self):
        p = make_parser()
        verify.add_to(p)
        args = p.parse_args(["--no-verify"])
        assert args.no_verify is True


# ── yes ───────────────────────────────────────────────────────────────────────


class TestYes:
    def test_add_to_registers_flag(self):
        p = make_parser()
        yes.add_to(p)
        args = p.parse_args([])
        assert args.yes is False

    def test_long_flag(self):
        p = make_parser()
        yes.add_to(p)
        args = p.parse_args(["--yes"])
        assert args.yes is True

    def test_short_flag(self):
        p = make_parser()
        yes.add_to(p)
        args = p.parse_args(["-y"])
        assert args.yes is True


# ── model ─────────────────────────────────────────────────────────────────────


class TestModel:
    def test_default_value(self):
        p = make_parser()
        model.add_to(p)
        args = p.parse_args([])
        assert args.model == "gpt-5-mini"

    def test_custom_default(self):
        p = make_parser()
        model.add_to(p, default="gpt-4o")
        args = p.parse_args([])
        assert args.model == "gpt-4o"

    def test_override_via_cli(self):
        p = make_parser()
        model.add_to(p)
        args = p.parse_args(["--model", "claude-3"])
        assert args.model == "claude-3"

    def test_default_model_constant(self):
        assert model.DEFAULT_MODEL == "gpt-5-mini"


# ── prompt ────────────────────────────────────────────────────────────────────


class TestPrompt:
    def test_default_is_none(self):
        p = make_parser()
        prompt.add_to(p)
        args = p.parse_args([])
        assert args.prompt is None

    def test_long_flag(self):
        p = make_parser()
        prompt.add_to(p)
        args = p.parse_args(["--prompt", "優先保留細節"])
        assert args.prompt == "優先保留細節"

    def test_short_flag(self):
        p = make_parser()
        prompt.add_to(p)
        args = p.parse_args(["-p", "high quality"])
        assert args.prompt == "high quality"


# ── params_file ───────────────────────────────────────────────────────────────


class TestParamsFile:
    def test_default_is_none(self):
        p = make_parser()
        params_file.add_to(p)
        args = p.parse_args([])
        assert args.params_file is None

    def test_set_path(self):
        p = make_parser()
        params_file.add_to(p)
        args = p.parse_args(["--params-file", "params_20240101.json"])
        assert args.params_file == "params_20240101.json"


# ── vmaf_feedback ─────────────────────────────────────────────────────────────


class TestVmafFeedback:
    def test_default_is_none(self):
        p = make_parser()
        vmaf_feedback.add_to(p)
        args = p.parse_args([])
        assert args.vmaf_feedback is None

    def test_set_path(self):
        p = make_parser()
        vmaf_feedback.add_to(p)
        args = p.parse_args(["--vmaf-feedback", "vmaf_20240101.json"])
        assert args.vmaf_feedback == "vmaf_20240101.json"


# ── vmaf ──────────────────────────────────────────────────────────────────────


class TestVmaf:
    def test_default_is_none(self):
        p = make_parser()
        vmaf.add_to(p)
        args = p.parse_args([])
        assert args.vmaf is None

    def test_flag_without_value_defaults_to_1(self):
        """--vmaf 不帶數字時 const=1"""
        p = make_parser()
        vmaf.add_to(p)
        args = p.parse_args(["--vmaf"])
        assert args.vmaf == 1

    def test_flag_with_explicit_value(self):
        p = make_parser()
        vmaf.add_to(p)
        args = p.parse_args(["--vmaf", "5"])
        assert args.vmaf == 5

    def test_run_mode_same_behaviour(self):
        """run_mode 只影響 help 文字，行為相同"""
        p = make_parser()
        vmaf.add_to(p, run_mode=True)
        assert p.parse_args([]).vmaf is None
        assert p.parse_args(["--vmaf"]).vmaf == 1
        assert p.parse_args(["--vmaf", "3"]).vmaf == 3

    def test_invalid_value_raises(self):
        p = make_parser()
        vmaf.add_to(p)
        with pytest.raises(SystemExit):
            p.parse_args(["--vmaf", "abc"])


# ── preview ───────────────────────────────────────────────────────────────────


class TestPreview:
    def test_with_toggle_default(self):
        p = make_parser()
        preview.add_to(p)
        args = p.parse_args([])
        assert args.preview is False
        assert args.preview_duration == 30

    def test_toggle_flag(self):
        p = make_parser()
        preview.add_to(p)
        args = p.parse_args(["--preview"])
        assert args.preview is True

    def test_custom_duration(self):
        p = make_parser()
        preview.add_to(p)
        args = p.parse_args(["--preview-duration", "60"])
        assert args.preview_duration == 60

    def test_without_toggle(self):
        """run 子命令模式：不加 --preview 旗標"""
        p = make_parser()
        preview.add_to(p, include_toggle=False)
        # --preview 不應存在
        with pytest.raises(SystemExit):
            p.parse_args(["--preview"])

    def test_without_toggle_duration_still_works(self):
        p = make_parser()
        preview.add_to(p, include_toggle=False)
        args = p.parse_args(["--preview-duration", "45"])
        assert args.preview_duration == 45

    def test_invalid_duration_raises(self):
        p = make_parser()
        preview.add_to(p)
        with pytest.raises(SystemExit):
            p.parse_args(["--preview-duration", "abc"])


# ── auto_loop ─────────────────────────────────────────────────────────────────


class TestAutoLoop:
    def test_legacy_mode_default_is_none(self):
        """legacy 模式：不帶 --auto-loop 時為 None"""
        p = make_parser()
        auto_loop.add_to(p)
        args = p.parse_args([])
        assert args.auto_loop is None

    def test_legacy_mode_flag_without_value_defaults_to_3(self):
        """legacy 模式：--auto-loop 不帶數字時 const=3"""
        p = make_parser()
        auto_loop.add_to(p)
        args = p.parse_args(["--auto-loop"])
        assert args.auto_loop == 3

    def test_legacy_mode_explicit_value(self):
        p = make_parser()
        auto_loop.add_to(p)
        args = p.parse_args(["--auto-loop", "5"])
        assert args.auto_loop == 5

    def test_run_mode_default_is_2(self):
        """run 子命令模式：不帶 --auto-loop 時預設 2"""
        p = make_parser()
        auto_loop.add_to(p, run_mode=True)
        args = p.parse_args([])
        assert args.auto_loop == 2

    def test_run_mode_explicit_value(self):
        p = make_parser()
        auto_loop.add_to(p, run_mode=True)
        args = p.parse_args(["--auto-loop", "4"])
        assert args.auto_loop == 4

    def test_run_mode_requires_value(self):
        """run 模式不使用 nargs='?'，--auto-loop 後必須帶值"""
        p = make_parser()
        auto_loop.add_to(p, run_mode=True)
        with pytest.raises(SystemExit):
            p.parse_args(["--auto-loop"])

    def test_invalid_value_raises(self):
        p = make_parser()
        auto_loop.add_to(p)
        with pytest.raises(SystemExit):
            p.parse_args(["--auto-loop", "abc"])


# ── 組合測試：多個 flag 同時加入同一 parser ───────────────────────────────────


class TestComposed:
    def test_run_parser_composition(self):
        """模擬 _run_main 的 parser 組合"""
        p = make_parser()
        ffmpeg.add_to(p)
        vmaf.add_to(p, run_mode=True)
        auto_loop.add_to(p, run_mode=True)
        preview.add_to(p, include_toggle=False)
        model.add_to(p)
        prompt.add_to(p)

        args = p.parse_args(["--vmaf", "5", "--auto-loop", "3", "--model", "gpt-4o", "-p", "test"])
        assert args.ffmpeg is False
        assert args.vmaf == 5
        assert args.auto_loop == 3
        assert args.preview_duration == 30
        assert args.model == "gpt-4o"
        assert args.prompt == "test"

    def test_legacy_parser_composition(self):
        """模擬 _legacy_main 的 parser 組合"""
        p = make_parser()
        batch.add_to(p)
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

        args = p.parse_args(
            [
                "--batch",
                "--ffmpeg",
                "--vmaf",
                "4",
                "--preview",
                "--preview-duration",
                "60",
                "--yes",
                "--vmaf-feedback",
                "vmaf.json",
                "--model",
                "gpt-4o",
                "--auto-loop",
                "2",
                "-p",
                "test prompt",
                "--params-file",
                "params.json",
            ]
        )
        assert args.batch is True
        assert args.ffmpeg is True
        assert args.no_verify is False
        assert args.vmaf == 4
        assert args.preview is True
        assert args.preview_duration == 60
        assert args.yes is True
        assert args.vmaf_feedback == "vmaf.json"
        assert args.model == "gpt-4o"
        assert args.auto_loop == 2
        assert args.prompt == "test prompt"
        assert args.params_file == "params.json"

    def test_all_defaults(self):
        """全部預設值驗證"""
        p = make_parser()
        batch.add_to(p)
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

        args = p.parse_args([])
        assert args.batch is False
        assert args.ffmpeg is False
        assert args.no_verify is False
        assert args.vmaf is None
        assert args.preview is False
        assert args.preview_duration == 30
        assert args.yes is False
        assert args.vmaf_feedback is None
        assert args.model == "gpt-5-mini"
        assert args.auto_loop is None
        assert args.prompt is None
        assert args.params_file is None
