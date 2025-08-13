from typing import Optional

from pydantic import BaseModel, Field


class ApplicationConfig(BaseModel):
    """
    Application configuration class for defining and managing application configuration items.
    Supports reading configuration from environment variables.
    """

    output_dir: str = Field(
        default="outputs",
        description="Directory path for output files",
        alias="OUTPUT_DIR",
    )

    log_dir: str = Field(
        default="logs",
        description="Directory path for log files",
        alias="LOG_DIR",
    )

    log_level: str = Field(
        default="INFO",
        description="Log level, options: DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is INFO",
        alias="LOG_LEVEL",
    )

    # PDF parsing engine configuration
    pdf_parse_engine: str = Field(
        default="pipeline",
        description="PDF parsing engine selection, options: 'pipeline' or 'vlm-sglang-engine'",
        alias="PDF_PARSE_ENGINE",
    )

    # VLM related configuration
    vlm_server_url: Optional[str] = Field(
        default=None,
        description="VLM server URL, required when using vlm-sglang-client engine",
        alias="VLM_SERVER_URL",
    )

    # MINERU related configuration
    mineru_min_batch_inference_size: int = Field(
        default=256,
        description="MINERU model inference minimum batch size",
        alias="MINERU_MIN_BATCH_INFERENCE_SIZE",
    )

    mineru_device_mode: str = Field(
        default="cuda",
        description="MINERU model device mode, such as 'cuda' or 'cpu'",
        alias="MINERU_DEVICE_MODE",
    )

    mineru_model_source: str = Field(
        default="local",
        description="MINERU model source, such as 'local' or 'remote'",
        alias="MINERU_MODEL_SOURCE",
    )

    mineru_virtual_vram_size: int = Field(
        default=8192,
        description="MINERU virtual VRAM size (MB), default 8GB",
        alias="MINERU_VIRTUAL_VRAM_SIZE",
    )

    vlm_mem_fraction_static: float = Field(
        default=0.5,
        description="VLM memory fraction static, default 0.5",
        alias="VLM_MEM_FRACTION_STATIC",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True
