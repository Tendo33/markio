import pytest

from markio.utils import file_utils
from markio.utils import libreoffice_converter


def test_create_temporary_file_re_raises_creation_error(monkeypatch):
    def _raise_create_error(*args, **kwargs):
        raise OSError("create failed")

    monkeypatch.setattr(file_utils, "NamedTemporaryFile", _raise_create_error)

    with pytest.raises(OSError, match="create failed"):
        with file_utils.create_temporary_file():
            pass


def test_check_libreoffice_installed_returns_false_when_binary_missing(monkeypatch):
    def _raise_missing_binary(*args, **kwargs):
        raise FileNotFoundError("soffice not found")

    monkeypatch.setattr(libreoffice_converter.subprocess, "run", _raise_missing_binary)
    assert libreoffice_converter.check_libreoffice_installed() is False
