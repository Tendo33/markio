import threading
from contextlib import contextmanager
from typing import Any, Optional

from markio.settings import settings
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


class ModelManager:
    """Unified model manager that selectively initializes corresponding models based on configuration"""

    def __init__(self):
        self.pipeline_initialized = False
        self.vlm_initialized = False
        self.current_engine = None
        self._lock = threading.RLock()  # Use RLock to support reentrant
        self._initialization_error = None
        self._models = {}  # Store initialized model instances

    def initialize_models(self) -> bool:
        """
        Initialize corresponding models based on configuration

        Returns:
            bool: Whether initialization was successful
        """
        with self._lock:
            if self._initialization_error:
                logger.error(
                    f"Previous initialization failed: {self._initialization_error}"
                )
                return False

            if self.current_engine:
                logger.info(
                    f"Models already initialized with engine: {self.current_engine}"
                )
                return True

            engine = settings.pdf_parse_engine.lower()
            logger.info(f"Initializing models for engine: {engine}")

            try:
                if engine in ["pipeline", "pipeline-engine"]:
                    success = self._initialize_pipeline_model()
                elif engine in ["vlm", "vlm-sglang-engine", "vlm-sglang-client"]:
                    success = self._initialize_vlm_model(engine)
                else:
                    logger.warning(
                        f"Unknown engine: {engine}, falling back to pipeline"
                    )
                    success = self._initialize_pipeline_model()

                if not success:
                    self._initialization_error = f"Failed to initialize {engine} engine"
                    return False

                return True

            except ImportError as e:
                self._initialization_error = f"Import error: {str(e)}"
                logger.error(f"Model import failed: {e}")
                return False
            except RuntimeError as e:
                self._initialization_error = f"Runtime error: {str(e)}"
                logger.error(f"Model runtime error: {e}")
                return False
            except Exception as e:
                self._initialization_error = f"Unexpected error: {str(e)}"
                logger.error(f"Model initialization failed: {e}")
                return False

    def _validate_vlm_config(self, engine: str) -> bool:
        """Validate VLM configuration validity"""
        if engine == "vlm-sglang-client":
            if not hasattr(settings, "vlm_server_url") or not settings.vlm_server_url:
                logger.error(
                    "vlm-sglang-client engine requires vlm_server_url configuration"
                )
                return False
        return True

    def _initialize_pipeline_model(self) -> bool:
        """Initialize pipeline model"""
        if self.pipeline_initialized:
            return True

        try:
            from mineru.backend.pipeline.pipeline_analyze import custom_model_init

            logger.info("Initializing pipeline model...")
            custom_model_init()
            self.pipeline_initialized = True
            self.current_engine = "pipeline"
            logger.info("Pipeline model initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pipeline model: {e}")
            return False

    def _initialize_vlm_model(self, engine: str) -> bool:
        """Initialize VLM model"""
        if self.vlm_initialized:
            return True

        if not self._validate_vlm_config(engine):
            return False

        try:
            # Import VLM model singleton
            from mineru.backend.vlm.vlm_analyze import ModelSingleton

            # Determine backend and server_url based on engine type
            if engine == "vlm-sglang-client":
                backend = "sglang-client"
                server_url = getattr(settings, "vlm_server_url", None)
            else:
                backend = "sglang-engine"
                server_url = None

            # Directly initialize VLM model
            model_singleton = ModelSingleton()
            model = model_singleton.get_model(
                backend,
                None,
                server_url,
                mem_fraction_static=settings.vlm_mem_fraction_static,
            )

            # Store model instance for subsequent management
            self._models[engine] = model

            self.vlm_initialized = True
            self.current_engine = engine
            logger.info(f"VLM model initialized successfully with {backend}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize VLM model: {e}")
            logger.info("Falling back to pipeline model...")
            return self._initialize_pipeline_model()

    def get_current_engine(self) -> Optional[str]:
        """Get current engine being used"""
        return self.current_engine

    def get_model_instance(self, engine: str = None) -> Optional[Any]:
        """Get model instance for specified engine"""
        if not engine:
            engine = self.current_engine
        return self._models.get(engine)

    def is_initialized(self) -> bool:
        """Check if models are initialized"""
        return self.current_engine is not None and self._initialization_error is None

    def get_initialization_error(self) -> Optional[str]:
        """Get initialization error message"""
        return self._initialization_error

    def reset(self):
        """Reset model manager state (mainly for testing)"""
        with self._lock:
            self.pipeline_initialized = False
            self.vlm_initialized = False
            self.current_engine = None
            self._initialization_error = None
            self._models.clear()

    @contextmanager
    def safe_initialization(self):
        """Safe initialization context manager"""
        try:
            if not self.initialize_models():
                raise RuntimeError(
                    f"Model initialization failed: {self._initialization_error}"
                )
            yield self
        except Exception as e:
            logger.error(f"Error during model initialization: {e}")
            raise


# Global model manager instance (thread-safe)
_model_manager_instance = None
_model_manager_lock = threading.Lock()


def get_model_manager() -> ModelManager:
    """Get global model manager instance (thread-safe)"""
    global _model_manager_instance
    if _model_manager_instance is None:
        with _model_manager_lock:
            if _model_manager_instance is None:
                _model_manager_instance = ModelManager()
    return _model_manager_instance


# For backward compatibility, keep the original global instance
model_manager = get_model_manager()
