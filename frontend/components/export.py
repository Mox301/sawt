"""Download buttons for the raw JSON result and the plain-text report."""

import json
from datetime import datetime
from typing import Any

import streamlit as st

from frontend.core.i18n import Lang, t
from frontend.services.report import build_report


def render_export(data: dict[str, Any], file_name: str, lang: Lang) -> None:
    st.markdown(f"### {t('export_results', lang)}")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            t("download_json", lang),
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name=f"analysis_{stamp}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            t("download_report", lang),
            data=build_report(data, file_name),
            file_name=f"report_{stamp}.txt",
            mime="text/plain",
            use_container_width=True,
        )
