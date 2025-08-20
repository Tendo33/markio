import asyncio
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import islice
from typing import Dict, Iterator, List

from markio.parsers.doc_parser import doc_parse_main
from markio.parsers.docx_parser import docx_parse_main
from markio.parsers.epub_parser import epub_parse_main
from markio.parsers.html_parser import html_parse_main
from markio.parsers.image_parser import image_parse_main
from markio.parsers.pdf_parser import pdf_parse_main
from markio.parsers.pdf_parser_vlm import pdf_parse_vlm_main
from markio.parsers.ppt_parser import ppt_parse_main
from markio.parsers.pptx_parser import pptx_parse_main
from markio.parsers.url_parser import url_parse_main
from markio.parsers.xlsx_parser import xlsx_parse_main
from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


# Select PDF parser based on environment variables
pdf_parse_engine = settings.pdf_parse_engine
if pdf_parse_engine == "pipeline":
    pdf_parser_func = pdf_parse_main
elif pdf_parse_engine == "vlm-sglang-engine":
    pdf_parser_func = pdf_parse_vlm_main
else:
    logger.warning(
        f"Invalid PDF_PARSE_ENGINE: {pdf_parse_engine}, using pipeline as default"
    )
    pdf_parser_func = pdf_parse_main

logger.info(f"Using PDF parse engine: {pdf_parse_engine}")

# Define parser function mapping
FUNCTION_MAP = {
    "pdf": pdf_parser_func,
    "img": image_parse_main,
    "doc": doc_parse_main,
    "ppt": ppt_parse_main,
    "pptx": pptx_parse_main,
    "html": html_parse_main,
    "docx": docx_parse_main,
    "url": url_parse_main,
    "xlsx": xlsx_parse_main,
    "epub": epub_parse_main,
}


def parameter_adapter(file_ext: str, **kwargs) -> Dict:
    """Adapt parameters based on file type.

    This function adapts the common parameters and file-specific parameters for each parser.
    It ensures that each parser receives the correct parameters it needs.

    Args:
        file_ext: The file extension/type to determine which parser to use
        **kwargs: Additional parameters passed to the parser

    Returns:
        Dict: A dictionary of parameters adapted for the specific parser
    """
    # Common parameters that most parsers support
    common_params = {
        "resource_path": kwargs.get("file_path", ""),
        "save_parsed_content": kwargs.get("save_parsed_content", False),
        "output_dir": kwargs.get("output_dir", ""),
    }

    # File-specific parameters for each parser type
    file_params = {
        "pdf": {
            "resource_path": kwargs.get("file_path", ""),
            "parse_method": kwargs.get("parse_method", "auto"),
            "lang": kwargs.get("lang", "ch"),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "save_middle_content": kwargs.get("save_middle_content", False),
            "output_dir": kwargs.get("output_dir", "outputs"),
            "start_page": kwargs.get("start_page", 0),
            "end_page": kwargs.get("end_page"),
        },
        "img": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
            "parse_backend": kwargs.get("parse_backend", "pipeline"),
        },
        "docx": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "doc": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "ppt": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "pptx": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "html": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "htm": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "xlsx": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "epub": {
            "resource_path": kwargs.get("file_path", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
        "url": {
            "resource_path": kwargs.get("url", ""),
            "save_parsed_content": kwargs.get("save_parsed_content", False),
            "output_dir": kwargs.get("output_dir", ""),
        },
    }

    # Validate required parameters
    if file_ext not in file_params:
        raise ValueError(f"Unsupported file type: {file_ext}")

    if file_ext == "url" and not kwargs.get("url"):
        raise ValueError("URL is required for URL parser")
    elif file_ext != "url" and not kwargs.get("file_path"):
        raise ValueError(f"File path is required for {file_ext} parser")

    if kwargs.get("save_parsed_content") and not kwargs.get("output_dir"):
        raise ValueError(
            "Output directory is required when save_parsed_content is True"
        )

    # Combine common and file-specific parameters
    params = {**common_params, **file_params.get(file_ext, {})}

    # Remove None values to avoid passing None to parser functions
    params = {k: v for k, v in params.items() if v is not None}

    return params


async def process_file_with_adapter(file_ext: str, **kwargs) -> None:
    """Process file using the appropriate parser function with improved error handling.

    Args:
        file_ext: The file extension/type to determine which parser to use
        **kwargs: Additional parameters passed to the parser
    """
    if file_ext not in FUNCTION_MAP:
        logger.warning(f"Unsupported file type: {file_ext}")
        return

    parse_function = FUNCTION_MAP[file_ext]

    try:
        # Adapt parameters for the specific parser
        params = parameter_adapter(file_ext, **kwargs)

        logger.info(
            f"Processing {kwargs.get('file_name', 'unnamed')}.{file_ext} with params: {params}"
        )

        # Execute the parser function
        result = await parse_function(**params)

        if isinstance(result, str):
            logger.info(
                f"Successfully processed {kwargs.get('file_name', 'unnamed')}.{file_ext}"
            )
        else:
            logger.warning(f"Parser returned unexpected result type: {type(result)}")

    except ValueError as e:
        logger.error(
            f"Parameter error for {kwargs.get('file_name', 'unnamed')}.{file_ext}: {e}"
        )
    except FileNotFoundError as e:
        logger.error(
            f"File not found for {kwargs.get('file_name', 'unnamed')}.{file_ext}: {e}"
        )
    except Exception as e:
        logger.error(
            f"Error processing {kwargs.get('file_name', 'unnamed')}.{file_ext}: {e}"
        )
        logger.exception("Detailed error information:")


async def process_file(file_path: str, **kwargs) -> None:
    """Process a single file."""
    file_ext = os.path.splitext(file_path)[-1][1:].lower()
    file_name = os.path.basename(file_path).split(".")[0]
    if file_ext in FUNCTION_MAP:
        await process_file_with_adapter(
            file_ext=file_ext,
            file_path=file_path,
            file_name=file_name,
            **kwargs,
        )
    else:
        logger.warning(f"Unsupported file type: {file_name}.{file_ext}")


class ConcurrentProcessor:
    """Concurrent processor with multiple processing strategies."""

    def __init__(self, max_workers: int = 4, use_process_pool: bool = False):
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool
        self.executor_class = (
            ProcessPoolExecutor if use_process_pool else ThreadPoolExecutor
        )
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_file_with_semaphore(self, file_path: str, **kwargs) -> None:
        """Process file with semaphore-controlled concurrency."""
        async with self.semaphore:
            await process_file(file_path, **kwargs)

    async def process_files_concurrent(self, files: List[str], **kwargs) -> None:
        """Process file list concurrently."""
        tasks = [
            self.process_file_with_semaphore(file_path, **kwargs) for file_path in files
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_files_batched(
        self, files: List[str], batch_size: int, **kwargs
    ) -> None:
        """Process files in batches concurrently."""
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} files")
            await self.process_files_concurrent(batch, **kwargs)


def get_all_files(folder_path: str) -> List[str]:
    """Get all file paths in a directory."""
    return [
        os.path.join(root, filename)
        for root, _, filenames in os.walk(folder_path)
        for filename in filenames
    ]


def chunked_iterable(iterable: List[str], size: int) -> Iterator[List[str]]:
    """Chunk an iterable into smaller parts."""
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


async def process_files_in_folder_submit(
    folder_path: str,
    max_workers: int,
    batch_size: int,
    **kwargs,
) -> None:
    """Process files in a folder using asyncio tasks."""
    if os.path.isdir(folder_path):
        files = get_all_files(folder_path)
    elif os.path.isfile(folder_path):
        files = [folder_path]
    else:
        logger.error(f"Invalid path: {folder_path} is neither a file nor a directory.")
        return

    if not files:
        logger.warning(f"No files found in folder {folder_path}")
        return

    logger.info(f"Found {len(files)} files to process in {folder_path}")

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = []
        for batch in chunked_iterable(files, batch_size):
            logger.info(f"Starting processing batch of {len(batch)} files")
            for file in batch:
                task = loop.run_in_executor(
                    executor,
                    process_file,
                    file,
                    **kwargs,
                )
                tasks.append(task)
        await asyncio.gather(*tasks)


async def process_files_in_folder(
    folder_path: str,
    max_workers: int = 4,
    batch_size: int = 10,
    use_process_pool: bool = False,
    **kwargs,
) -> None:
    """Process files in folder with improved concurrency control."""
    if os.path.isdir(folder_path):
        files = get_all_files(folder_path)
    elif os.path.isfile(folder_path):
        files = [folder_path]
    else:
        logger.error(f"Invalid path: {folder_path} is neither a file nor a directory.")
        return

    if not files:
        logger.warning(f"No files found in folder {folder_path}")
        return

    logger.info(f"Found {len(files)} files to process in {folder_path}")

    # Filter supported file types
    supported_files = [
        f for f in files if os.path.splitext(f)[-1][1:].lower() in FUNCTION_MAP
    ]

    if not supported_files:
        logger.warning("No supported file types found")
        return

    logger.info(f"Processing {len(supported_files)} supported files")

    # Create concurrent processor
    processor = ConcurrentProcessor(max_workers, use_process_pool)

    start_time = time.time()

    try:
        await processor.process_files_batched(supported_files, batch_size, **kwargs)

        elapsed_time = time.time() - start_time
        logger.info(f"Processing completed in {elapsed_time:.2f} seconds")
        logger.info(
            f"Average time per file: {elapsed_time / len(supported_files):.2f} seconds"
        )

    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        raise


def merge_json_files(root_folder: str, output_file: str, file_type: str) -> None:
    """Merge JSON or JSONL files."""
    merged_data = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if file_path == output_file:
                continue
            try:
                if file_type == "json" and filename.endswith(".json"):
                    with open(file_path, "r", encoding="utf-8") as file:
                        merged_data.append(json.load(file))
                elif file_type == "jsonl" and filename.endswith(".jsonl"):
                    with open(file_path, "r", encoding="utf-8") as file:
                        merged_data.extend(json.loads(line) for line in file)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error parsing {file_path}: {e}")
    try:
        with open(output_file, "w", encoding="utf-8") as output_file_obj:
            if file_type == "json":
                json.dump(merged_data, output_file_obj, ensure_ascii=False, indent=4)
            elif file_type == "jsonl":
                for data in merged_data:
                    json.dump(data, output_file_obj, ensure_ascii=False)
                    output_file_obj.write("\n")
        logger.info(f"Merged {len(merged_data)} items into {output_file}")
    except IOError as e:
        logger.error(f"Error writing to {output_file}: {e}")


async def main():
    """Main function with hardcoded configuration parameters."""
    folder_path = "./input_files"
    max_workers = 4
    batch_size = 10
    use_process_pool = False
    merged_output_path = "./outputs/merged_output.jsonl"
    output_dir = "./outputs"

    parse_method = "auto"
    lang = "ch"
    save_parsed_content = True
    save_middle_content = False
    parse_backend = "pipeline"

    start_page = 0
    end_page = None

    try:
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Starting improved file processing...")
        logger.info(
            f"Configuration: max_workers={max_workers}, batch_size={batch_size}, use_process_pool={use_process_pool}"
        )
        logger.info(
            f"Parser config: parse_method={parse_method}, lang={lang}, parse_backend={parse_backend}"
        )
        logger.info(
            f"Output config: save_parsed_content={save_parsed_content}, save_middle_content={save_middle_content}"
        )

        await process_files_in_folder(
            folder_path=folder_path,
            max_workers=max_workers,
            batch_size=batch_size,
            use_process_pool=use_process_pool,
            parse_method=parse_method,
            lang=lang,
            save_parsed_content=save_parsed_content,
            save_middle_content=save_middle_content,
            output_dir=output_dir,
            parse_backend=parse_backend,
            start_page=start_page,
            end_page=end_page,
        )

        if merged_output_path:
            file_type = "json" if merged_output_path.endswith(".json") else "jsonl"
            logger.info(f"Merging JSON files into {merged_output_path}")
            merge_json_files(
                root_folder=output_dir,
                output_file=merged_output_path,
                file_type=file_type,
            )

        logger.info("Processing completed successfully")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        logger.exception("Detailed error information:")
        raise


if __name__ == "__main__":
    asyncio.run(main())
