import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
WEBAPP_DIR = REPO_ROOT / "markio" / "webapp"


@pytest.fixture(scope="session")
def console_build_ready() -> None:
    index_file = WEBAPP_DIR / "index.html"
    if index_file.exists():
        return

    npm = shutil.which("npm")
    if npm is None:
        pytest.skip("npm is required to build console assets")

    env = os.environ.copy()
    if not (FRONTEND_DIR / "node_modules").exists():
        subprocess.run(
            [npm, "ci"],
            cwd=FRONTEND_DIR,
            check=True,
            env=env,
        )

    subprocess.run(
        [npm, "run", "build"],
        cwd=FRONTEND_DIR,
        check=True,
        env=env,
    )

def _build_console_app() -> FastAPI:
    from markio.main import create_app, mount_web_console, register_routers

    app = create_app()
    register_routers(app)
    mount_web_console(app)
    return app


def test_console_route_serves_spa_shell(console_build_ready):
    client = TestClient(_build_console_app())
    response = client.get('/console/')
    assert response.status_code == 200
    html = response.text
    assert '<div id="app"></div>' in html
    assert '/console/assets/' in html


def test_console_asset_bundle_served(console_build_ready):
    client = TestClient(_build_console_app())
    html = client.get('/console/').text
    script_match = re.search(r'src="(/console/assets/[^"]+\.js)"', html)
    assert script_match is not None
    script_path = script_match.group(1)

    js = client.get(script_path)
    assert js.status_code == 200

    assets_dir = WEBAPP_DIR / 'assets'
    js_files = list(assets_dir.glob('*.js'))
    assert js_files
    assert any('/v1/tasks' in path.read_text(encoding='utf-8') for path in js_files)


def test_console_includes_markio_console_title(console_build_ready):
    client = TestClient(_build_console_app())
    html = client.get('/console/').text
    assert '<title>Markio Console</title>' in html


def test_console_fallback_page_when_assets_missing(tmp_path: Path):
    from markio.main import mount_web_console

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
