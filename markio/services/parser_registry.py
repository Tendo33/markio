from __future__ import annotations

from collections.abc import Awaitable, Callable

from markio.parsers import (
    doc_parser,
    docx_parser,
    epub_parser,
    html_parser,
    image_parser,
    pdf_parser,
    ppt_parser,
    pptx_parser,
    xlsx_parser,
)

ParserCallable = Callable[..., Awaitable[str]]


EXTENSION_PARSERS: dict[str, ParserCallable] = {
    ".doc": doc_parser.doc_parse_main,
    ".docx": docx_parser.docx_parse_main,
    ".pdf": pdf_parser.pdf_parse_main,
    ".ppt": ppt_parser.ppt_parse_main,
    ".pptx": pptx_parser.pptx_parse_main,
    ".xlsx": xlsx_parser.xlsx_parse_main,
    ".html": html_parser.html_parse_main,
    ".htm": html_parser.html_parse_main,
    ".epub": epub_parser.epub_parse_main,
    ".png": image_parser.image_parse_main,
    ".jpg": image_parser.image_parse_main,
    ".jpeg": image_parser.image_parse_main,
}


MIME_TYPES: dict[str, tuple[str, ...]] = {
    ".doc": ("application/msword",),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    ".pdf": ("application/pdf",),
    ".ppt": (
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ),
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    ".html": ("text/html",),
    ".htm": ("text/html",),
    ".epub": ("application/epub+zip", "application/zip"),
    ".png": ("image/png",),
    ".jpg": ("image/jpeg",),
    ".jpeg": ("image/jpeg",),
}


def get_parser_for_extension(extension: str) -> ParserCallable | None:
    return EXTENSION_PARSERS.get(extension.lower())


def get_supported_extensions() -> tuple[str, ...]:
    return tuple(sorted(EXTENSION_PARSERS.keys()))


def get_expected_mime_types(extension: str) -> tuple[str, ...]:
    return MIME_TYPES.get(extension.lower(), ())


def is_expected_mime_type(extension: str, content_type: str | None) -> bool:
    expected = get_expected_mime_types(extension)
    if not expected or not content_type:
        return True
    return content_type in expected
