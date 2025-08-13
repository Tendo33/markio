import asyncio
import os
import subprocess
from pathlib import Path

from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


def check_libreoffice_installed() -> bool:
    """
    Check if LibreOffice is installed on the system.

    Returns:
        bool: True if LibreOffice is installed, False otherwise.
    """
    try:
        subprocess.run(
            ["soffice", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


async def convert_by_libreoffice(
    input_path: str,
    output_format: str,
    output_path: str = None,
    rm_original: bool = False,
) -> str:
    """
    Asynchronously convert a file to a different format using LibreOffice.

    Args:
        input_path (str): Path to the input file.
        output_format (str): Target output format (e.g., "docx", "pptx").
        output_path (str, optional): Path for the output file. Defaults to input file directory.
        rm_original (bool, optional): Whether to remove the original file after conversion. Defaults to False.

    Returns:
        str: Path to the converted file.

    Raises:
        FileNotFoundError: If LibreOffice is not installed or input file not found.
        ValueError: If the input or output format is not supported.
    """
    if not check_libreoffice_installed():
        logger.error(
            "LibreOffice is not installed. Please install using the command: sudo apt-get install libreoffice"
        )
        raise FileNotFoundError("LibreOffice is not installed.")

    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    input_format = Path(input_path).suffix.lower()[1:]  # Remove the dot
    if input_format not in ["doc", "docx", "ppt", "pptx"]:
        raise ValueError(f"Unsupported input format: {input_format}")
    if output_format not in ["docx", "pptx"]:
        raise ValueError(f"Unsupported output format: {output_format}")

    if not output_path:
        output_path = os.path.join(
            os.path.dirname(input_path),
            os.path.splitext(os.path.basename(input_path))[0] + f".{output_format}",
        )

    output_dir = os.path.dirname(output_path)
    logger.info(
        f"Converting [{input_path}] to [{output_path}] format [{output_format}]"
    )

    command = [
        "soffice",
        "--headless",
        "--convert-to",
        output_format,
        "--outdir",
        output_dir,
        input_path,
    ]

    # Asynchronously run the conversion command
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )

    # Wait for the process to complete
    await process.communicate()

    converted_file = os.path.join(
        output_dir, Path(input_path).stem + f".{output_format}"
    )
    if converted_file != output_path:
        os.rename(converted_file, output_path)

    if rm_original and input_path != output_path:
        os.remove(input_path)

    logger.info(f"Conversion complete: {output_path}")
    return output_path
