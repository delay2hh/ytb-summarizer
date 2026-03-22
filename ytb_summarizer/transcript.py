"""Transcript extraction using youtube-transcript-api and yt-dlp fallback."""
from __future__ import annotations

from typing import Callable

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

from .utils import extract_video_id, clean_transcript


def get_video_info(url: str) -> dict:
    """Get video title and other metadata via yt-dlp."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
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


def get_playlist_entries(url: str, progress_cb: Callable[[str], None] | None = None) -> list[dict]:
    """Return list of video info dicts for a playlist."""
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


def fetch_transcript(url: str, lang: str = "en") -> str:
    """Fetch transcript text for a video. Tries requested lang, then auto-generated."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Cannot parse video ID from URL: {url}")

    try:
        # Try preferred language first
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            transcript = transcript_list.find_transcript([lang])
        except NoTranscriptFound:
            # Fall back to any available transcript
            try:
                transcript = transcript_list.find_generated_transcript([lang, "en"])
            except NoTranscriptFound:
                transcript = next(iter(transcript_list))

        entries = transcript.fetch()
        text = " ".join(e.text for e in entries)
        return clean_transcript(text)

    except TranscriptsDisabled:
        raise RuntimeError(f"字幕已禁用，无法获取视频 {video_id} 的字幕。")
    except Exception as e:
        raise RuntimeError(f"获取字幕失败: {e}")
