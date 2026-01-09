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
SPREADSHEET_ID = None # add SPREADSHEET_ID

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1


def save_to_sheet(data: dict):
    col_a = sheet.col_values(1)  
    col_b = sheet.col_values(2)  

    target_row = None

    for i in range(1, max(len(col_a), len(col_b))):
        a_val = col_a[i] if i < len(col_a) else ""
        b_val = col_b[i] if i < len(col_b) else ""

        if a_val and not b_val:
            target_row = i + 1 
            break

    if not target_row:
        print("❌ Нет строки с ID в колонке A и пустой B")
        return

    def platform_value(platform, type_):
        if platform == "YouTube":
            return "Youtube shorts"
        if platform == "TikTok":
            return "TikTok"
        if platform == "Instagram":
            return "Instagram"
        return ""

    values = [
        data["video_url"],        
        platform_value(data["platform"], data["type"]),
        data["channel_handle"],   
        data["channel_url"],      
        data["subscribers"],      
        data["count_video"],      
        data["publish_date"],     
        data["views"],            
        data["comments"],         
        data["likes"],            
        data["reposts"],          
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

        pretty_print(data)
        save_to_sheet(data)


# ================== INSTAGRAM ==================
class Instagram:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })
        self.ydl = self._build_ydl()

    def _build_ydl(self):
        try:
            return yt_dlp.YoutubeDL({
                "quiet": True,
                "skip_download": True,
                "simulate": True,
                "no_warnings": True,
                "cookiesfrombrowser": ("firefox",),
            })
        except Exception:
            return yt_dlp.YoutubeDL({
                "quiet": True,
                "skip_download": True,
                "simulate": True,
                "no_warnings": True,
            })

    def format_date(self, ts):
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else None

    # ---------- NUMBER PARSER ----------
    def parse_num(self, s):
        if not s:
            return None

        s = s.strip().lower()
        if not s:
            return None

        s = s.replace(" ", "").replace(",", "")

        try:
            if "тыс" in s:
                return int(float(s.replace("тыс.", "").replace("тыс", "")) * 1_000)
            if "млн" in s:
                return int(float(s.replace("млн", "")) * 1_000_000)
            if s.endswith("k"):
                return int(float(s[:-1]) * 1_000)
            if s.endswith("m"):
                return int(float(s[:-1]) * 1_000_000)
            return int(float(s))
        except ValueError:
            return None

    # ---------- PROFILE ----------
    def get_instagram_profile_info(self, profile_url: str) -> dict:
        r = self.session.get(profile_url, timeout=10)
        r.raise_for_status()
        html = r.text

        result = {
            "subscribers": None,
            "count_video": None
        }

        m = re.search(
            r'<meta property="og:description" content="([^"]+)"',
            html
        )
        if not m:
            return result

        text = m.group(1)

        sub = re.search(
            r'([\d\.,\s]+)\s*(Followers|подписчик[а-я]*)',
            text,
            re.I
        )
        posts = re.search(
            r'([\d\.,\s]+)\s*(Posts|публикац[а-я]*)',
            text,
            re.I
        )

        if sub and sub.group(1):
            result["subscribers"] = self.parse_num(sub.group(1))
        if posts and posts.group(1):
            result["count_video"] = self.parse_num(posts.group(1))

        return result

    # ---------- VIDEO ----------
    def get_reel_views_from_profile(self, username: str, shortcode: str) -> int | None:
        url = f"https://www.instagram.com/{username}/"
        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        html = r.text

        m = re.search(
            r'<script type="application/json".*?>(\{.*?\})</script>',
            html,
            re.DOTALL
        )
        if not m:
            return None

        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return None

        try:
            edges = (
                data["entry_data"]["ProfilePage"][0]
                ["graphql"]["user"]
                ["edge_owner_to_timeline_media"]["edges"]
            )
        except (KeyError, IndexError):
            return None

        for edge in edges:
            node = edge.get("node", {})
            if node.get("shortcode") == shortcode:
                return (
                        node.get("video_view_count")
                        or node.get("edge_play_count", {}).get("count")
                )

        return None

    def collect(self, url):
        try:
            info = self.ydl.extract_info(url, download=False)
        except Exception:
            print("❌ Instagram видео недоступно")
            return

        username = info.get("channel") or info.get("uploader")
        if not username:
            print("❌ Не удалось определить Instagram username")
            return

        profile_url = f"https://www.instagram.com/{username}/"
        profile = self.get_instagram_profile_info(profile_url)

        shortcode = info.get("id")

        profile_views = self.get_reel_views_from_profile(username, shortcode)

        views = (
                info.get("view_count")
                or info.get("play_count")
                or profile_views
                or 0
        )

        data = {
            "platform": "Instagram",
            "type": "Instagram",
            "video_url": info.get("webpage_url"),
            "channel_handle": f"@{username}",
            "channel_url": profile_url,
            "subscribers": profile.get("subscribers"),
            "count_video": profile.get("count_video"),
            "publish_date": self.format_date(info.get("timestamp")),
            "views": views,
            "comments": info.get("comment_count"),
            "likes": info.get("like_count"),
            "reposts": profile.get('reposts')
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
    elif "instagram.com" in domain:
        Instagram().collect(url)

    print(f"⏱ Время выполнения: {time.perf_counter() - start:.2f} сек\n")


if __name__ == '__main__':
       content_url(input('URL: '))
 
