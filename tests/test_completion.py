# Copyright (c) 2026 Titouan Christophe
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for `zcompose completion` and its `__list_apps` helper."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from zcompose import _COMPLETION_SCRIPTS, main

ZCOMPOSE_PY = str(Path(__file__).resolve().parent.parent / "zcompose.py")

FIXTURE = """
    name: completion test

    networks:
      zeth:
        ipv4: 192.0.2.0/24

    applications:
      server:
        source: .
        network: zeth
      client:
        source: .
        network: zeth
"""


def _write(tmp_path: Path, content: str, name: str = "zcompose.yml") -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return p


# ---------------------------------------------------------------- `completion`


@pytest.mark.parametrize(
    "shell,marker",
    [
        ("bash", "complete -F _zcompose zcompose"),
        ("zsh", "#compdef zcompose"),
        ("fish", "complete -c zcompose"),
    ],
)
def test_completion_script_contains_marker(shell: str, marker: str) -> None:
    assert marker in _COMPLETION_SCRIPTS[shell]


def test_completion_prints_script(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["completion", "bash"]) == 0
    assert "complete -F _zcompose zcompose" in capsys.readouterr().out


def test_list_apps_hidden_from_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "__list_apps" not in capsys.readouterr().out


# ---------------------------------------------------------------- `__list_apps`


def test_list_apps(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = _write(tmp_path, FIXTURE)
    assert main(["-f", str(p), "__list_apps"]) == 0
    assert capsys.readouterr().out.splitlines() == ["client", "server"]


def test_list_apps_default_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, FIXTURE)
    monkeypatch.chdir(tmp_path)
    assert main(["__list_apps"]) == 0
    assert capsys.readouterr().out.splitlines() == ["client", "server"]


def test_list_apps_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["-f", str(tmp_path / "nope.yml"), "__list_apps"]) == 0
    assert capsys.readouterr().out == ""


def test_list_apps_invalid_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = _write(tmp_path, "not: [valid")
    assert main(["-f", str(p), "__list_apps"]) == 0
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------- end-to-end shell completion


def _zcompose_shell_func(shell: str) -> str:
    if shell == "fish":
        return f"function zcompose; python3 {ZCOMPOSE_PY} $argv; end"
    return f'zcompose() {{ python3 "{ZCOMPOSE_PY}" "$@"; }}'


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not installed")
def test_bash_completion_lists_apps(tmp_path: Path) -> None:
    _write(tmp_path, FIXTURE)
    script = f"""
        {_zcompose_shell_func("bash")}
        source <(zcompose completion bash)
        COMP_WORDS=(zcompose build "")
        COMP_CWORD=2
        _zcompose
        echo "${{COMPREPLY[@]}}"
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(result.stdout.split()) == ["client", "server"]


@pytest.mark.skipif(shutil.which("zsh") is None, reason="zsh not installed")
def test_zsh_completion_lists_apps(tmp_path: Path) -> None:
    # Stub the completion-rendering builtins (`_describe`/`_files`/`compdef`)
    # so this exercises our own subcommand/app-name detection logic without
    # needing a full interactive `compinit`+widget completion context.
    _write(tmp_path, FIXTURE)
    script = f"""
        {_zcompose_shell_func("zsh")}
        _describe() {{ local name=$2; print -- "${{(@P)name}}"; }}
        _files() {{ :; }}
        compdef() {{ :; }}
        source <(zcompose completion zsh)
        words=(zcompose build "")
        CURRENT=3
        _zcompose
    """
    result = subprocess.run(
        ["zsh", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(result.stdout.split()) == ["client", "server"]


@pytest.mark.skipif(shutil.which("fish") is None, reason="fish not installed")
def test_fish_completion_lists_apps(tmp_path: Path) -> None:
    _write(tmp_path, FIXTURE)
    script = f"""
        {_zcompose_shell_func("fish")}
        zcompose completion fish | source
        complete -C "zcompose build "
    """
    result = subprocess.run(
        ["fish", "--no-config", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(result.stdout.split()) == ["client", "server"]
