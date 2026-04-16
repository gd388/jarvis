"""Task executor — intercepts voice commands and runs real OS-level actions."""

import logging
import re
import subprocess
import urllib.parse
import webbrowser
from typing import Optional, Tuple

from utils import setup_logger

logger = setup_logger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────── #

def _open_url(url: str) -> None:
    """Open a URL in the default browser (non-blocking)."""
    webbrowser.open(url)
    logger.info(f"🌐 Opened: {url}")


def _youtube_search_url(query: str) -> str:
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)


def _youtube_play_url(query: str) -> str:
    """Direct 'autoplaying' search — first result page opens & starts."""
    return (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
        + "&sp=EgIQAQ%253D%253D"   # filter: sort by relevance, first video
    )


def _run(cmd: list[str]) -> None:
    """Fire-and-forget a subprocess."""
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ── pattern matching ───────────────────────────────────────────────────────── #

# Each entry: (regex_pattern, handler_name)
# Patterns are checked in order — first match wins.
_PATTERNS: list[Tuple[re.Pattern, str]] = [
    # YouTube play / search
    (re.compile(r"play\s+(.+?)\s+(?:on\s+)?(?:youtube|you tube)", re.I), "play_youtube"),
    (re.compile(r"(?:open\s+)?youtube\s+(?:and\s+)?(?:play|search(?:\s+for)?)\s+(.+)", re.I), "play_youtube"),
    (re.compile(r"(?:search|find|look up)\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|you tube)", re.I), "play_youtube"),
    (re.compile(r"(?:open|go to|launch)\s+(?:youtube|you tube)$", re.I), "open_youtube"),

    # Browser / websites
    (re.compile(r"(?:open|go to|launch|navigate to)\s+(.+)", re.I), "open_website"),

    # Volume
    (re.compile(r"volume\s+up", re.I), "volume_up"),
    (re.compile(r"volume\s+down", re.I), "volume_down"),
    (re.compile(r"mute", re.I), "mute"),

    # System
    (re.compile(r"(?:take\s+a?\s*)?screenshot", re.I), "screenshot"),
]


# ── action functions ───────────────────────────────────────────────────────── #

def _do_play_youtube(query: str) -> str:
    url = _youtube_play_url(query)
    _open_url(url)
    return f"Playing {query} on YouTube now, sir."


def _do_open_youtube() -> str:
    _open_url("https://www.youtube.com")
    return "Opening YouTube, sir."


def _do_open_website(target: str) -> str:
    target = target.strip()
    # Add scheme if missing
    if not target.startswith(("http://", "https://")):
        # Check if it looks like a domain (contains a dot)
        if "." in target:
            url = "https://" + target
        else:
            # Treat as Google search
            url = "https://www.google.com/search?q=" + urllib.parse.quote(target)
    else:
        url = target
    _open_url(url)
    return f"Opening {target} for you, sir."


def _do_volume_up() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "10%+"])
    return "Volume increased, sir."


def _do_volume_down() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "10%-"])
    return "Volume decreased, sir."


def _do_mute() -> str:
    _run(["amixer", "-D", "pulse", "sset", "Master", "toggle"])
    return "Audio toggled, sir."


def _do_screenshot() -> str:
    import datetime, os
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.expanduser(f"~/Desktop/screenshot_{ts}.png")
    _run(["gnome-screenshot", "-f", path])
    return f"Screenshot saved to your desktop, sir."


# ── public API ─────────────────────────────────────────────────────────────── #

def try_execute(command: str) -> Optional[str]:
    """
    Try to match *command* against known task patterns.

    Returns a spoken reply string if a task was executed,
    or None if no pattern matched (caller should use LLM instead).
    """
    for pattern, handler in _PATTERNS:
        m = pattern.search(command)
        if m:
            logger.info(f"⚡ Task matched: {handler} — '{command}'")
            try:
                if handler == "play_youtube":
                    return _do_play_youtube(m.group(1).strip())
                elif handler == "open_youtube":
                    return _do_open_youtube()
                elif handler == "open_website":
                    return _do_open_website(m.group(1).strip())
                elif handler == "volume_up":
                    return _do_volume_up()
                elif handler == "volume_down":
                    return _do_volume_down()
                elif handler == "mute":
                    return _do_mute()
                elif handler == "screenshot":
                    return _do_screenshot()
            except Exception as exc:
                logger.error(f"❌ Task '{handler}' failed: {exc}")
                return f"I'm sorry, I couldn't complete that task. {exc}"

    return None  # no match → let LLM handle it
