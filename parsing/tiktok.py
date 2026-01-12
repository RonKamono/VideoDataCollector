import yt_dlp
import requests
import re
from datetime import datetime

class TikTok:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.ydl = yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "simulate": True,
        })

    def format_date(self, ts):
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else None

    def get_profile_info(self, url):
        html = self.session.get(url).text
        subs = re.search(r'"followerCount":(\d+)', html)
        vids = re.search(r'"videoCount":(\d+)', html)
        return {
            "subscribers": int(subs.group(1)) if subs else 0,
            "count_video": int(vids.group(1)) if vids else 0,
        }

    def collect(self, url):
        try:
            info = self.ydl.extract_info(url, download=False)
        except Exception:
            print("❌ TikTok видео недоступно без логина")
            return

        profile = self.get_profile_info(info["uploader_url"])

        reposts = None
        if info:
            reposts = (
                info.get("repost_count")
                if info.get("repost_count") is not None
                else info.get("share_count")
            )

        data = {
            "platform": "TikTok",
            "type": "TikTok Video",
            "video_url": url,
            "channel_handle": f"@{info['uploader']}",
            "channel_url": info["uploader_url"],
            "subscribers": profile["subscribers"],
            "count_video": profile["count_video"],
            "publish_date": self.format_date(info.get("timestamp")),
            "views": info.get("view_count", 0),
            "comments": info.get("comment_count", 0),
            "likes": info.get("like_count", 0),
            "reposts": reposts
        }

        return data