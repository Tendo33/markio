from markio.settings.config_model import ApplicationConfig


def test_task_settings_defaults():
    config = ApplicationConfig()
    assert config.task_worker_count == 2
    assert config.task_queue_backend == "memory"
    assert config.task_history_limit == 500
    assert config.task_state_file == "data/task_state.json"
    assert config.task_upload_dir == "data/task_uploads"
    assert config.task_max_upload_size_bytes == 50 * 1024 * 1024
    assert config.task_max_auto_retries == 0
    assert config.task_retry_delay_seconds == 0.0
    assert config.task_processing_timeout_seconds == 0.0
    assert config.rate_limit_enabled is True
    assert config.rate_limit_requests == 120
    assert config.rate_limit_window_seconds == 60
