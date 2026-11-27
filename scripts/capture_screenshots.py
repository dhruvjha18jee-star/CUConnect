# scripts/capture_screenshots.py
# Launches the redesigned Streamlit app locally and captures crisp UI screenshots via Playwright (Edge/Chrome).
# Course mapping: Report & Presentation visual verification artifacts.

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed_data import seed_database

OUT_DIR = ROOT / "docs" / "diagrams" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _wait_server(url: str, timeout_s: float = 25.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Streamlit server did not become ready in time.")


def _click_nav(page, label_prefix: str) -> None:
    page.locator(f"section[data-testid='stSidebar'] button:has-text('{label_prefix}')").first.click()
    time.sleep(1.5)


def main() -> None:
    port = 8522
    url = f"http://127.0.0.1:{port}"
    streamlit_exe = ROOT / ".venv" / "Scripts" / "streamlit.exe"

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        tmp_db = str(Path(tmpdir) / "capture_seed.db")
        seed_database(db_path=tmp_db, reset=True)
        env = os.environ.copy()
        env["CUCONNECT_DB"] = tmp_db

        proc = subprocess.Popen(
            [
                str(streamlit_exe),
                "run",
                str(ROOT / "ui" / "streamlit_app.py"),
                "--server.port",
                str(port),
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            _wait_server(url)
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(channel="msedge", headless=True)
                except Exception:
                    browser = p.chromium.launch(channel="chrome", headless=True)

                context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
                page = context.new_page()
                page.goto(url, wait_until="networkidle")
                page.get_by_placeholder("e.g. aarav").wait_for(timeout=15000)
                time.sleep(1.5)

                # 1. Login / Auth screen
                page.screenshot(path=str(OUT_DIR / "ui_login.png"))
                print("Captured ui_login.png")

                # Log in as seeded user 'aarav' / 'chanakya2026'
                page.get_by_placeholder("e.g. aarav").fill("aarav")
                page.get_by_placeholder("Enter password").fill("chanakya2026")
                page.get_by_role("button", name="Log In").click()
                page.locator("text=Home Feed").first.wait_for(timeout=12000)
                time.sleep(1.8)

                # Type 'diy' in Top-Right Quick Student Search widget
                qs = page.get_by_placeholder("Search Students (prefix search)...")
                qs.fill("diy")
                qs.press("Enter")
                time.sleep(1.5)

                # 2. Redesigned Home Feed (Rover Demo + Quick Search 'diy' + Live Campus Network + Vanilla Sidebar)
                page.screenshot(path=str(OUT_DIR / "ui_home_feed.png"))
                print("Captured ui_home_feed.png")

                # 3. Home Feed scrolled to show Ananya Rao's Hackathon Certificate image post
                page.evaluate("""() => {
                    const el = document.querySelector('[data-testid="stMain"]') || window;
                    if (el === window) window.scrollTo(0, 740);
                    else el.scrollTop = 740;
                }""")
                time.sleep(0.8)
                page.screenshot(path=str(OUT_DIR / "ui_home_feed_cert.png"))
                print("Captured ui_home_feed_cert.png")

                # Scroll back up and click Diya Nair's primary "View Profile ↗" button
                page.evaluate("""() => {
                    const el = document.querySelector('[data-testid="stMain"]') || window;
                    if (el === window) window.scrollTo(0, 0);
                    else el.scrollTop = 0;
                }""")
                time.sleep(0.5)
                page.locator('button[data-testid="stBaseButton-primary"]:has-text("View Profile")').first.click()
                time.sleep(1.6)

                # 4. Student Profile Redirection View (Diya Nair)
                page.screenshot(path=str(OUT_DIR / "ui_student_profile.png"))
                print("Captured ui_student_profile.png")

                # 5. Post Composer (with image attachment uploader)
                _click_nav(page, "Post Composer")
                page.screenshot(path=str(OUT_DIR / "ui_post_composer.png"))
                print("Captured ui_post_composer.png")

                # 6. People You May Know
                _click_nav(page, "People You May Know")
                page.screenshot(path=str(OUT_DIR / "ui_suggestions.png"))
                print("Captured ui_suggestions.png")

                # 7. Degree & Chain Tool (select 'isha' to show 3+ 4-hop chain)
                _click_nav(page, "Degree & Chain Tool")
                sel = page.locator("div[data-testid='stSelectbox'] input").first
                sel.click()
                sel.fill("isha")
                page.keyboard.press("Enter")
                time.sleep(1.3)
                page.screenshot(path=str(OUT_DIR / "ui_degree_chain.png"))
                print("Captured ui_degree_chain.png")

                # 8. Search Users (type 'sh' to show Trie matching Aarav Sharma + Pranav Shetty)
                _click_nav(page, "Search Users")
                page.get_by_placeholder("e.g. aa, diy, shar, ver...").fill("sh")
                page.keyboard.press("Enter")
                time.sleep(1.3)
                page.screenshot(path=str(OUT_DIR / "ui_search_trie.png"))
                print("Captured ui_search_trie.png")

                # 9. Trending Posts
                _click_nav(page, "Trending Posts")
                page.screenshot(path=str(OUT_DIR / "ui_trending.png"))
                print("Captured ui_trending.png")

                # 10. Communities (Iterative DFS)
                _click_nav(page, "Communities")
                page.screenshot(path=str(OUT_DIR / "ui_communities.png"))
                print("Captured ui_communities.png")

                # 11. Browse All Students (AVL Tree)
                _click_nav(page, "Browse All Students")
                page.screenshot(path=str(OUT_DIR / "ui_avl_directory.png"))
                print("Captured ui_avl_directory.png")

                browser.close()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
