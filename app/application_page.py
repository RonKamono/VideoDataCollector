# ---------- UI ----------
import flet as ft

# ---------- System ----------
import asyncio
import os
import time
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

# ---------- Network ----------
import requests

# ---------- yt-dlp ----------
import yt_dlp

# ---------- Browser cookies ----------
import browser_cookie3

# ---------- Playwright (ASYNC) ----------
from playwright.async_api import async_playwright

# ---------- Your modules ----------
from functions.save_data import DataSave


data_save = DataSave()

class AppPage:
# --------------- INIT ---------------
    def __init__(self, page, colors):
        self.page = page
        self.colors = colors
        self.data_video = None
        self.instagram_collect = Instagram()
        self.tiktok_collect = TikTok()
        self.youtube_collect = YouTube()

        # --------------- INIT CREATE ---------------
        self._create_text_fields()
        self._create_buttons()
        self._create_containers()

        # --------------- BUILD ---------------
        self.application_page = self._build_app_view()

        self._load_spreadsheet()

# --------------- CREATE ---------------
    def _create_text_field(self, **kwargs):
        """Создает стандартное текстовое поле"""
        defaults = {
            'height': 50,
            'width': 380,
            'value': '',
            'bgcolor': self.colors.secondary_bg,
            'border_radius': 16,
            'border_color': self.colors.color_bg,
            'text_align': ft.TextAlign.CENTER,
            'text_style': ft.TextStyle(
                color=self.colors.text_primary,
                size=16,
                weight=ft.FontWeight.W_500,
            ),
        }
        defaults.update(kwargs)
        return ft.TextField(**defaults)

    def _create_text_fields(self):
        """Создает все текстовые поля"""
        self.url_spreadsheet = self._create_text_field(hint_text='URL SPREADSHEET :')
        self.url_textfield = self._create_text_field(hint_text='URL COLLECT :')

        self.video_url = self._create_text_field(bgcolor=self.colors.color_bg)
        self.type_platform = self._create_text_field(bgcolor=self.colors.color_bg)
        self.channel_id = self._create_text_field(bgcolor=self.colors.color_bg)
        self.channel_url = self._create_text_field(bgcolor=self.colors.color_bg)
        self.subscriber_count = self._create_text_field(bgcolor=self.colors.color_bg)
        self.video_count = self._create_text_field(bgcolor=self.colors.color_bg)
        self.time_upload = self._create_text_field(bgcolor=self.colors.color_bg)
        self.view_count = self._create_text_field(bgcolor=self.colors.color_bg)
        self.comments_count = self._create_text_field(bgcolor=self.colors.color_bg)
        self.like_count = self._create_text_field(bgcolor=self.colors.color_bg)
        self.repost_count = self._create_text_field(bgcolor=self.colors.color_bg)

    def _create_buttons(self):
        """Создает кнопки"""
        button_style = {
            'color': self.colors.text_primary,
            'bgcolor': self.colors.surface,
            'width': 185,
            'height': 40,
        }

        self.confirm_button = ft.ElevatedButton(
            content=ft.Text('Collect', size=16),
            on_click=lambda e: self.page.run_task(self._collect_data),
            **button_style
        )


        self.send_data_button = ft.ElevatedButton(
            content=ft.Text('Send', size=16),
            on_click=lambda e: self._save_data(e),
            **button_style
        )

        self.save_spreadsheet = ft.ElevatedButton(
            content=ft.Text('Save spreadsheet', size=16),
            on_click=lambda e: self._save_spreadsheet(e),
            color = self.colors.text_primary,
            bgcolor = self.colors.surface,
            width = 380,
            height = 40,
        )

    def _create_container_with_text(self, name, textfield):
        return ft.Container(
            padding=ft.padding.symmetric(0,32),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=140,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=ft.Text(
                            name,
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color=self.colors.text_primary,
                        ),
                    ),
                    ft.Container(  # поле всегда начинается с одной линии
                        expand=True,
                        content=textfield,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def _create_containers(self):
        self.video_url_container = self._create_container_with_text('VIDEO URL: ', self.video_url)
        self.type_platform_container = self._create_container_with_text('PLATFORM: ', self.type_platform)
        self.channel_id_container = self._create_container_with_text('CHANNEL ID: ', self.channel_id)
        self.channel_url_container = self._create_container_with_text('CHANNEL URL: ', self.channel_url)
        self.subscriber_count_container = self._create_container_with_text('SUBSCRIBERS: ', self.subscriber_count)
        self.video_count_container = self._create_container_with_text('VIDEO COUNT: ', self.video_count)
        self.time_upload_container = self._create_container_with_text('LOADING TIME : ', self.time_upload)
        self.view_count_container = self._create_container_with_text('VIEWS: ', self.view_count)
        self.comments_count_container = self._create_container_with_text('COMMENTS: ', self.comments_count)
        self.like_count_container = self._create_container_with_text('LIKES: ', self.like_count)
        self.repost_count_container =self._create_container_with_text('REPOSTS: ', self.repost_count)
# --------------- BUILD VIEW ---------------
    def _build_app_view(self):
        return ft.Row(
            controls=[
                ft.Column(
                    expand=2,
                    controls=[
                        ft.Text('VIDEO DATA COLLECTOR',
                                size=32,
                                weight=ft.FontWeight.W_600,
                                color=self.colors.text_primary),
                        self.url_spreadsheet,
                        self.url_textfield,
                        ft.Row(
                            controls=[
                                self.confirm_button,
                                self.send_data_button
                            ],alignment = ft.MainAxisAlignment.CENTER
                        ),
                        self.save_spreadsheet
                    ], alignment = ft.MainAxisAlignment.CENTER, horizontal_alignment = ft.CrossAxisAlignment.CENTER
                ),
                ft.Column(
                    expand=3,
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=ft.padding.symmetric(20, 0),
                            bgcolor=self.colors.secondary_bg,
                            border_radius=40,
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Container(
                                        border_radius=40,
                                        padding=ft.padding.symmetric(15, 165),
                                        bgcolor=self.colors.color_bg,
                                        content=ft.Text('VIDEO INFO',
                                            size=32,
                                            weight=ft.FontWeight.W_600,
                                            color=self.colors.text_primary),
                                    ),
                                    self.video_url_container,
                                    self.type_platform_container,
                                    self.channel_id_container,
                                    self.channel_url_container,
                                    self.subscriber_count_container,
                                    self.video_count_container,
                                    self.time_upload_container,
                                    self.view_count_container,
                                    self.comments_count_container,
                                    self.like_count_container,
                                    self.repost_count_container

                                ], alignment = ft.MainAxisAlignment.CENTER, horizontal_alignment = ft.CrossAxisAlignment.CENTER
                            )
                        )
                    ], alignment = ft.MainAxisAlignment.CENTER, horizontal_alignment = ft.CrossAxisAlignment.CENTER
                )
            ], alignment = ft.MainAxisAlignment.CENTER
        )


# --------------- APP FUNCTIONS  ---------------
    async def _collect_data(self):
        video_url = self.url_textfield.value

        await self.content_url(video_url)

        if not self.data_video:
            print("❌ Data not received")
            return

        self.video_url.value = self.data_video['video_url']
        self.type_platform.value = self.data_video['platform']
        self.channel_id.value = self.data_video['channel_handle']
        self.channel_url.value = self.data_video['channel_url']
        self.subscriber_count.value = str(self.data_video['subscribers'])
        self.video_count.value = str(self.data_video['count_video'])
        self.time_upload.value = self.data_video['publish_date']
        self.view_count.value = str(self.data_video['views'])
        self.comments_count.value = str(self.data_video['comments'])
        self.like_count.value = str(self.data_video['likes'])
        self.repost_count.value = str(self.data_video['reposts'])

        self.url_textfield.value = ""
        self.application_page.update()

    def _save_data(self, e):
        spreadsheet_url = self.get_spreadsheet_url()
        if not spreadsheet_url:
            return

        data = {
            "video_url": self.video_url.value,
            "platform": self.type_platform.value,
            "type": self.type_platform.value,
            "channel_handle": self.channel_id.value,
            "channel_url": self.channel_url.value,
            "subscribers": self.subscriber_count.value,
            "count_video": self.video_count.value,
            "publish_date": self.time_upload.value,
            "views": self.view_count.value,
            "comments": self.comments_count.value,
            "likes": self.like_count.value,
            "reposts": self.repost_count.value,
        }

        saver = DataSave()
        saver.save_to_sheet(data, spreadsheet_url)

    def _save_spreadsheet(self, e):
        from config.settings import _get_config_path
        url = self.url_spreadsheet.value.strip()
        if not url:
            return

        path = _get_config_path()

        with open(path, "w", encoding="utf-8") as f:
            json.dump({"spreadsheet_url": url}, f, ensure_ascii=False, indent=2)

        print(f"✅ Spreadsheet сохранён: {path}")

    def _load_spreadsheet(self):
        from config.settings import _get_config_path
        path = _get_config_path()

        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.url_spreadsheet.value = data.get("spreadsheet_url", "")
            self.url_spreadsheet.update()
        except:
            pass

    def get_spreadsheet_url(self): # --------------- Функция получения ссылки на таблицу ---------------
        return self.url_spreadsheet.value

    async def content_url(self, url: str):
        start = time.perf_counter()
        print("Run collect")

        domain = urlparse(url).netloc.lower()
        print(f"DOMAIN=[{domain}]")

        if "youtube.com" in domain or "youtu.be" in domain:
            self.data_video = self.youtube_collect.collect(url)

        elif "instagram.com" in domain:
            self.data_video = self.instagram_collect.collect(url)

        elif "tiktok.com" in domain:
            self.data_video = await self.tiktok_collect.collect(url)
        else:
            self.data_video = None

        print(f"⏱ Время выполнения: {time.perf_counter() - start:.2f} сек\n")


# ---------- PARSING CLASS ----------
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

class TikTok:
    def __init__(self):
        base = os.environ.get("LOCALAPPDATA")
        self.app_dir = os.path.join(base, "VideoDataCollector")
        os.makedirs(self.app_dir, exist_ok=True)

        # Netscape cookies for yt-dlp
        self.cookie_file = os.path.join(self.app_dir, "tiktok_cookies.txt")

        # Persistent Chromium profile (важно)
        self.browser_dir = os.path.join(self.app_dir, "chromium_profile")
        os.makedirs(self.browser_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        self.ydl = yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "simulate": True,
            "cookies": self.cookie_file,
        })

    # ---------- COOKIES ----------
    async def ensure_cookies(self):
        if Path(self.cookie_file).exists():
            return
        await self._fetch_cookies()

    async def _fetch_cookies(self):
        print("🔐 Получаем TikTok cookies через Chromium (persistent)…")

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                self.browser_dir,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            )

            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto(
                "https://www.tiktok.com",
                wait_until="domcontentloaded",
                timeout=60000
            )

            await page.wait_for_selector("body")

            cookies = await context.cookies()
            await context.close()

        self._save_cookies(cookies)

        # Загружаем cookies в requests-сессию
        for c in cookies:
            self.session.cookies.set(
                c["name"], c["value"], domain=c["domain"], path=c["path"]
            )

    def _save_cookies(self, cookies):
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                f.write(
                    f"{c['domain']}\tTRUE\t{c['path']}\t"
                    f"{'TRUE' if c['secure'] else 'FALSE'}\t"
                    f"{int(c.get('expires', 0))}\t"
                    f"{c['name']}\t{c['value']}\n"
                )

    # ---------- HELPERS ----------
    def format_date(self, ts):
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else None

    def get_profile_info(self, url):
        if not url:
            return {"subscribers": 0, "count_video": 0}

        html = self.session.get(url, timeout=10).text
        subs = re.search(r'"followerCount":(\d+)', html)
        vids = re.search(r'"videoCount":(\d+)', html)

        return {
            "subscribers": int(subs.group(1)) if subs else 0,
            "count_video": int(vids.group(1)) if vids else 0,
        }


    def normalize_url(self, url: str) -> str:
        url = url.split("?")[0]

        if "/photo/" in url:
            parts = url.split("/photo/")
            return parts[0] + "/video/" + parts[1]

        return url


    # ---------- MAIN ----------
    async def collect(self, url):
        await self.ensure_cookies()

        try:
            url = self.normalize_url(url)
            info = self.ydl.extract_info(url, download=False)
        except Exception as e:
            print("❌ TikTok недоступен даже с cookies:", e)
            return None

        profile_url = info.get("uploader_url")
        profile = self.get_profile_info(profile_url)

        reposts = (
            info.get("repost_count")
            if info.get("repost_count") is not None
            else info.get("share_count")
        )

        return {
            "platform": "TikTok",
            "type": "TikTok Photo" if "photo" in url else "TikTok Video",
            "video_url": url,
            "channel_handle": f"@{info.get('uploader','')}",
            "channel_url": profile_url,
            "subscribers": profile["subscribers"],
            "count_video": profile["count_video"],
            "publish_date": self.format_date(info.get("timestamp")),
            "views": info.get("view_count", 0),
            "comments": info.get("comment_count", 0),
            "likes": info.get("like_count", 0),
            "reposts": reposts,
        }

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
