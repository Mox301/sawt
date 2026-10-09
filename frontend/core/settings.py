"""App-wide settings and constants."""

import os
from typing import Any

API_URL: str = os.environ.get("SAWT_API_URL", "http://localhost:8000").rstrip("/")
ANALYSIS_TIMEOUT_S = 3600
HEALTH_TIMEOUT_S = 3
HEALTH_CACHE_TTL_S = 10

AUDIO_TYPES = ["wav", "mp3", "m4a", "flac", "ogg"]
REPO_URL = "github.com/Mox301/sawt"

# Calm palette that starts with the theme's primary colour (.streamlit/config.toml).
CHART_COLORS = ["#1F6E8C", "#E0A458", "#5FA8A0", "#9C6B98", "#7A8B99", "#C8645B"]

PAGE_CONFIG: dict[str, Any] = {
    "page_title": "Sawt · صوت",
    "page_icon": "🎙️",
    "layout": "wide",
}
