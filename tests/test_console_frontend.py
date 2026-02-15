import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from markio.main import app, mount_web_console


client = TestClient(app)


def test_console_route_serves_spa_shell():
    response = client.get('/console/')
    assert response.status_code == 200
    html = response.text
    assert '<div id="app"></div>' in html
    assert '/console/assets/' in html


def test_console_asset_bundle_served():
    html = client.get('/console/').text
    script_match = re.search(r'src="(/console/assets/[^"]+\.js)"', html)
    assert script_match is not None
    script_path = script_match.group(1)

    js = client.get(script_path)
    assert js.status_code == 200

    assets_dir = Path(__file__).resolve().parents[1] / 'markio' / 'webapp' / 'assets'
    js_files = list(assets_dir.glob('*.js'))
    assert js_files
    assert any('/v1/tasks' in path.read_text(encoding='utf-8') for path in js_files)


def test_console_includes_markio_console_title():
    html = client.get('/console/').text
    assert '<title>Markio Console</title>' in html


def test_console_fallback_page_when_assets_missing(tmp_path: Path):
    fallback_app = FastAPI()
    missing_dir = tmp_path / "missing-webapp"
    mount_web_console(fallback_app, web_console_dir=missing_dir)

    fallback_client = TestClient(fallback_app)
    response = fallback_client.get('/console/')
    assert response.status_code == 200
    assert "Markio Console frontend is not built yet" in response.text

    deep_link = fallback_client.get('/console/tasks')
    assert deep_link.status_code == 200
    assert "Markio Console frontend is not built yet" in deep_link.text
