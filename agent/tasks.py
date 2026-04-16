"""Task executor — intercepts voice commands and runs real OS-level actions."""

import logging
import re
import subprocess
import urllib.parse
import webbrowser
from typing import Optional, Tuple

from utils import setup_logger

logger = setup_logger(__name__)


def _open_url(url: str) -> None:
    webbrowser.open(url)
    logger.info(f"🌐 Opened: {url}")


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


_PATTERNS: list[Tuple[re.Pattern, str]] = [
    # YouTube explicit
    (re.compile(r"play\s+(.+?)\s+(?:on\s+)?(?:youtube|you tube)", re.I), "play_youtube"),
    (re.compile(r"(?:open\s+)?youtube\s+(?:and\s+)?(?:play|search(?:\s+for)?)\s+(.+)", re.I), "play_youtube"),
    (re.compile(r"(?:search|find|look up)\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|you tube)", re.I), "play_youtube"),
    # Catch-all: "youtube <query>"
    (re.compile(r"^(?:youtube|you tube)\s+(.+)$", re.I), "play_youtube"),
    # Generic "play <something>" — treat as YouTube play
    (re.compile(r"^play\s+(.+)", re.I), "play_youtube"),
    # Open YouTube without a query
    (re.compile(r"(?:open|go to|launch)\s+(?:youtube|you tube)$", re.I), "open_youtube"),
    (re.compile(r"(?:open|go to|launch|navigate to)\s+(.+)", re.I), "open_website"),
    (re.compile(r"volume\s+up", re.I), "volume_up"),
    (re.compile(r"volume\s+down", re.I), "volume_down"),
    (re.compile(r"\bmute\b", re.I), "mute"),
    (re.compile(r"(?:take\s+a?\s*)?screenshot", re.I), "screenshot"),
]


def _do_play_youtube(query: str) -> str:
    url = _youtube_get_first_video_url(query)
    if url:
        _open_url(url)
        return f"Playing {query} on YouTube now, sir."
    fallback = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    _open_url(fallback)
    return f"Opening YouTube search for {query}, sir."


def _do_open_youtube() -> str:
    _open_url("https://www.youtube.com")
    return "Opening YouTube, sir."


def _do_open_website(target: str) -> str:
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        url = "https://" + target if "." in target else (
            "https://www.google.com/search?q=" + urllib.parse.quote(target)
        )
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
    return "Screenshot saved to your desktop, sir."


def try_execute(command: str) -> Optional[str]:
    """Match command against task patterns. Returns reply or None for LLM."""
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
                return "I'm sorry, I couldn't complete that task."
    return None
