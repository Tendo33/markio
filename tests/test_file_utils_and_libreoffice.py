import pytest

from markio.utils import file_utils
from markio.utils import libreoffice_converter


def test_create_temporary_file_re_raises_creation_error(monkeypatch):
    def _raise_create_error(*args, **kwargs):
        raise OSError("create failed")

    monkeypatch.setattr(file_utils, "NamedTemporaryFile", _raise_create_error)

    with pytest.raises(OSError, match="create failed"):
        with file_utils.create_temporary_file():
            pass


def test_check_libreoffice_installed_returns_false_when_binary_missing(monkeypatch):
    def _raise_missing_binary(*args, **kwargs):
        raise FileNotFoundError("soffice not found")

    monkeypatch.setattr(libreoffice_converter.subprocess, "run", _raise_missing_binary)
    assert libreoffice_converter.check_libreoffice_installed() is False


@pytest.mark.asyncio
async def test_process_resource_path_delegates_url_fetch_to_url_parser(monkeypatch, tmp_path):
    calls: list[tuple[str, str | None, str | None, int | None]] = []

    async def _fake_download_via_url_parser(
        url: str,
        output_dir: str | None = None,
        filename: str | None = None,
        timeout_seconds: int | None = None,
    ) -> str:
        calls.append((url, output_dir, filename, timeout_seconds))
        local_path = tmp_path / "downloaded.txt"
        local_path.write_text("ok", encoding="utf-8")
        return str(local_path)

    monkeypatch.setattr(
        "markio.parsers.url_parser.download_file_from_url",
        _fake_download_via_url_parser,
    )

    resolved = await file_utils.process_resource_path(
        resource_path="https://example.com/demo.txt",
        output_dir=str(tmp_path),
    )

    assert resolved == str(tmp_path / "downloaded.txt")
    assert calls == [("https://example.com/demo.txt", str(tmp_path), None, 300)]


@pytest.mark.asyncio
async def test_download_file_from_url_preserves_timeout_argument(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    async def _fake_download_via_url_parser(
        url: str,
        output_dir: str | None = None,
        filename: str | None = None,
        timeout_seconds: int | None = None,
    ) -> str:
        captured.update(
            {
                "url": url,
                "output_dir": output_dir,
                "filename": filename,
                "timeout_seconds": timeout_seconds,
            }
        )
        local_path = tmp_path / "timeout.txt"
        local_path.write_text("ok", encoding="utf-8")
        return str(local_path)

    monkeypatch.setattr(
        "markio.parsers.url_parser.download_file_from_url",
        _fake_download_via_url_parser,
    )

    resolved = await file_utils.download_file_from_url(
        "https://example.com/timeout.txt",
        output_path=str(tmp_path),
        timeout=17,
    )

    assert resolved == str(tmp_path / "timeout.txt")
    assert captured == {
        "url": "https://example.com/timeout.txt",
        "output_dir": str(tmp_path),
        "filename": None,
        "timeout_seconds": 17,
    }
