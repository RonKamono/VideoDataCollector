from google.oauth2.service_account import Credentials
import gspread
import re

class DataSave:
    def __init__(self):
        pass

    def _spreadsheet_url(self, spreadsheet_url):
        SERVICE_ACCOUNT_FILE = "service_account.json"
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        # Извлекаем Spreadsheet ID из URL
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", spreadsheet_url)
        if not match:
            raise ValueError("Невалидная ссылка на Google Sheets")

        spreadsheet_id = match.group(1)

        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(spreadsheet_id).sheet1

        return sheet

    def save_to_sheet(self, data: dict, spreadsheet_url):
        sheet = self._spreadsheet_url(spreadsheet_url)

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

    def pretty_print(self, data: dict):
        print("\n" + "=" * 50)
        print(f"Видео:             {data['video_url']}")
        print(f"Тип:               {data['type']}")
        print(f"Платформа:         {data['platform']}")
        print("-" * 50)
        print(f"Канал:             {data['channel_handle']}")
        print(f"URL канала:        {data['channel_url']}")
        print(f"Подписчики:        {data['subscribers']}")
        print(f"Видео всего:       {data['count_video']}")
        print("-" * 50)
        print(f"Дата публикации:   {data['publish_date']}")
        print(f"Просмотры:         {data['views']}")
        print(f"Комментарии:       {data['comments']}")
        print(f"Лайки:             {data['likes']}")
        print(f"Репосты:           {data['reposts']}")
        print("=" * 50 + "\n")