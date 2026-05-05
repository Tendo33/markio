from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Awaitable, Callable

from markio.schemas.task_schemas import SubmitTaskRequest, TaskStatus

logger = logging.getLogger(__name__)

ParserFunc = Callable[[str, SubmitTaskRequest], Awaitable[str]]
CacheGetter = Callable[[str], Awaitable[str | None]]
CacheSetter = Callable[[str, str], Awaitable[bool]]


class BaseTaskManager:
    def __init__(
        self,
        parser_func: ParserFunc | None = None,
        cache_getter: CacheGetter | None = None,
        cache_setter: CacheSetter | None = None,
    ) -> None:
        if parser_func is None:
            from markio.services.document_service import parse_local_file

            parser_func = parse_local_file

        self.parser_func = parser_func
        self.cache_getter = cache_getter
        self.cache_setter = cache_setter

    def _build_cache_key(self, request: SubmitTaskRequest) -> str:
        try:
            hasher = hashlib.sha256()
            with open(request.file_path, "rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    hasher.update(chunk)
        except FileNotFoundError:
            return ""

        owner_id = (request.owner_id or "").strip() or "anonymous"
        extension = os.path.splitext(request.filename or "")[1].lower()
        options: dict[str, object] = {
            "owner_id": owner_id,
            "extension": extension,
        }
        if extension == ".pdf":
            options.update(
                {
                    "parse_method": request.parse_method,
                    "lang": request.lang,
                    "save_middle_content": request.save_middle_content,
                    "start_page": request.start_page,
                    "end_page": request.end_page,
                    "engine": os.getenv("PDF_PARSE_ENGINE", "pipeline"),
                }
            )
        options_digest = hashlib.sha256(
            json.dumps(options, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        return f"markio:result:{hasher.hexdigest()}:{options_digest}"

    async def _safe_cache_get(self, cache_key: str) -> str | None:
        if not self.cache_getter:
            return None
        try:
            result = await self.cache_getter(cache_key)
            if isinstance(result, str) and result:
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache get failed for {cache_key}: {exc}")
        return None

    async def _safe_cache_set(self, cache_key: str | None, value: str) -> None:
        if not cache_key or not self.cache_setter:
            return
        try:
            await self.cache_setter(cache_key, value)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Cache set failed for {cache_key}: {exc}")

    @staticmethod
    def _normalize_status_filter(status: TaskStatus | str | None) -> TaskStatus | None:
        if status is None:
            return None
        if isinstance(status, TaskStatus):
            return status
        return TaskStatus(status)

    @staticmethod
    def _cleanup_temp_file(file_path: str) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to clean up temp file {file_path}: {exc}")
