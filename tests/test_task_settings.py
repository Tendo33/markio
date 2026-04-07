import pytest

from markio.settings.config_interface import Settings
from markio.settings.config_model import ApplicationConfig


def test_task_settings_defaults():
    config = ApplicationConfig()
    assert config.task_worker_count == 2
    assert config.task_queue_backend == "memory"
    assert config.task_history_limit == 500
    assert config.task_state_file == "data/task_state.json"
    assert config.task_state_result_max_chars == 0
    assert config.task_upload_dir == "data/task_uploads"
    assert config.task_max_upload_size_bytes == 50 * 1024 * 1024
    assert config.task_max_auto_retries == 0
    assert config.task_retry_delay_seconds == 0.0
    assert config.task_processing_timeout_seconds == 0.0
    assert config.rate_limit_enabled is True
    assert config.rate_limit_requests == 120
    assert config.rate_limit_window_seconds == 60


def test_settings_reload_fails_when_auth_secret_missing(monkeypatch):
    original_instance = Settings._instance
    try:
        monkeypatch.setenv("AUTH_JWT_SECRET", "")
        monkeypatch.setattr(Settings, "_instance", None)
        with pytest.raises(ValueError, match="AUTH_JWT_SECRET is required"):
            Settings.get_instance()
    finally:
        Settings._instance = original_instance


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("TASK_QUEUE_BACKEND", "invalid"),
        ("PDF_PARSE_ENGINE", "invalid"),
        ("URL_FETCH_MODE", "invalid"),
        ("AUTH_JWT_ALGORITHM", "RS256"),
        ("MINERU_DEVICE_MODE", "invalid"),
    ],
)
def test_application_config_rejects_invalid_enum_like_values(field, value):
    with pytest.raises(ValueError):
        ApplicationConfig.model_validate({field: value})
