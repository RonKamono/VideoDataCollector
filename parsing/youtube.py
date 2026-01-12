import yt_dlp
import requests
import re

from datetime import datetime


class YouTube:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        self.ydl_video = yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "simulate": True,
        })

        self.ydl_shorts = yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "extract_flat": True,
            "playlistend": 5000,
        })

    def format_date(self, d):
        return datetime.strptime(d, "%Y%m%d").strftime("%d/%m/%Y") if d else None

    def get_channel_handle(self, channel_url):
        html = self.session.get(channel_url).text
        m = re.search(r'/@([^"/]+)', html)
        return f"@{m.group(1)}" if m else ""

    def get_shorts_count(self, channel_id):
        url = f"https://www.youtube.com/channel/{channel_id}/shorts"
        info = self.ydl_shorts.extract_info(url, download=False)
        return len(info.get("entries", []))

    def collect(self, url):
        info = self.ydl_video.extract_info(url, download=False)

        channel_id = info["channel_id"]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        data = {
            "platform": "YouTube",
            "type": "YouTube Shorts" if "/shorts/" in url else "YouTube Video",
            "video_url": f"https://www.youtube.com/watch?v={info['id']}",
            "channel_handle": self.get_channel_handle(channel_url),
            "channel_url": channel_url,
            "subscribers": info.get("channel_follower_count", 0),
            "count_video": self.get_shorts_count(channel_id),
            "publish_date": self.format_date(info.get("upload_date")),
            "views": info.get("view_count", 0),
            "comments": info.get("comment_count", 0),
            "likes": info.get("like_count", 0),
            "reposts": "",
        }

        return data
