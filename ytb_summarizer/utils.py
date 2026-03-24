"""URL parsing and filename utilities."""
import re
import urllib.parse


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_playlist_id(url: str) -> str | None:
    """Extract YouTube playlist ID from URL."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if "list" in params:
        return params["list"][0]
    return None


def is_playlist_url(url: str) -> bool:
    return extract_playlist_id(url) is not None and "list=" in url


def is_bilibili_url(url: str) -> bool:
    """Return True if the URL points to a Bilibili video."""
    return "bilibili.com" in url or "b23.tv" in url


def extract_bilibili_bvid(url: str) -> str | None:
    """Extract BV ID or av ID from a Bilibili URL."""
    match = re.search(r"/video/(BV\w+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/video/(av\d+)", url)
    if match:
        return match.group(1)
    return None


def sanitize_filename(name: str) -> str:
    """Replace characters not safe for filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    return name[:200] or "untitled"


def clean_transcript(text: str) -> str:
    """Remove repeated whitespace/newlines from transcript text."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()
