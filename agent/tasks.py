"""Task executor — intercepts voice commands and runs real OS-level actions."""

import re
import subprocess
import urllib.parse
from typing import Optional, Tuple

from utils import setup_logger
import agent.browser as browser

logger = setup_logger(__name__)


def _run(cmd: list[str]) -> None:
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _youtube_get_first_video_url(query: str) -> Optional[str]:
    """Use yt-dlp to resolve the first real video watch URL for *query*."""
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query}", "--get-id", "--no-playlist", "-q", "--no-warnings"],
            capture_output=True, text=True, timeout=15,
        )
        video_id = result.stdout.strip()
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"🎵 Resolved video: {url}")
            return url
    except Exception as exc:
        logger.warning(f"⚠️ yt-dlp search failed: {exc}")
    return None


# ── Patterns ─────────────────────────────────────────────────────────────── #

_PATTERNS: list[Tuple[re.Pattern, str]] = [
    # ── YouTube open/play ──────────────────────────────────────────────── #
    (re.compile(r"play\s+(.+?)\s+(?:on\s+)?(?:youtube|you tube)", re.I),          "play_youtube"),
    (re.compile(r"(?:open\s+)?youtube\s+(?:and\s+)?(?:play|search(?:\s+for)?)\s+(.+)", re.I), "play_youtube"),
    (re.compile(r"(?:search|find|look up)\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|you tube)", re.I), "play_youtube"),
    (re.compile(r"^(?:youtube|you tube)\s+(.+)$", re.I),                           "play_youtube"),
    (re.compile(r"^play\s+(.+)", re.I),                                            "play_youtube"),
    # Natural phrases: "can you play X", "ok so play X", "please play X"
    (re.compile(r"(?:can\s+you\s+|please\s+|ok\s+(?:so\s+)?(?:can\s+you\s+)?)?play\s+(?:the\s+)?(.+)", re.I), "play_youtube"),
    (re.compile(r"(?:open|go to|launch)\s+(?:youtube|you tube)$", re.I),           "open_youtube"),

    # ── YouTube browser control ────────────────────────────────────────── #
    (re.compile(r"\b(?:play\s+(?:the\s+)?first\s+(?:video|song|result)|first\s+video|first\s+song)\b", re.I), "yt_first"),
    (re.compile(r"\b(?:pause|stop\s+(?:the\s+)?video)\b", re.I),                  "yt_pause"),
    (re.compile(r"\b(?:resume|continue|unpause)\b", re.I),                         "yt_play"),
    (re.compile(r"\b(?:next\s+(?:video|song)|skip(?:\s+video)?)\b", re.I),         "yt_next"),
    (re.compile(r"\bskip\s+ad\b", re.I),                                           "yt_skip_ad"),
    (re.compile(r"\bfull\s*screen\b", re.I),                                       "yt_fullscreen"),
    (re.compile(r"\byt\s+search\s+(?:for\s+)?(.+)", re.I),                        "yt_search"),
    (re.compile(r"\bsearch\s+(?:for\s+)?(.+?)\s+on\s+youtube\b", re.I),           "yt_search"),
    # forward/back skip in video
    (re.compile(r"(?:skip|forward|fast\s*forward)\s+(\d+)\s+sec", re.I),          "yt_forward"),
    (re.compile(r"(?:rewind|go\s+back)\s+(\d+)\s+sec", re.I),                     "yt_back"),
    (re.compile(r"(?:skip|forward|fast\s*forward)\s+forward\b", re.I),            "yt_forward_10"),
    (re.compile(r"(?:rewind|go\s+back|skip\s+back)\b", re.I),                     "yt_back_10"),

    # ── Generic page control ───────────────────────────────────────────── #
    (re.compile(r"\bscroll\s+down\b", re.I),                                       "scroll_down"),
    (re.compile(r"\bscroll\s+up\b", re.I),                                         "scroll_up"),
    (re.compile(r"\bscroll\s+to\s+(?:the\s+)?top\b", re.I),                       "scroll_top"),
    (re.compile(r"\bscroll\s+to\s+(?:the\s+)?bottom\b", re.I),                    "scroll_bottom"),
    (re.compile(r"\b(?:go\s+)?back\b", re.I),                                      "go_back"),
    (re.compile(r"\bgo\s+forward\b", re.I),                                        "go_forward"),
    (re.compile(r"\b(?:refresh|reload)\s+(?:the\s+)?page\b", re.I),               "refresh"),
    (re.compile(r"\bclose\s+(?:this\s+)?tab\b", re.I),                             "close_tab"),
    (re.compile(r"\bnew\s+tab\b", re.I),                                            "new_tab"),
    (re.compile(r"\bzoom\s+in\b", re.I),                                            "zoom_in"),
    (re.compile(r"\bzoom\s+out\b", re.I),                                           "zoom_out"),
    (re.compile(r"\bclick\s+(?:on\s+)?(?:the\s+)?(.+)", re.I),                    "click_element"),

    # ── Page interaction ──────────────────────────────────────────────── #
    # "type hello in the search box"  /  "enter my email in the email field"
    (re.compile(r"(?:type|enter|write|put|input)\s+(.+?)\s+(?:in(?:to)?|on)\s+(?:the\s+)?(.+?)(?:\s+(?:field|box|input|bar))?$", re.I), "fill_input"),
    # "press enter" / "submit the form" / "hit enter"
    (re.compile(r"\b(?:press|hit)\s+enter\b", re.I),                               "press_enter"),
    (re.compile(r"\bsubmit\s+(?:the\s+)?(?:form|search|query)\b", re.I),           "press_enter"),

    # ── System ────────────────────────────────────────────────────────── #
    (re.compile(r"(?:open|go to|launch|navigate to)\s+(.+)", re.I),               "open_website"),
    (re.compile(r"volume\s+up", re.I),                                             "volume_up"),
    (re.compile(r"volume\s+down", re.I),                                           "volume_down"),
    (re.compile(r"volume\s+(\d+)(?:\s+percent)?", re.I),                          "volume_set"),
    (re.compile(r"\bmute\b", re.I),                                                 "mute"),
    (re.compile(r"(?:take\s+a?\s*)?screenshot", re.I),                             "screenshot"),
]

# ── Handlers ──────────────────────────────────────────────────────────────── #

def _do_play_youtube(query: str) -> str:
    url = _youtube_get_first_video_url(query)
    if url:
        return browser.open_url(url) and f"Playing {query} on YouTube, sir." or f"Playing {query}, sir."
    fallback = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    browser.open_url(fallback)
    return f"Opening YouTube search for {query}, sir."


def _do_open_youtube() -> str:
    browser.open_url("https://www.youtube.com")
    return "Opening YouTube, sir."


def _do_open_website(target: str) -> str:
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        url = "https://" + target if "." in target else (
            "https://www.google.com/search?q=" + urllib.parse.quote(target)
        )
    else:
        url = target
    browser.open_url(url)
    return f"Opening {target} for you, sir."


def _do_volume_up() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "10%+"])
    return "Volume increased, sir."


def _do_volume_down() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "10%-"])
    return "Volume decreased, sir."


def _do_volume_set(level: int) -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"])
    return f"Volume set to {level} percent, sir."


def _do_mute() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "toggle"])
    return "Audio toggled, sir."


def _do_screenshot() -> str:
    import datetime, os
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.expanduser(f"~/Desktop/screenshot_{ts}.png")
    _run(["gnome-screenshot", "-f", path])
    return "Screenshot saved to your desktop, sir."


# ── Main dispatcher ───────────────────────────────────────────────────────── #

def try_execute(command: str) -> Optional[str]:
    """Match command against task patterns. Returns reply or None for LLM."""
    cmd = command.strip()
    for pattern, handler in _PATTERNS:
        m = pattern.search(cmd)
        if m:
            logger.info(f"⚡ Task matched: {handler} — '{cmd}'")
            try:
                # YouTube open/play
                if handler == "play_youtube":      return _do_play_youtube(m.group(1).strip())
                if handler == "open_youtube":      return _do_open_youtube()
                # YouTube page control
                if handler == "yt_first":          return browser.yt_click_first_video()
                if handler == "yt_pause":          return browser.yt_pause()
                if handler == "yt_play":           return browser.yt_play()
                if handler == "yt_next":           return browser.yt_next()
                if handler == "yt_skip_ad":        return browser.yt_skip_ad()
                if handler == "yt_fullscreen":     return browser.yt_fullscreen()
                if handler == "yt_search":         return browser.yt_search(m.group(1).strip())
                if handler == "yt_forward":        return browser.yt_seek_forward(int(m.group(1)))
                if handler == "yt_back":           return browser.yt_seek_back(int(m.group(1)))
                if handler == "yt_forward_10":     return browser.yt_seek_forward(10)
                if handler == "yt_back_10":        return browser.yt_seek_back(10)
                # Generic page control
                if handler == "scroll_down":       return browser.scroll_down()
                if handler == "scroll_up":         return browser.scroll_up()
                if handler == "scroll_top":        return browser.scroll_top()
                if handler == "scroll_bottom":     return browser.scroll_bottom()
                if handler == "go_back":           return browser.go_back()
                if handler == "go_forward":        return browser.go_forward()
                if handler == "refresh":           return browser.refresh_page()
                if handler == "close_tab":         return browser.close_tab()
                if handler == "new_tab":           return browser.new_tab()
                if handler == "zoom_in":           return browser.zoom_in()
                if handler == "zoom_out":          return browser.zoom_out()
                if handler == "click_element":     return browser.click_element_by_text(m.group(1).strip())
                if handler == "fill_input":        return browser.fill_input(m.group(2).strip(), m.group(1).strip())
                if handler == "press_enter":       return browser.press_enter()
                # Website
                if handler == "open_website":      return _do_open_website(m.group(1).strip())
                # System
                if handler == "volume_up":         return _do_volume_up()
                if handler == "volume_down":       return _do_volume_down()
                if handler == "volume_set":        return _do_volume_set(int(m.group(1)))
                if handler == "mute":              return _do_mute()
                if handler == "screenshot":        return _do_screenshot()
            except Exception as exc:
                logger.error(f"❌ Task '{handler}' failed: {exc}")
                return "I'm sorry, I couldn't complete that task, sir."
    return None
