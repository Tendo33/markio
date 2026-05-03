from pathlib import Path

import pytest
from fastapi import HTTPException

from markio.routers._request_guards import resolve_strict_output_dir


def test_resolve_strict_output_dir_accepts_relative_subdir_within_base(tmp_path: Path):
    base_dir = tmp_path / "outputs"

    resolved = resolve_strict_output_dir("jobs/demo-1", str(base_dir))

    assert resolved == str((base_dir / "jobs" / "demo-1").resolve())


def test_resolve_strict_output_dir_preserves_existing_outputs_prefixed_path(tmp_path: Path):
    base_dir = tmp_path / "outputs"
    prefixed = Path(base_dir.name) / "jobs" / "demo-1"

    resolved = resolve_strict_output_dir(str(prefixed), str(base_dir))

    assert resolved == str((base_dir / "jobs" / "demo-1").resolve())


def test_resolve_strict_output_dir_rejects_parent_escape(tmp_path: Path):
    base_dir = tmp_path / "outputs"

    with pytest.raises(HTTPException) as exc_info:
        resolve_strict_output_dir("../escape", str(base_dir))

    assert exc_info.value.status_code == 400
    assert "Invalid output_dir" in str(exc_info.value.detail)
