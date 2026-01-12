import yt_dlp
import requests
import json
from datetime import datetime
import browser_cookie3

class Instagram:
    def __init__(self):
        self.session = self._build_session_with_cookies()
        self.ydl = self._build_ydl()

    # -------- SESSION WITH INSTAGRAM COOKIES --------
    def _build_session_with_cookies(self):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/"
        })

        try:
            cookiejar = browser_cookie3.firefox(domain_name="instagram.com")

            # Загружаем cookies в requests
            s.cookies.update(cookiejar)

            # Извлекаем csrftoken
            csrf = None
            for c in cookiejar:
                if c.name == "csrftoken":
                    csrf = c.value
                    break

            if not csrf:
                raise Exception("csrftoken not found in cookies")

            s.headers["X-CSRFToken"] = csrf
            s.headers["X-IG-App-ID"] = "936619743392459"

            print("✅ Instagram cookies + CSRF загружены")

        except Exception as e:
            print("❌ Cookies error:", e)

        return s

    # -------- YT-DLP --------
    def _build_ydl(self):
        return yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "no_warnings": True,
            "cookiesfrombrowser": ("firefox",),
        })

    def format_date(self, ts):
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else None

    # -------- PROFILE  --------
    def shortcode_to_media_id(self, shortcode: str) -> str:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        media_id = 0
        for c in shortcode:
            media_id = media_id * 64 + alphabet.index(c)
        return str(media_id)

    def get_instagram_profile_info(self, username: str):
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

        r = self.session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        user = data["data"]["user"]

        return {
            "subscribers": user["edge_followed_by"]["count"],
            "count_video": user["edge_owner_to_timeline_media"]["count"]
        }

    def get_reel_views(self, media_id: str) -> int | None:
        if not media_id:
            return None

        url = f"https://www.instagram.com/api/v1/media/{media_id}/info/"

        r = self.session.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        items = data.get("items", [])
        if not items:
            return None

        item = items[0]

        return (
                item.get("play_count")
                or item.get("view_count")
                or None
        )

    def debug_media_info(self, media_id: str):
        url = f"https://www.instagram.com/api/v1/media/{media_id}/info/"

        r = self.session.get(url, timeout=10)

        print("\n=== MEDIA INFO DEBUG ===")
        print("URL:", url)
        print("Status:", r.status_code)

        try:
            data = r.json()
            print(json.dumps(data, indent=2))
        except:
            print("RAW TEXT:")
            print(r.text)

        print("=======================\n")

    def get_repost_count(self, media_id: str):
        url = f"https://www.instagram.com/api/v1/media/{media_id}/info/"

        r = self.session.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        items = data.get("items", [])
        if not items:
            return None

        item = items[0]

        return item.get("media_repost_count")

    # -------- VIDEO --------
    def collect(self, url):
        try:
            info = self.ydl.extract_info(url, download=False)
        except Exception:
            print("❌ Instagram видео недоступно")
            return

        username = info.get("channel") or info.get("uploader")
        if not username:
            print("❌ Не удалось определить username")
            return

        profile_url = f"https://www.instagram.com/{username}/"
        profile = self.get_instagram_profile_info(username)

        shortcode = info.get("id")
        media_id = self.shortcode_to_media_id(shortcode)

        views = self.get_reel_views(media_id)
        reposts = self.get_repost_count(media_id)

        self.debug_media_info(media_id)

        data = {
            "platform": "Instagram",
            "type": "Instagram Reel",
            "video_url": info.get("webpage_url"),
            "channel_handle": f"@{username}",
            "channel_url": profile_url,
            "subscribers": profile["subscribers"],
            "count_video": profile["count_video"],
            "publish_date": self.format_date(info.get("timestamp")),
            "views": views,
            "comments": info.get("comment_count"),
            "likes": info.get("like_count"),
            "reposts": reposts
        }
        return data