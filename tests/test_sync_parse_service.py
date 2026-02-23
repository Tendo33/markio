from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from markio.services.sync_parse_service import run_uploaded_file_parser


@pytest.mark.asyncio
async def test_run_uploaded_file_parser_calls_parser_and_cleans_temp_file():
    upload = UploadFile(filename="demo.docx", file=BytesIO(b"demo"))
    seen_path = ""

    async def fake_parser(resource_path: str, flag: bool) -> str:
        nonlocal seen_path
        seen_path = resource_path
        assert Path(resource_path).exists()
        return "# parsed"

    result = await run_uploaded_file_parser(
        file=upload,
        parser=fake_parser,
        parser_args=(True,),
    )

    assert result == "# parsed"
    assert seen_path
    assert not Path(seen_path).exists()


@pytest.mark.asyncio
async def test_run_uploaded_file_parser_cleans_temp_file_on_error():
    upload = UploadFile(filename="demo.docx", file=BytesIO(b"demo"))
    seen_path = ""

    async def failing_parser(resource_path: str) -> str:
        nonlocal seen_path
        seen_path = resource_path
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await run_uploaded_file_parser(file=upload, parser=failing_parser)

    assert seen_path
    assert not Path(seen_path).exists()


@pytest.mark.asyncio
async def test_run_uploaded_file_parser_streams_in_chunks():
    class _FakeUpload:
        def __init__(self, payload: bytes):
            self.filename = "demo.bin"
            self._payload = payload
            self._offset = 0
            self.calls: list[int | None] = []

        async def read(self, size: int | None = None):
            self.calls.append(size)
            if self._offset >= len(self._payload):
                return b""
            if size is None:
                size = len(self._payload)
            chunk = self._payload[self._offset : self._offset + size]
            self._offset += len(chunk)
            return chunk

    fake_file = _FakeUpload(b"a" * (2 * 1024 * 1024 + 128))

    async def fake_parser(resource_path: str) -> str:
        return Path(resource_path).read_text(encoding="utf-8")

    result = await run_uploaded_file_parser(file=fake_file, parser=fake_parser)

    assert len(result) == len(fake_file._payload)
    assert 1024 * 1024 in fake_file.calls
    assert len(fake_file.calls) >= 3
