from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    # Note: legacy values are kept for backward compatibility and normalized at
    # load time / on use via normalize_pdf_engine(). Do not remove them without
    # a migration, or existing deployments will fail config validation at startup.
    pdf_parse_engine: Literal[
        "pipeline",
        "vlm-engine",
        "hybrid-engine",
        "vlm-http-client",
        "hybrid-http-client",
        "vlm-vllm-engine",
        "vlm-vllm-client",
        "vlm-auto-engine",
        "hybrid-auto-engine",
    ] = Field(
        default="pipeline",
        description=(
            "PDF parsing engine selection. Options: 'pipeline' (pure CPU/GPU pipeline), "
            "'vlm-engine' (local VLM, auto-selects inference engine), "
            "'hybrid-engine' (pipeline + VLM), 'vlm-http-client' / 'hybrid-http-client' "
            "(remote OpenAI-compatible endpoint, requires VLM_SERVER_URL). "
            "Legacy 'vlm-vllm-engine'/'vlm-vllm-client'/'vlm-auto-engine'/'hybrid-auto-engine' "
            "values remain accepted for backward compatibility."
        ),
        alias="PDF_PARSE_ENGINE",
    )

    # VLM related configuration
    vlm_server_url: Optional[str] = Field(
        default=None,
        description="VLM server URL, required when using vlm-http-client or hybrid-http-client engine",
        alias="VLM_SERVER_URL",
    )

    # MINERU related configuration
    mineru_min_batch_inference_size: int = Field(
        default=256,
        description="MINERU model inference minimum batch size",
        alias="MINERU_MIN_BATCH_INFERENCE_SIZE",
    )

    mineru_device_mode: Literal["cuda", "cpu", "mps"] = Field(
        default="cuda",
        description="MINERU model device mode, such as 'cuda' or 'cpu'",
        alias="MINERU_DEVICE_MODE",
    )

    mineru_model_source: Literal["local", "remote"] = Field(
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

    cors_allow_origins: str = Field(
        default="",
        description="Comma-separated CORS allowlist origins. Empty value disables cross-origin access.",
        alias="CORS_ALLOW_ORIGINS",
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Whether to allow credentials in CORS responses.",
        alias="CORS_ALLOW_CREDENTIALS",
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

    task_queue_backend: Literal["memory", "redis"] = Field(
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

    task_state_result_max_chars: int = Field(
        default=0,
        description="Maximum result chars persisted in task state file. 0 disables result persistence.",
        alias="TASK_STATE_RESULT_MAX_CHARS",
    )

    task_upload_dir: str = Field(
        default="data/task_uploads",
        description="Directory for uploaded async task source files",
        alias="TASK_UPLOAD_DIR",
    )

    task_max_upload_size_bytes: int = Field(
        default=50 * 1024 * 1024,
        description="Maximum file size (bytes) for async task uploads",
        alias="TASK_MAX_UPLOAD_SIZE_BYTES",
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
        description="Redis backend only: processing timeout before requeue (seconds)",
        alias="TASK_PROCESSING_TIMEOUT_SECONDS",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable lightweight per-IP, per-route rate limiting",
        alias="RATE_LIMIT_ENABLED",
    )

    rate_limit_requests: int = Field(
        default=120,
        description="Allowed requests in each rate-limit window",
        alias="RATE_LIMIT_REQUESTS",
    )

    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate-limit window size in seconds",
        alias="RATE_LIMIT_WINDOW_SECONDS",
    )

    rate_limit_max_buckets: int = Field(
        default=5000,
        description="Maximum in-memory rate-limit buckets to avoid unbounded growth",
        alias="RATE_LIMIT_MAX_BUCKETS",
    )

    rate_limit_trust_proxy_headers: bool = Field(
        default=False,
        description="Trust Forwarded/X-Forwarded-For headers for rate-limit client IP detection",
        alias="RATE_LIMIT_TRUST_PROXY_HEADERS",
    )

    url_fetch_mode: Literal["direct", "jina_proxy"] = Field(
        default="direct",
        description="URL fetch mode: 'direct' or 'jina_proxy'",
        alias="URL_FETCH_MODE",
    )

    url_proxy_base: str = Field(
        default="https://r.jina.ai/",
        description="Proxy prefix used when URL_FETCH_MODE=jina_proxy",
        alias="URL_PROXY_BASE",
    )

    url_request_timeout_seconds: int = Field(
        default=30,
        description="Timeout in seconds for URL fetch",
        alias="URL_REQUEST_TIMEOUT_SECONDS",
    )

    url_max_response_bytes: int = Field(
        default=5 * 1024 * 1024,
        description="Maximum response payload size in bytes for URL fetch",
        alias="URL_MAX_RESPONSE_BYTES",
    )

    url_block_private_networks: bool = Field(
        default=True,
        description="Block URL targets resolving to private/link-local/loopback addresses",
        alias="URL_BLOCK_PRIVATE_NETWORKS",
    )

    url_allowed_domains: str = Field(
        default="",
        description="Optional comma-separated domain allowlist for URL parsing",
        alias="URL_ALLOWED_DOMAINS",
    )

    url_max_redirects: int = Field(
        default=3,
        description="Maximum redirects followed during URL fetch",
        alias="URL_MAX_REDIRECTS",
    )

    auth_jwt_secret: str = Field(
        default="",
        description="HS256 JWT secret used for API authentication",
        alias="AUTH_JWT_SECRET",
    )

    auth_jwt_algorithm: Literal["HS256"] = Field(
        default="HS256",
        description="JWT signing algorithm (currently HS256)",
        alias="AUTH_JWT_ALGORITHM",
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )


# Canonical engine names, i.e. what normalize_pdf_engine() returns. Dispatch
# sites must compare against these instead of hardcoding their own name lists,
# otherwise a legacy alias accepted by ApplicationConfig gets misrouted.
PIPELINE_PDF_ENGINE = "pipeline"
VLM_PDF_ENGINES = frozenset(
    {
        "vlm-engine",
        "hybrid-engine",
        "vlm-http-client",
        "hybrid-http-client",
    }
)


def normalize_pdf_engine(raw: str | None) -> str:
    """Normalize legacy PDF_PARSE_ENGINE values to their current canonical names.

    Kept in the settings layer so both parsers and the model manager share one
    mapping. `raw is None`/empty falls back to the default pipeline engine.
    """
    engine = (raw or "pipeline").strip().lower()
    alias_map = {
        "vlm-vllm-engine": "vlm-engine",
        "vlm-vllm-client": "vlm-http-client",
        "vlm-auto-engine": "vlm-engine",
        "hybrid-auto-engine": "hybrid-engine",
        "pipeline-engine": "pipeline",
    }
    return alias_map.get(engine, engine)
