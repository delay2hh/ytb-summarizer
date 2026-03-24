"""Transcript extraction: YouTube (youtube-transcript-api) and Bilibili (yt-dlp + requests)."""
from __future__ import annotations

from typing import Callable

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._transcripts import TranscriptList

from .utils import extract_video_id, clean_transcript, is_bilibili_url


# ── Public API (dispatch by URL) ─────────────────────────────────────────────

def get_video_info(url: str, bilibili_sessdata: str = "") -> dict:
    """Get video metadata. Dispatches to YouTube or Bilibili handler."""
    if is_bilibili_url(url):
        return _get_bilibili_video_info(url, sessdata=bilibili_sessdata)
    return _get_youtube_video_info(url)


def fetch_transcript(url: str, lang: str = "en", bilibili_sessdata: str = "") -> str:
    """Fetch transcript text. Dispatches to YouTube or Bilibili handler."""
    if is_bilibili_url(url):
        return _fetch_bilibili_transcript(url, sessdata=bilibili_sessdata)
    return _fetch_youtube_transcript(url, lang=lang)


def get_playlist_entries(url: str, progress_cb: Callable[[str], None] | None = None) -> list[dict]:
    """Return list of video info dicts for a YouTube playlist."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries", [])
        if progress_cb:
            progress_cb(f"播放列表共 {len(entries)} 个视频")
        return [
            {
                "title": e.get("title", "Unknown"),
                "url": f"https://www.youtube.com/watch?v={e['id']}",
                "video_id": e.get("id", ""),
            }
            for e in entries
            if e.get("id")
        ]


# ── YouTube ───────────────────────────────────────────────────────────────────

def _get_youtube_video_info(url: str) -> dict:
    import yt_dlp

    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader", ""),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "url": url,
            "video_id": info.get("id", ""),
        }


def _fetch_youtube_transcript(url: str, lang: str = "en") -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Cannot parse video ID from URL: {url}")

    api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id, languages=[lang, "en"])
        entries = fetched.to_raw_data()
        text = " ".join(e["text"] for e in entries)
        return clean_transcript(text)
    except Exception:
        pass

    try:
        transcript_list: TranscriptList = api.list(video_id)
        try:
            transcript = transcript_list.find_transcript([lang, "en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript([lang, "en"])
            except Exception:
                transcript = next(iter(transcript_list))

        fetched = transcript.fetch()
        entries = fetched.to_raw_data()
        text = " ".join(e["text"] for e in entries)
        return clean_transcript(text)

    except Exception as e:
        raise RuntimeError(f"获取 YouTube 字幕失败: {e}")


# ── Bilibili ──────────────────────────────────────────────────────────────────

def _get_bilibili_video_info(url: str, sessdata: str = "") -> dict:
    import yt_dlp

    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    if sessdata:
        ydl_opts["http_headers"] = {"Cookie": f"SESSDATA={sessdata}"}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader", info.get("channel", "")),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "url": url,
            "video_id": info.get("id", ""),
        }


def _fetch_bilibili_transcript(url: str, sessdata: str = "") -> str:
    """
    Fetch Bilibili subtitle via yt-dlp (no download) + requests.
    Priority: zh-Hans > zh > ai-zh > en > any available.
    Supports json3 format and BCC format.
    """
    import yt_dlp
    import requests

    headers = {}
    if sessdata:
        headers["Cookie"] = f"SESSDATA={sessdata}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "http_headers": headers,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Collect all available subtitles (manual subtitles override auto-generated)
    auto_caps = info.get("automatic_captions") or {}
    subtitles = info.get("subtitles") or {}
    all_subs: dict = {**auto_caps, **subtitles}

    if not all_subs:
        raise RuntimeError(
            "该视频没有字幕。B 站 AI 字幕需要大会员账号的 SESSDATA，请在 Settings 中填写后重试。"
        )

    # Choose best language
    preferred = ["zh-Hans", "zh", "zh-CN", "zh-Hant", "ai-zh", "en"]
    chosen = next((l for l in preferred if l in all_subs), next(iter(all_subs)))

    # Find a downloadable subtitle URL
    sub_url = None
    for entry in all_subs[chosen]:
        if entry.get("url"):
            sub_url = entry["url"]
            break

    if not sub_url:
        raise RuntimeError(f"未找到可下载的字幕链接 (语言: {chosen})")

    resp = requests.get(sub_url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Parse json3 format (YouTube-style, used by yt-dlp for bilibili)
    if "events" in data:
        texts = [
            seg["utf8"]
            for event in data["events"]
            for seg in event.get("segs", [])
            if seg.get("utf8", "").strip()
        ]
    # Parse BCC format (Bilibili native)
    elif "body" in data:
        texts = [item["content"] for item in data["body"] if item.get("content")]
    else:
        raise RuntimeError(f"未知字幕格式，字段: {list(data.keys())}")

    if not texts:
        raise RuntimeError("字幕内容为空")

    return clean_transcript(" ".join(texts))
