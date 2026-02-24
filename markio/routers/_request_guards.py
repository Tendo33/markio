from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from markio.services import parser_registry


def get_file_extension(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def validate_supported_extension(
    file_extension: str,
    *,
    allowed_extensions: Iterable[str] | None = None,
) -> str:
    normalized_extension = file_extension.lower()
    if allowed_extensions is None:
        supported_extensions = set(parser_registry.get_supported_extensions())
    else:
        supported_extensions = {ext.lower() for ext in allowed_extensions}

    if normalized_extension in supported_extensions:
        return normalized_extension

    supported_types = ", ".join(sorted(supported_extensions))
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type. Supported types are: {supported_types}",
    )


def warn_mime_mismatch(
    *,
    file_extension: str,
    content_type: str | None,
    logger: Any,
) -> None:
    if parser_registry.is_expected_mime_type(file_extension, content_type):
        return
    expected = ", ".join(parser_registry.get_expected_mime_types(file_extension)) or "unknown"
    logger.warning(
        "Upload MIME mismatch: extension=%s content_type=%s expected=%s",
        file_extension,
        content_type,
        expected,
    )


def validate_upload_file(
    file: UploadFile,
    *,
    logger: Any,
    allowed_extensions: Iterable[str] | None = None,
) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_extension = validate_supported_extension(
        get_file_extension(file.filename),
        allowed_extensions=allowed_extensions,
    )
    warn_mime_mismatch(
        file_extension=file_extension,
        content_type=file.content_type,
        logger=logger,
    )
    return file_extension


def resolve_strict_output_dir(requested: str, base: str) -> str:
    base_dir = Path(base).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    requested_path = Path(requested or base).expanduser()
    if requested_path.is_absolute():
        resolved_dir = requested_path.resolve()
    else:
        resolved_dir = (Path.cwd() / requested_path).resolve()

    try:
        resolved_dir.relative_to(base_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output_dir: must be within {base_dir}",
        ) from exc

    resolved_dir.mkdir(parents=True, exist_ok=True)
    return str(resolved_dir)


def resolve_parser_output_dir(
    *,
    requested_output_dir: str,
    base_output_dir: str,
    save_parsed_content: bool,
) -> str:
    validated_requested_dir = resolve_strict_output_dir(
        requested_output_dir or base_output_dir,
        base_output_dir,
    )
    if save_parsed_content:
        return validated_requested_dir
    return resolve_strict_output_dir(base_output_dir, base_output_dir)


def enforce_upload_size(*, bytes_written: int, max_bytes: int) -> None:
    if bytes_written <= max_bytes:
        return
    raise HTTPException(
        status_code=413,
        detail=(
            "Uploaded file is too large. "
            f"Maximum allowed size is {max_bytes} bytes."
        ),
    )


def cleanup_file_safely(file_path: str, *, logger: Any) -> None:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        logger.warning("Failed to clean temporary file: %s", file_path)
