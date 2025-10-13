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
        description="PDF parsing engine selection, options: 'pipeline', 'vlm-vllm-engine', 'vlm-vllm-client'",
        alias="PDF_PARSE_ENGINE",
    )

    # VLM related configuration
    vlm_server_url: Optional[str] = Field(
        default=None,
        description="VLM server URL, required when using vlm-vllm-client engine",
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

    vlm_gpu_memory_utilization: float = Field(
        default=0.9,
        description="vLLM GPU memory utilization (0.0-1.0), default 0.9. Controls the fraction of GPU memory to use.",
        alias="VLM_GPU_MEMORY_UTILIZATION",
    )

    # Server configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address",
        alias="HOST",
    )

    port: int = Field(
        default=8000,
        description="Server port",
        alias="PORT",
    )

    # MCP configuration
    enable_mcp: bool = Field(
        default=False,
        description="Enable MCP server",
        alias="ENABLE_MCP",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True
        extra = "ignore"  # 忽略额外字段，提高兼容性
