import yt_dlp
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time

#Class YouTube info parsing above URL

class YouTube:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

        self.video_opts = {
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "no_warnings": True,
        }

        self.shorts_opts = {
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "extract_flat": True,
            "playlistend": 5000,  # защита
            "no_warnings": True,
        }

        self.ydl_video = yt_dlp.YoutubeDL(self.video_opts)
        self.ydl_shorts = yt_dlp.YoutubeDL(self.shorts_opts)

        self.cache_handles = {}
        self.cache_shorts = {}

    def format_date(self, upload_date):
        if not upload_date:
            return None
        return datetime.strptime(upload_date, "%Y%m%d").strftime("%d/%m/%Y")

    def get_channel_info(self, channel_url: str) -> dict:
        if channel_url in self.cache_handles:
            return self.cache_handles[channel_url]

        r = self.session.get(channel_url, timeout=10)
        r.raise_for_status()
        html = r.text

        handle = None
        m = re.search(r'/@([^"/]+)', html)
        if m:
            handle = "@" + m.group(1)

        result = {"channel_handle": handle}
        self.cache_handles[channel_url] = result
        return result

    def get_shorts_count(self, channel_id: str) -> int:
        if channel_id in self.cache_shorts:
            return self.cache_shorts[channel_id]

        shorts_url = f"https://www.youtube.com/channel/{channel_id}/shorts"
        info = self.ydl_shorts.extract_info(shorts_url, download=False)

        count = len(info.get("entries", []))
        self.cache_shorts[channel_id] = count
        return count

    def decode_if_needed(self, value):
        from urllib.parse import unquote
        if not value:
            return None
        return unquote(value) if "%" in value else value

    def pretty_print(self, data: dict):
        print("\n" + "=" * 50)
        print(f"🔗 Видео:            {data.get('video_url')}")
        print(f"📹 Тип:              {data.get('type')}")
        print("-" * 50)
        print(f"👤 Канал:            {data.get('channel_handle')}")
        print(f"🌐 URL канала:       {data.get('channel_url')}")
        print(f"👥 Подписчики:       {data.get('subscribers')}")
        print(f"🎬 Shorts всего:     {data.get('count_video')}")
        print("-" * 50)
        print(f"📅 Дата публикации:  {data.get('publish_date')}")
        print(f"👁 Просмотры:         {data.get('views')}")
        print(f"💬 Комментарии:      {data.get('comments')}")
        print(f"👍 Лайки:            {data.get('likes')}")
        print(f"🔁 Репосты:          {data.get('reposts')}")
        print("=" * 50 + "\n")

    def get_info_youtube(self, video_url: str):
        video_info = self.ydl_video.extract_info(video_url, download=False)

        channel_id = video_info["channel_id"]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        channel_page = self.get_channel_info(channel_url)
        raw_handle = channel_page.get("channel_handle")
        channel_handle = self.decode_if_needed(raw_handle)

        shorts_count = self.get_shorts_count(channel_id)

        data = {
            "video_url": f"https://www.youtube.com/shorts/{video_info['id']}",
            "type": 'Youtube shorts',
            "channel_handle": channel_handle,
            "channel_url": channel_url,
            "subscribers": video_info.get("channel_follower_count"),
            "count_video": shorts_count,
            "publish_date": self.format_date(video_info.get("upload_date")),
            "views": video_info.get("view_count"),
            "comments": video_info.get("comment_count"),
            "likes": video_info.get("like_count"),
            "reposts": "",
        }

        self.pretty_print(data)
        return data


#Class TikTok info parsing above URL
class TikTok:
    def __init__(self):
        pass

#Class Instagram info parsing above URL
class Instagram:
    def __init__(self):
        pass



def content_url(url: str):
    start = time.perf_counter()   # ⏱ старт
    print('Run collect')
    parsed = urlparse(url.lower())
    domain = parsed.netloc

    if "youtube.com" in domain or "youtu.be" in domain:
        yt = YouTube()
        yt.get_info_youtube(url)

    elif "tiktok.com" in domain:
        print("TikTok: пока не реализовано")

    elif "instagram.com" in domain:
        print("Instagram: пока не реализовано")

    else:
        print("Платформа не поддерживается")

    end = time.perf_counter()     # ⏱ конец
    print(f"\n⏱ Время выполнения: {end - start:.2f} сек\n")

while True:
    content_url(input("Write URL: "))