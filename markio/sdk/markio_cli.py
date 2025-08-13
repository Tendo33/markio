import asyncio
from typing import Optional

import typer

from markio.sdk.markio_sdk import MarkioSDK

app = typer.Typer(help="Markio Document Parser CLI")
sdk = MarkioSDK()


@app.command()
def pdf(
    file_path: str = typer.Argument(..., help="Path to the PDF file"),
    parse_method: str = typer.Option(
        "auto", "--method", "-m", help="Parse method: auto|ocr|txt"
    ),
    save_parsed_content: bool = typer.Option(
        False, "--save", "-s", help="Save parsed content to file"
    ),
    save_middle_content: bool = typer.Option(
        False, "--save-middle", "-sm", help="Save intermediate files"
    ),
    start_page: int = typer.Option(0, "--start", "-st", help="Start page (0-based)"),
    end_page: Optional[int] = typer.Option(
        None, "--end", "-e", help="End page (inclusive)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a PDF file to Markdown."""

    async def run():
        result = await sdk.parse_pdf(
            file_path=file_path,
            parse_method=parse_method,
            save_parsed_content=save_parsed_content,
            save_middle_content=save_middle_content,
            start_page=start_page,
            end_page=end_page,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def pdf_vlm(
    file_path: str = typer.Argument(..., help="Path to the PDF file"),
    save_parsed_content: bool = typer.Option(
        False, "--save", "-s", help="Save parsed content to file"
    ),
    save_middle_content: bool = typer.Option(
        False, "--save-middle", "-sm", help="Save intermediate files"
    ),
    start_page: int = typer.Option(0, "--start", "-st", help="Start page (0-based)"),
    end_page: Optional[int] = typer.Option(
        None, "--end", "-e", help="End page (inclusive)"
    ),
    server_url: Optional[str] = typer.Option(
        None,
        "--server",
        "-sv",
        help="Server URL for sglang-client backend. If provided, uses sglang-client backend; otherwise uses sglang-engine backend.",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a PDF file to Markdown using VLM (Vision Language Model) backend."""

    async def run():
        result = await sdk.parse_pdf_vlm(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
            save_middle_content=save_middle_content,
            start_page=start_page,
            end_page=end_page,
            server_url=server_url,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def docx(
    file_path: str = typer.Argument(..., help="Path to the DOCX file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a DOCX file to Markdown."""

    async def run():
        result = await sdk.parse_docx(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def doc(
    file_path: str = typer.Argument(..., help="Path to the DOC file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a DOC file to Markdown (converts to DOCX using LibreOffice first)."""

    async def run():
        result = await sdk.parse_doc(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def pptx(
    file_path: str = typer.Argument(..., help="Path to the PPTX file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a PPTX file to Markdown."""

    async def run():
        result = await sdk.parse_pptx(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def ppt(
    file_path: str = typer.Argument(..., help="Path to the PPT file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a PPT file to Markdown (converts to PPTX using LibreOffice first)."""

    async def run():
        result = await sdk.parse_ppt(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def xlsx(
    file_path: str = typer.Argument(..., help="Path to the XLSX file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse an XLSX file to Markdown."""

    async def run():
        result = await sdk.parse_xlsx(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def html(
    file_path: str = typer.Argument(..., help="Path to the HTML file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse an HTML file to Markdown."""

    async def run():
        result = await sdk.parse_html(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def url(
    url: str = typer.Argument(..., help="URL to parse"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse a URL to Markdown."""

    async def run():
        result = await sdk.parse_url(
            url=url,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def epub(
    file_path: str = typer.Argument(..., help="Path to the EPUB file"),
    save_parsed_content: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save parsed content to file (images will be automatically extracted when True)",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse an EPUB file to Markdown."""

    async def run():
        result = await sdk.parse_epub(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


@app.command()
def image(
    file_path: str = typer.Argument(..., help="Path to the image file"),
    save_parsed_content: bool = typer.Option(
        False, "--save", "-s", help="Save parsed content to file"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
):
    """Parse an image file to Markdown (OCR)."""

    async def run():
        result = await sdk.parse_image(
            file_path=file_path,
            save_parsed_content=save_parsed_content,
        )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result["content"])
            typer.echo(f"Content saved to: {output}")
        else:
            typer.echo(result["content"])

    asyncio.run(run())


if __name__ == "__main__":
    app()
