"""Browser controller — Selenium-based automation for voice-driven page control."""

from __future__ import annotations

import socket
import subprocess
import time
from typing import Optional

from utils import setup_logger

logger = setup_logger(__name__)

_DEBUG_PORT = 9222
_BRAVE_BIN  = "brave-browser"

# ── singleton driver ─────────────────────────────────────────────────────── #
_driver = None


def _debug_port_open() -> bool:
    """Return True if Brave's remote-debug port is open and accepting."""
    try:
        with socket.create_connection(("localhost", _DEBUG_PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _ensure_brave() -> None:
    """Launch Brave with remote debugging if it is not already running on port 9222."""
    if _debug_port_open():
        return

    logger.info(f"🚀 Brave not listening on port {_DEBUG_PORT} — (re)launching with debug port …")

    # Kill ONLY the Brave instance that was launched with the remote-debug
    # port.  The overlay Brave (--user-data-dir=/tmp/jarvis-overlay-profile)
    # must NOT be killed here — it is a completely separate process.
    subprocess.run(["pkill", "-9", "-f", "brave.*remote-debugging-port"], capture_output=True)
    time.sleep(2.0)   # wait for profile lock files to clear

    subprocess.Popen(
        [
            _BRAVE_BIN,
            f"--remote-debugging-port={_DEBUG_PORT}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Poll until the port is ready (up to 15 s)
    for _ in range(150):
        time.sleep(0.1)
        if _debug_port_open():
            logger.info(f"✓ Brave debug port {_DEBUG_PORT} open")
            return
    logger.warning("⚠️  Brave debug port did not open in time")


def get_driver():
    """Return (and lazily create) a Selenium driver attached to running Brave."""
    global _driver
    if _driver is not None:
        try:
            _ = _driver.current_url   # check still alive
            return _driver
        except Exception:
            _driver = None

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        _ensure_brave()

        opts = Options()
        # Attach to the already-running Brave via remote debugging.
        # All logins, cookies, and extensions from your real profile are available.
        opts.add_experimental_option("debuggerAddress", f"localhost:{_DEBUG_PORT}")

        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=opts)
        logger.info("✓ Selenium attached to existing Brave via remote debugging")
        return _driver
    except Exception as exc:
        logger.error(f"❌ Could not attach to Brave: {exc}")
        return None


def quit_driver() -> None:
    global _driver
    if _driver:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None


# ── helpers ──────────────────────────────────────────────────────────────── #

def _js(script: str, *args):
    drv = get_driver()
    if drv is None:
        return None
    try:
        return drv.execute_script(script, *args)
    except Exception as exc:
        logger.warning(f"⚠️  JS error: {exc}")
        return None


def _find(by, selector, timeout: float = 4):
    """Find element with wait; return element or None."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    drv = get_driver()
    if drv is None:
        return None
    try:
        return WebDriverWait(drv, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except Exception:
        return None


def _find_all(by, selector, timeout: float = 4) -> list:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    drv = get_driver()
    if drv is None:
        return []
    try:
        WebDriverWait(drv, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return drv.find_elements(by, selector)
    except Exception:
        return []


# ── public browser actions ───────────────────────────────────────────────── #

def open_url(url: str) -> str:
    drv = get_driver()
    if drv is None:
        import webbrowser
        webbrowser.open(url)
        return "Opened in default browser, sir."
    # Open in a new tab so the user’s existing tabs are untouched
    drv.execute_script("window.open(arguments[0], '_blank')", url)
    drv.switch_to.window(drv.window_handles[-1])
    logger.info(f"🌐 New tab opened: {url}")
    return "Done, sir."


def current_url() -> Optional[str]:
    drv = get_driver()
    return drv.current_url if drv else None


def current_title() -> Optional[str]:
    drv = get_driver()
    return drv.title if drv else None


# ── YouTube ──────────────────────────────────────────────────────────────── #

def yt_click_first_video() -> str:
    """Click the first video thumbnail on any YouTube page."""
    from selenium.webdriver.common.by import By

    # Works on homepage, search results and channel pages
    selectors = [
        "ytd-video-renderer a#thumbnail",
        "ytd-rich-item-renderer a#thumbnail",
        "ytd-compact-video-renderer a#thumbnail",
    ]
    for sel in selectors:
        els = _find_all(By.CSS_SELECTOR, sel)
        if els:
            href = els[0].get_attribute("href") or ""
            if "watch" in href:
                els[0].click()
                logger.info(f"▶️  Clicked first video: {href}")
                return "Playing the first video, sir."
    return "I couldn't find a video to click, sir."


def yt_play_pause() -> str:
    _js("document.querySelector('video')?.paused ? document.querySelector('video').play() : document.querySelector('video').pause()")
    return "Toggled play/pause, sir."


def yt_pause() -> str:
    _js("document.querySelector('video')?.pause()")
    return "Paused, sir."


def yt_play() -> str:
    _js("document.querySelector('video')?.play()")
    return "Resuming, sir."


def yt_next() -> str:
    from selenium.webdriver.common.by import By
    el = _find(By.CSS_SELECTOR, ".ytp-next-button")
    if el:
        el.click()
        return "Playing next video, sir."
    return "Couldn't find the next button, sir."


def yt_skip_ad() -> str:
    from selenium.webdriver.common.by import By
    el = _find(By.CSS_SELECTOR, ".ytp-skip-ad-button", timeout=3)
    if el:
        el.click()
        return "Skipped the ad, sir."
    return "No ad to skip, sir."


def yt_fullscreen() -> str:
    from selenium.webdriver.common.by import By
    el = _find(By.CSS_SELECTOR, ".ytp-fullscreen-button")
    if el:
        el.click()
        return "Fullscreen toggled, sir."
    return "Couldn't toggle fullscreen, sir."


def yt_mute() -> str:
    _js("var v=document.querySelector('video'); if(v) v.muted=!v.muted;")
    return "Toggled mute, sir."


def yt_volume(level: int) -> str:
    """Set YouTube video volume 0–100."""
    _js(f"var v=document.querySelector('video'); if(v) v.volume={level/100:.2f};")
    return f"Volume set to {level} percent, sir."


def yt_seek_forward(secs: int = 10) -> str:
    _js(f"var v=document.querySelector('video'); if(v) v.currentTime+=({secs});")
    return f"Skipped forward {secs} seconds, sir."


def yt_seek_back(secs: int = 10) -> str:
    _js(f"var v=document.querySelector('video'); if(v) v.currentTime-=({secs});")
    return f"Went back {secs} seconds, sir."


def yt_search(query: str) -> str:
    """Type a search query into the YouTube search bar and submit."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    bar = _find(By.NAME, "search_query") or _find(By.CSS_SELECTOR, "input#search")
    if bar:
        bar.clear()
        bar.send_keys(query)
        bar.send_keys(Keys.RETURN)
        return f"Searching YouTube for {query}, sir."
    # Fallback: navigate directly
    import urllib.parse
    open_url("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    return f"Opened YouTube search for {query}, sir."


# ── generic page actions ─────────────────────────────────────────────────── #

def scroll_down(px: int = 600) -> str:
    _js(f"window.scrollBy(0, {px})")
    return "Scrolled down, sir."


def scroll_up(px: int = 600) -> str:
    _js(f"window.scrollBy(0, -{px})")
    return "Scrolled up, sir."


def scroll_top() -> str:
    _js("window.scrollTo(0,0)")
    return "Scrolled to the top, sir."


def scroll_bottom() -> str:
    _js("window.scrollTo(0,document.body.scrollHeight)")
    return "Scrolled to the bottom, sir."


def go_back() -> str:
    drv = get_driver()
    if drv:
        drv.back()
    return "Going back, sir."


def go_forward() -> str:
    drv = get_driver()
    if drv:
        drv.forward()
    return "Going forward, sir."


def refresh_page() -> str:
    drv = get_driver()
    if drv:
        drv.refresh()
    return "Page refreshed, sir."


def close_tab() -> str:
    drv = get_driver()
    if drv:
        drv.close()
    return "Tab closed, sir."


def new_tab(url: str = "about:blank") -> str:
    drv = get_driver()
    if drv:
        drv.execute_script(f"window.open('{url}','_blank');")
        drv.switch_to.window(drv.window_handles[-1])
    return "Opened new tab, sir."


def zoom_in() -> str:
    _js("document.body.style.zoom = (parseFloat(document.body.style.zoom||1)+0.1).toFixed(1)")
    return "Zoomed in, sir."


def zoom_out() -> str:
    _js("document.body.style.zoom = Math.max(0.5,(parseFloat(document.body.style.zoom||1)-0.1)).toFixed(1)")
    return "Zoomed out, sir."


def get_page_text(max_chars: int = 4000) -> Optional[str]:
    """Return visible body text of the current page, truncated to *max_chars*.

    Skips the local Jarvis overlay (localhost:8000).  Uses JS ``innerText``
    instead of Selenium's ``.text`` so SPA pages that render via JavaScript
    are captured correctly.  Waits up to 5 s for the page to populate.
    """
    import time as _time

    drv = get_driver()
    if drv is None:
        return None
    try:
        # If Selenium is sitting on the Jarvis overlay, look for a real page
        _overlay = ("127.0.0.1:8000", "localhost:8000")
        try:
            cur = drv.current_url or ""
        except Exception:
            cur = ""
        if any(o in cur for o in _overlay):
            for handle in drv.window_handles:
                try:
                    drv.switch_to.window(handle)
                    url = drv.current_url or ""
                    if not any(o in url for o in _overlay):
                        break
                except Exception:
                    continue

        # Wait up to 5 s for a SPA to render its body text
        text = ""
        for _ in range(10):
            try:
                text = drv.execute_script("return document.body.innerText") or ""
                text = text.strip()
            except Exception:
                pass
            if text:
                break
            _time.sleep(0.5)

        if not text:
            return None
        if len(text) > max_chars:
            text = text[:max_chars] + "…"
        logger.info(f"📄 Page text extracted ({len(text)} chars) from: {drv.current_url}")
        return text
    except Exception as exc:
        logger.warning(f"⚠️  Could not extract page text: {exc}")
        return None


def click_link_containing(text: str) -> str:
    """Click the first link whose visible text contains *text*."""
    from selenium.webdriver.common.by import By

    drv = get_driver()
    if drv is None:
        return "Browser not available, sir."
    try:
        links = drv.find_elements(By.TAG_NAME, "a")
        for link in links:
            if text.lower() in (link.text or "").lower():
                link.click()
                return f"Clicked '{link.text}', sir."
        return f"No link containing '{text}' found, sir."
    except Exception as exc:
        return f"Could not click link: {exc}"


def click_element_by_text(text: str) -> str:
    """Click any interactive element (button, link, input[submit]) whose
    visible text, value, or aria-label contains *text*."""
    from selenium.webdriver.common.by import By

    drv = get_driver()
    if drv is None:
        return "Browser not available, sir."
    needle = text.lower()
    try:
        candidates = (
            drv.find_elements(By.TAG_NAME, "button")
            + drv.find_elements(By.TAG_NAME, "a")
            + drv.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
            + drv.find_elements(By.CSS_SELECTOR, "[role='button']")
        )
        for el in candidates:
            label = (
                el.text
                or el.get_attribute("value")
                or el.get_attribute("aria-label")
                or el.get_attribute("title")
                or ""
            )
            if needle in label.lower():
                drv.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
                el.click()
                logger.info(f"🖱️  Clicked element with label: '{label.strip()}'")
                return f"Clicked '{label.strip()}', sir."
        return f"I couldn't find any element matching '{text}', sir."
    except Exception as exc:
        logger.warning(f"⚠️  click_element_by_text error: {exc}")
        return f"Could not click that element, sir."


def fill_input(field_hint: str, value: str) -> str:
    """Find a text input whose placeholder, label, aria-label, id, or name
    contains *field_hint* and type *value* into it."""
    from selenium.webdriver.common.by import By

    drv = get_driver()
    if drv is None:
        return "Browser not available, sir."
    needle = field_hint.lower()
    try:
        inputs = drv.find_elements(
            By.CSS_SELECTOR,
            "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='checkbox']):not([type='radio']), textarea",
        )
        for inp in inputs:
            attrs = " ".join(filter(None, [
                inp.get_attribute("placeholder") or "",
                inp.get_attribute("aria-label") or "",
                inp.get_attribute("name") or "",
                inp.get_attribute("id") or "",
                inp.get_attribute("title") or "",
            ])).lower()
            if needle in attrs or not needle:  # empty hint → first input
                drv.execute_script("arguments[0].scrollIntoView({block:'center'})", inp)
                inp.clear()
                inp.send_keys(value)
                logger.info(f"⌨️  Typed into field (hint='{field_hint}'): '{value}'")
                return f"Typed '{value}' into the {field_hint or 'input'} field, sir."
        return f"I couldn't find a field matching '{field_hint}', sir."
    except Exception as exc:
        logger.warning(f"⚠️  fill_input error: {exc}")
        return f"Could not type into that field, sir."


def press_enter() -> str:
    """Send Enter key to the currently focused element (submits forms)."""
    from selenium.webdriver.common.keys import Keys

    drv = get_driver()
    if drv is None:
        return "Browser not available, sir."
    try:
        focused = drv.switch_to.active_element
        focused.send_keys(Keys.RETURN)
        logger.info("↵ Pressed Enter on focused element")
        return "Pressed Enter, sir."
    except Exception as exc:
        logger.warning(f"⚠️  press_enter error: {exc}")
        return "Could not press Enter, sir."
