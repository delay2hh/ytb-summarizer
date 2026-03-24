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
    Fetch Bilibili subtitle via Bilibili's player API + requests.
    Flow: pagelist → player/v2 (with SESSDATA cookie) → download BCC subtitle file.
    Priority: zh-Hans > zh-CN > zh > ai-zh > en > any.
    """
    import requests
    from .utils import extract_bilibili_bvid

    bvid = extract_bilibili_bvid(url)
    if not bvid:
        # For short URLs (b23.tv), resolve via yt-dlp first
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            bvid = info.get("id", "")
        if not bvid:
            raise ValueError(f"无法解析 B 站视频 ID: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
    }
    if sessdata:
        headers["Cookie"] = f"SESSDATA={sessdata}"

    # Step 1: Get CID (content part ID)
    r1 = requests.get(
        f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}",
        headers=headers, timeout=15,
    )
    r1.raise_for_status()
    d1 = r1.json()
    if d1.get("code") != 0 or not d1.get("data"):
        raise RuntimeError(f"获取视频分P信息失败: {d1.get('message', '未知错误')}")
    cid = d1["data"][0]["cid"]

    # Step 2: Get subtitle list from player/v2
    r2 = requests.get(
        f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}",
        headers=headers, timeout=15,
    )
    r2.raise_for_status()
    d2 = r2.json()
    player_data = d2.get("data", {})
    subtitle_info = player_data.get("subtitle", {})
    subtitles = subtitle_info.get("subtitles", [])
    need_login = player_data.get("need_login_subtitle", False)

    if not subtitles:
        if need_login and not sessdata:
            raise RuntimeError(
                "该视频字幕需要登录才能获取。\n"
                "请在 Settings → B站 SESSDATA 中填入你的 Cookie 后重试。"
            )
        if need_login and sessdata:
            raise RuntimeError(
                "SESSDATA 无效或已过期，请重新获取。\n"
                "浏览器登录 B 站 → F12 → Application → Cookies → 复制 SESSDATA 的值。"
            )
        raise RuntimeError(
            "该视频暂无字幕（B 站 AI 字幕由系统自动生成，部分视频尚未支持）。"
        )

    # Step 3: Choose best subtitle language
    preferred = ["zh-Hans", "zh-CN", "zh", "ai-zh", "en"]
    chosen = next(
        (s for lang in preferred for s in subtitles if s.get("lan") == lang),
        subtitles[0],
    )

    # Step 4: Download subtitle file (BCC JSON)
    sub_url = chosen.get("subtitle_url", "")
    if sub_url.startswith("//"):
        sub_url = "https:" + sub_url
    if not sub_url:
        raise RuntimeError("未找到字幕下载链接")

    r3 = requests.get(sub_url, headers=headers, timeout=30)
    r3.raise_for_status()
    bcc = r3.json()

    # Parse BCC format: {"body": [{"content": "text", "from": 0.0, "to": 1.5}, ...]}
    texts = [item["content"] for item in bcc.get("body", []) if item.get("content")]
    if not texts:
        raise RuntimeError("字幕内容为空")

    return clean_transcript(" ".join(texts))
