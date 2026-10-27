import pytest


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERVERSE_DATA_DIR", str(tmp_path))
    from paperverse import config as cfg
    cfg.get_settings.cache_clear()
    yield tmp_path
    cfg.get_settings.cache_clear()
