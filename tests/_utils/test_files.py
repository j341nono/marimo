from __future__ import annotations

from pathlib import Path

import pytest

from marimo._utils.files import (
    async_expand_file_patterns,
    expand_file_patterns,
)


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize(
    ("pattern", "expected_names"),
    [
        ("*.py", ["top.py"]),
        ("./*.py", ["top.py"]),
        ("**/*.py", ["sub/deep/last.py", "sub/nested.py", "top.py"]),
        ("sub/**/*.py", ["sub/deep/last.py", "sub/nested.py"]),
        ("*/*.py", ["sub/nested.py"]),
        ("sub/neste?.py", ["sub/nested.py"]),
        ("**/missing*.py", []),
    ],
)
async def test_expand_file_patterns_respects_path_segments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    absolute: bool,
    pattern: str,
    expected_names: list[str],
) -> None:
    for name in [
        "top.py",
        "top.txt",
        "sub/nested.py",
        "sub/deep/last.py",
        ".cache/ignored.py",
        "sub/.cache/ignored.py",
    ]:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    monkeypatch.chdir(tmp_path)
    if absolute:
        pattern = str(tmp_path / pattern)
    expected = sorted(
        tmp_path / name if absolute else Path(name) for name in expected_names
    )

    sync_files = expand_file_patterns((pattern,))
    async_files = sorted(
        [path async for path in async_expand_file_patterns((pattern,))]
    )

    assert (sync_files, async_files) == (expected, expected)


async def test_expand_file_patterns_preserves_directory_and_explicit_paths(
    tmp_path: Path,
) -> None:
    (tmp_path / "sub").mkdir()
    first = tmp_path / "top.py"
    nested = tmp_path / "sub" / "nested.py"
    hidden_file = tmp_path / ".hidden.py"
    for path in [first, nested, hidden_file]:
        path.touch()
    patterns = (str(tmp_path), str(first), str(tmp_path / "**" / "*.py"))
    expected = sorted([first, nested, hidden_file])

    sync_files = expand_file_patterns(patterns)
    async_files = sorted(
        [path async for path in async_expand_file_patterns(patterns)]
    )

    assert (sync_files, async_files) == (expected, expected)
