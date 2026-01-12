import os

class WindowsSize:
    window_height = 850
    window_width = 1000

class Colors:
    color_bg = "#0F0F13"
    secondary_bg = "#1E1E24"
    surface = "#2A2A32"
    text_primary = "#FFFFFF"
    text_secondary = "#B0B0B8"
    accent = "#4A90E2"
    accent_hover = "#3A7BC8"
    success = "#4CAF50"
    warning = "#FF9800"
    error = "#F44336"



def _get_config_path():
    base = os.environ.get("LOCALAPPDATA")
    app_dir = os.path.join(base, "VideoDataCollector")

    os.makedirs(app_dir, exist_ok=True)

    return os.path.join(app_dir, "spreadsheet.json")

