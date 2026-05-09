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

    pnpm = shutil.which("pnpm")
    if pnpm is None:
        pytest.skip("pnpm is required to build console assets")

    env = os.environ.copy()
    if not (FRONTEND_DIR / "node_modules").exists():
        subprocess.run(
            [pnpm, "install", "--frozen-lockfile"],
            cwd=FRONTEND_DIR,
            check=True,
            env=env,
        )

    subprocess.run(
        [pnpm, "run", "build"],
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


def test_console_route_keeps_strict_security_headers(console_build_ready):
    client = TestClient(_build_console_app())
    response = client.get('/console/')

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "unsafe-eval" not in csp
    assert "script-src 'self' 'unsafe-inline'" not in csp


def test_console_frontend_centralizes_storage_access_and_avoids_html_injection():
    frontend_src = FRONTEND_DIR / "src"
    local_storage_users: list[str] = []
    inner_html_users: list[str] = []

    for path in frontend_src.rglob("*"):
        if path.suffix not in {".ts", ".vue"}:
            continue
        if path.is_dir():
            continue
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        if "localStorage" in content:
            local_storage_users.append(relative)
        if "innerHTML" in content:
            inner_html_users.append(relative)

    assert local_storage_users == ["frontend/src/api/client.ts"]
    assert inner_html_users == []


def test_console_public_assets_are_markio_branded():
    logo = (FRONTEND_DIR / "public" / "logo.svg").read_text(encoding="utf-8")

    assert "Markio" in logo
    assert "Tianshu" not in logo
    assert "天枢" not in logo
    assert not (FRONTEND_DIR / "public" / "vite.svg").exists()


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
