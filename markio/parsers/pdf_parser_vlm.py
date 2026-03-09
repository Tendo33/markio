from __future__ import annotations

from markio.parsers.pdf_parser import pdf_parse_main
from markio.settings import settings


async def pdf_parse_vlm_main(
    resource_path: str = "",
    parse_method: str = "auto",
    lang: str = "ch",
    save_parsed_content: bool = False,
    save_middle_content: bool = False,
    output_dir: str = "outputs",
    start_page: int = 0,
    end_page: int = None,
    server_url: str | None = None,
):
    backend = settings.pdf_parse_engine
    if backend.lower() == "pipeline":
        backend = "vlm-auto-engine"

    return await pdf_parse_main(
        resource_path=resource_path,
        parse_method=parse_method,
        lang=lang,
        save_parsed_content=save_parsed_content,
        save_middle_content=save_middle_content,
        output_dir=output_dir,
        start_page=start_page,
        end_page=end_page,
        backend=backend,
        server_url=server_url,
    )
