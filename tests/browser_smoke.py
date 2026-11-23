"""Exercise the built starter at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator("#cards .card").first.wait_for()
                assert "Collection could not load" not in page.locator("#status").inner_text()
                initial_count = page.locator("#count").inner_text()
                page.locator("#query").fill("railroad")
                assert page.locator("#cards .card").count() > 0
                page.locator(".record-title").first.click()
                assert page.locator("#detail").is_visible()
                assert "digitalcollections.nypl.org/items/" in page.locator("#detail-body .primary").get_attribute("href")
                with page.expect_download() as downloaded:
                    page.get_by_role("button", name="Save record JSON", exact=True).click()
                assert downloaded.value.suggested_filename.endswith(".json")
                page.locator("#close-detail").click()
                page.locator(".pin").nth(0).click()
                page.locator(".pin").nth(1).click()
                assert page.locator("#comparison .comparison-item").count() == 2
                page.locator("#query").fill('<img src=x onerror="alert(1)">')
                assert page.locator("#empty").is_visible()
                assert page.locator("#cards img").count() == 0
                page.locator("#empty-reset").click()
                assert page.locator("#count").inner_text() == initial_count
                with page.expect_download() as exported:
                    page.locator("#export").click()
                assert exported.value.suggested_filename.endswith(".csv")
                page.locator("#genre").select_option("Pamphlets")
                assert page.locator("#cards .card").count() > 0
                page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: search, source details, comparison, export, no-results recovery and mobile layout")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
