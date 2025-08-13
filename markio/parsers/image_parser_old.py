import os
from pathlib import Path

import cv2
from fastapi import HTTPException
from loguru import logger
from mineru.backend.pipeline.model_init import AtomModelSingleton
from mineru.backend.pipeline.model_list import AtomicModel

from markio.utils.file_utils import func_processing_time, process_resource_path


@func_processing_time
async def image_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "",
):
    """
    Parse images and extract text content using OCR, converting to Markdown format.

    This parser uses direct OCR model calls for text extraction from images, supporting:
    - Various image formats (PNG, JPG, JPEG, WEBP, etc.)
    - Multi-language text recognition
    - Text layout preservation
    - Automatic text direction detection
    - Support for both local file paths and URLs

    Args:
        img_file_path: Path to the image file to be parsed or URL
        save_parsed_content: Whether to save extracted text to markdown file
        output_dir: Directory where parsed content will be saved

    Returns:
        str: Extracted text content in Markdown format

    Raises:
        FileNotFoundError: If file not found or not accessible
        ValueError: If image file is invalid or corrupted
        Exception: For other errors during parsing or OCR processing
    """
    local_img_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_img_path)
    file_name = file_path.stem

    if not os.path.exists(local_img_path):
        raise FileNotFoundError(
            f"Error: Image file not found at {local_img_path}. Please check the file path."
        )

    try:
        atom_model_manager = AtomModelSingleton()
        ocr_model = atom_model_manager.get_atom_model(
            atom_model_name=AtomicModel.OCR, det_db_box_thresh=0.3, lang=None
        )
    except Exception as e:
        logger.error(f"Failed to initialize OCR model: {e}")
        raise HTTPException(
            status_code=500, detail=f"OCR model initialization failed: {str(e)}"
        )

    try:
        new_image = cv2.imread(local_img_path)

        if new_image is None:
            raise FileNotFoundError(
                f"Error: Unable to load image at {local_img_path}. Please check the file path."
            )

        new_image_rgb = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)

    except Exception as e:
        raise ValueError(f"Error: Unable to read image file {local_img_path}: {e}")

    if save_parsed_content:
        if not output_dir:
            raise ValueError("output_dir is required when save_parsed_content is True")

        output_path = os.path.join(output_dir, file_name)
        os.makedirs(output_path, exist_ok=True)

    try:
        ocr_result = ocr_model.ocr(new_image_rgb)[0]

        detected_texts = [item[1][0] for item in ocr_result] if ocr_result else []

        final_text = "\n".join(detected_texts)

        markdown_content = _convert_to_markdown(final_text, detected_texts, file_name)

        if save_parsed_content:
            md_file_path = os.path.join(output_path, f"{file_name}.md")
            with open(md_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

        logger.info(f"Image {file_name} saved to {output_path}")
        return markdown_content

    except Exception as e:
        logger.error(f"Error occurred during image parsing: {e}")
        raise HTTPException(status_code=500, detail=f"Image parsing failed: {str(e)}")


def _convert_to_markdown(final_text: str, detected_texts: list, file_name: str) -> str:
    """
    Convert OCR results to markdown format.

    Args:
        final_text (str): Combined text from OCR
        detected_texts (list): List of detected text strings
        file_name (str): Name of the image file

    Returns:
        str: Markdown formatted text with basic structure
    """
    if not detected_texts:
        return f"# {file_name}\n\n*No text content detected*"

    markdown_lines = [f"# {file_name}\n"]

    markdown_lines.append(final_text)

    return "\n".join(markdown_lines)
