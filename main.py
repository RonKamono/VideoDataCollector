import yt_dlp
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

#Class YouTube info parsing above URL
class YouTube:
    def __init__(self):
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0"
        }

        self.video_opts = {
            "quiet": True,
            "skip_download": True,
            "simulate": True,      # КЛЮЧЕВОЕ
        }

        self.channel_opts = {
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "extract_flat": True,  # КЛЮЧЕВОЕ
        }

    def format_date(self, upload_date):
        if not upload_date:
            return None
        return datetime.strptime(upload_date, "%Y%m%d").strftime("%d/%m/%Y")

    def get_channel_info(self ,channel_url: str) -> dict:
        r = requests.get(channel_url, headers=self.HEADERS, timeout=10)
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

    def get_shorts_count(self, channel_id: str) -> int:
        shorts_url = f"https://www.youtube.com/channel/{channel_id}/shorts"

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "extract_flat": True,   # ЗДЕСЬ это НУЖНО
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(shorts_url, download=False)

        return len(info.get("entries", []))

    def decode_if_needed(self, value: str | None) -> str | None:
        from urllib.parse import unquote

        if not value:
            return None

        # есть URL-encoding → декодируем
        if "%" in value:
            return unquote(value)

        # обычная строка → не трогаем
        return value

    def get_info_youtube(self, _video_url):
        with yt_dlp.YoutubeDL(self.video_opts) as ydl:
            video_info = ydl.extract_info(_video_url, download=False)

        channel_id = video_info["channel_id"]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        with yt_dlp.YoutubeDL(self.channel_opts) as ydl:
            channel_info = ydl.extract_info(channel_url, download=False)

        channel_page_info = self.get_channel_info(channel_url)
        shorts_count = self.get_shorts_count(channel_id)


        raw_handle = channel_page_info["channel_handle"][1:]
        channel_handle = self.decode_if_needed(raw_handle)

        data = {
            "video_url": f"https://www.youtube.com/shorts/{video_info['id']}",
            "title": 'Youtube shorts',
            "channel_handle": channel_handle,
            "channel_url": channel_url,
            "subscribers": channel_info.get("channel_follower_count"),
            "count_video": shorts_count,
            "publish_date": self.format_date(video_info.get("upload_date")),
            "views": video_info.get("view_count"),
            "comments": video_info.get("comment_count"),
            "likes": video_info.get("like_count"),
            "reposts": '',
        }

        for k, v in data.items():
            print(f"{k}: {v}")

#Class TikTok info parsing above URL
class TikTok:
    def __init__(self):
        pass

#Class Instagram info parsing above URL
class Instagram:
    def __init__(self):
        pass



def content_url(url: str):
    parsed = urlparse(url.lower())
    domain = parsed.netloc

    if "youtube.com" in domain or "youtu.be" in domain:
        yt = YouTube()
        yt.get_info_youtube(url)
        return

    if "tiktok.com" in domain:
        print("TikTok: пока не реализовано")
        return

    if "instagram.com" in domain:
        print("Instagram: пока не реализовано")
        return

    print("Платформа не поддерживается")

while True:
    content_url(input())