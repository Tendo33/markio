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

    # Redis configuration
    redis_host: str = Field(
        default="localhost",
        description="Redis server host address",
        alias="REDIS_HOST",
    )

    redis_port: int = Field(
        default=6379,
        description="Redis server port",
        alias="REDIS_PORT",
    )

    redis_db: int = Field(
        default=0,
        description="Redis database index (0-15)",
        alias="REDIS_DB",
    )

    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password (optional)",
        alias="REDIS_PASSWORD",
    )

    redis_enabled: bool = Field(
        default=False,
        description="Enable Redis caching and features",
        alias="REDIS_ENABLED",
    )

    redis_max_connections: int = Field(
        default=50,
        description="Maximum number of Redis connections in the pool",
        alias="REDIS_MAX_CONNECTIONS",
    )

    redis_socket_timeout: int = Field(
        default=5,
        description="Redis socket timeout in seconds",
        alias="REDIS_SOCKET_TIMEOUT",
    )

    redis_socket_connect_timeout: int = Field(
        default=5,
        description="Redis socket connect timeout in seconds",
        alias="REDIS_SOCKET_CONNECT_TIMEOUT",
    )

    redis_default_ttl: int = Field(
        default=3600,
        description="Default TTL (time to live) for cached items in seconds",
        alias="REDIS_DEFAULT_TTL",
    )

    task_worker_count: int = Field(
        default=2,
        description="Number of async workers for background parsing tasks",
        alias="TASK_WORKER_COUNT",
    )

    task_queue_backend: str = Field(
        default="memory",
        description="Task queue backend: 'memory' or 'redis'",
        alias="TASK_QUEUE_BACKEND",
    )

    task_history_limit: int = Field(
        default=500,
        description="Maximum number of task records kept in memory",
        alias="TASK_HISTORY_LIMIT",
    )

    task_state_file: str = Field(
        default="data/task_state.json",
        description="Path to persisted async task state file",
        alias="TASK_STATE_FILE",
    )

    task_upload_dir: str = Field(
        default="data/task_uploads",
        description="Directory for uploaded async task source files",
        alias="TASK_UPLOAD_DIR",
    )

    task_max_auto_retries: int = Field(
        default=0,
        description="Maximum automatic retries after task failures",
        alias="TASK_MAX_AUTO_RETRIES",
    )

    task_retry_delay_seconds: float = Field(
        default=0.0,
        description="Delay in seconds before automatic task retry",
        alias="TASK_RETRY_DELAY_SECONDS",
    )

    task_processing_timeout_seconds: float = Field(
        default=0.0,
        description="Processing timeout before requeue (seconds)",
        alias="TASK_PROCESSING_TIMEOUT_SECONDS",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True
        extra = "ignore"  # 忽略额外字段，提高兼容性
