from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from marimo._runtime.layout.layout import (
    LayoutConfig,
    read_layout_config,
    save_layout_config,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


def test_save_layout_config(temp_dir: str):
    config = LayoutConfig(type="grid", data={"cols": 2})
    filepath = save_layout_config(temp_dir, "test.py", config)

    assert filepath == "layouts/test.grid.json"
    full_path = os.path.join(temp_dir, filepath)
    assert os.path.exists(full_path)

    with open(full_path) as f:
        saved_data = json.load(f)
    assert saved_data == {"type": "grid", "data": {"cols": 2}}


@pytest.mark.parametrize(
    ("app_name", "expected"),
    [
        ("demo.py.py", "layouts/demo.py.grid.json"),
        ("demo.pyramid.py", "layouts/demo.pyramid.grid.json"),
        ("demo.pyramid", "layouts/demo.pyramid.grid.json"),
        ("demo.md", "layouts/demo.md.grid.json"),
    ],
)
def test_save_layout_preserves_filename(
    tmp_path: Path, app_name: str, expected: str
) -> None:
    config = LayoutConfig(type="grid", data={"cols": 2})

    filepath = save_layout_config(tmp_path, app_name, config)

    assert filepath == expected
    assert read_layout_config(tmp_path, filepath) == config


def test_save_layout_does_not_overwrite_another_notebook(
    tmp_path: Path,
) -> None:
    first_config = LayoutConfig(type="grid", data={"cols": 2})
    second_config = LayoutConfig(type="grid", data={"cols": 5})

    first_path = save_layout_config(tmp_path, "demo.py.py", first_config)
    second_path = save_layout_config(tmp_path, "demo.py", second_config)

    assert (first_path, second_path) == (
        "layouts/demo.py.grid.json",
        "layouts/demo.grid.json",
    )
    assert (
        read_layout_config(tmp_path, first_path),
        read_layout_config(tmp_path, second_path),
    ) == (first_config, second_config)


def test_read_layout_config(temp_dir: str):
    # Create a test layout file
    config = LayoutConfig(type="grid", data={"cols": 2})
    filepath = save_layout_config(temp_dir, "test.py", config)

    # Read it back
    read_config = read_layout_config(temp_dir, filepath)
    assert read_config is not None
    assert read_config.type == "grid"
    assert read_config.data == {"cols": 2}


def test_read_layout_config_data_uri():
    # Create a data URI
    config_data = {"type": "grid", "data": {"cols": 2}}
    json_str = json.dumps(config_data)
    import base64

    data_uri = f"data:application/json;base64,{base64.b64encode(json_str.encode()).decode()}"

    # Read it
    config = read_layout_config("", data_uri)
    assert config is not None
    assert config.type == "grid"
    assert config.data == {"cols": 2}


def test_read_layout_config_nonexistent_file(temp_dir: str):
    config = read_layout_config(temp_dir, "nonexistent.json")
    assert config is None


def test_read_layout_config_invalid_extension(temp_dir: str):
    # Create a non-JSON file
    path = Path(temp_dir) / "invalid.txt"
    path.write_text('{"type": "grid", "data": {}}')

    config = read_layout_config(temp_dir, "invalid.txt")
    assert config is None


def test_read_layout_config_invalid_data_uri():
    config = read_layout_config("", "data:invalid")
    assert config is None


@pytest.mark.parametrize(
    "contents",
    ["invalid json", b"\xff\xfe", "[]", '{"type": 1, "data": []}'],
    ids=["json", "encoding", "root", "fields"],
)
def test_read_layout_config_invalid_contents(
    temp_dir: str, contents: str | bytes
) -> None:
    path = Path(temp_dir) / "layouts" / "invalid.slides.json"
    path.parent.mkdir(exist_ok=True)
    if isinstance(contents, bytes):
        path.write_bytes(contents)
    else:
        path.write_text(contents)

    assert read_layout_config(temp_dir, "layouts/invalid.slides.json") is None
