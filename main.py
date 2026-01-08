import yt_dlp
import requests
import re
import json
import time
from datetime import datetime
from urllib.parse import urlparse
import gspread
from google.oauth2.service_account import Credentials

# ================== GOOGLE SHEETS ==================
SERVICE_ACCOUNT_FILE = "service_account.json"
SPREADSHEET_ID = "19bHwNqlLUTsdNVAz8SP5GZmY_dC6NuTlOusRnLFcjxg"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1


def save_to_sheet(data: dict):
    col_a = sheet.col_values(1)  # №
    col_b = sheet.col_values(2)  # Ссылка на видео

    target_row = None

    # начинаем с 2 строки (после шапки)
    for i in range(1, max(len(col_a), len(col_b))):
        a_val = col_a[i] if i < len(col_a) else ""
        b_val = col_b[i] if i < len(col_b) else ""

        if a_val and not b_val:
            target_row = i + 1  # +1 потому что индексы с 0
            break

    if not target_row:
        print("❌ Нет строки с ID в колонке A и пустой B")
        return

    def platform_value(platform, type_):
        if platform == "YouTube":
            return "Youtube shorts"
        if platform == "TikTok":
            return "TikTok"
        return ""

    values = [
        data["video_url"],        # B
        platform_value(data["platform"], data["type"]),  # C ← ВАЖНО
        data["channel_handle"],   # D
        data["channel_url"],      # E
        data["subscribers"],      # F
        data["count_video"],      # G
        data["publish_date"],     # H
        data["views"],            # I
        data["comments"],         # J
        data["likes"],            # K
        data["reposts"],          # L
    ]

    sheet.update(
        range_name=f"B{target_row}:L{target_row}",
        values=[values],
        value_input_option="USER_ENTERED"
    )

    print(f"✅ Записано в строку {target_row}")



def pretty_print(data: dict):
    print("\n" + "=" * 50)
    print(f"🔗 Видео:            {data['video_url']}")
    print(f"📹 Тип:              {data['type']}")
    print(f"🌍 Платформа:        {data['platform']}")
    print("-" * 50)
    print(f"👤 Канал:            {data['channel_handle']}")
    print(f"🌐 URL канала:       {data['channel_url']}")
    print(f"👥 Подписчики:       {data['subscribers']}")
    print(f"🎬 Видео всего:      {data['count_video']}")
    print("-" * 50)
    print(f"📅 Дата публикации:  {data['publish_date']}")
    print(f"👁 Просмотры:        {data['views']}")
    print(f"💬 Комментарии:      {data['comments']}")
    print(f"👍 Лайки:            {data['likes']}")
    print(f"🔁 Репосты:          {data['reposts']}")
    print("=" * 50 + "\n")


# ================== YOUTUBE ==================
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

        pretty_print(data)
        save_to_sheet(data)


# ================== TIKTOK ==================
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
            "reposts": info.get("share_count", 0),
        }

        pretty_print(data)
        save_to_sheet(data)


# ================== ROUTER ==================
def content_url(url: str):
    start = time.perf_counter()
    print("Run collect")

    domain = urlparse(url).netloc

    if "youtube.com" in domain or "youtu.be" in domain:
        YouTube().collect(url)
    elif "tiktok.com" in domain:
        TikTok().collect(url)
    else:
        print("Платформа не поддерживается")

    print(f"⏱ Время выполнения: {time.perf_counter() - start:.2f} сек\n")


while True:
    content_url(input('URL: '))
    sh = gc.open_by_key(SPREADSHEET_ID)
    print([ws.title for ws in sh.worksheets()])

