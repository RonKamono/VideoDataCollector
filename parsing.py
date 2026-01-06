import yt_dlp
from datetime import datetime

VIDEO_URL = "https://www.youtube.com/shorts/CFwuqHNrzT8"

def format_date(upload_date):
    if not upload_date:
        return None
    return datetime.strptime(upload_date, "%Y%m%d").strftime("%d/%m/%Y")

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_channel_info(channel_url: str) -> dict:
    r = requests.get(channel_url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "channel_name": None,
        "channel_handle": None,
    }

    for meta in soup.find_all("meta"):
        content = meta.get("content", "")
        if "/@" in content:
            handle = content.split("/@")[-1]
            if handle:
                result["channel_handle"] = "@" + handle
                break

    if not result["channel_handle"]:
        m = re.search(r'"canonicalBaseUrl":"(/@[^"]+)"', html)
        if m:
            result["channel_handle"] = m.group(1)

    return result


def get_shorts_count(channel_id: str) -> int:
    shorts_url = f"https://www.youtube.com/channel/{channel_id}/shorts"

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "simulate": True,
        "extract_flat": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(shorts_url, download=False)

    return len(info.get("entries", []))

# ---------- 1. Видео ----------
video_opts = {
    "quiet": True,
    "skip_download": True,
    "simulate": True,      # КЛЮЧЕВОЕ
}

with yt_dlp.YoutubeDL(video_opts) as ydl:
    video_info = ydl.extract_info(VIDEO_URL, download=False)

channel_id = video_info["channel_id"]
channel_url = f"https://www.youtube.com/channel/{channel_id}"

# ---------- 2. Канал ----------
channel_opts = {
    "quiet": True,
    "skip_download": True,
    "simulate": True,
    "extract_flat": True,  # КЛЮЧЕВОЕ
}

with yt_dlp.YoutubeDL(channel_opts) as ydl:
    channel_info = ydl.extract_info(channel_url, download=False)

channel_page_info = get_channel_info(channel_url)
shorts_count = get_shorts_count(channel_id)

data = {
    "video_url": f"https://www.youtube.com/shorts/{video_info['id']}",
    "title": 'YouTube',
    "channel_handle": channel_page_info["channel_handle"][1:],
    "channel_url": channel_url,
    "subscribers": channel_info.get("channel_follower_count"),
    "count_video": shorts_count,
    "publish_date": format_date(video_info.get("upload_date")),
    "views": video_info.get("view_count"),
    "comments": video_info.get("comment_count"),
    "likes": video_info.get("like_count"),
    "reposts": None,
}

for k, v in data.items():
    print(f"{k}: {v}")
