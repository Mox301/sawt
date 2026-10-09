"""Custom CSS: base tweaks for every page and right-to-left layout for Arabic."""

import streamlit as st

from frontend.core.i18n import Lang

BASE_CSS = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}

/* Space between radio buttons and their labels */
[data-testid="stRadio"] label > div[data-testid="stMarkdownContainer"] {
    padding-right: 10px;
    padding-left: 10px;
}
</style>
"""

RTL_CSS = """
<style>
.stApp {
    direction: rtl;
    text-align: right;
}
[data-testid="stRadio"] label > div:first-child {
    margin-left: 10px;
}

/* Charts and numbers stay left-to-right */
.js-plotly-plot {
    direction: ltr;
}
[data-testid="stMetricValue"] {
    direction: ltr;
    text-align: right;
}
[data-testid="stMetricLabel"] {
    text-align: right;
}

.stMarkdown,
[data-testid="stHeading"] {
    text-align: right;
}
.stMarkdown ul {
    padding-right: 1.5rem !important;
    padding-left: 0 !important;
}
.stMarkdown li {
    margin-bottom: 0.5rem !important;
}

/* Expander header: arrow and title with a gap, title aligned right */
[data-testid="stExpander"] summary {
    direction: rtl !important;
    display: flex !important;
    gap: 1.5rem !important;
    align-items: center !important;
}
[data-testid="stExpander"] summary p {
    margin: 0 !important;
    padding: 0 !important;
    text-align: right !important;
    flex: 1 !important;
}

/* File uploader: Arabic size/format hint and button label */
[data-testid="stFileUploader"] {
    text-align: right;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span::after {
    content: "100 ميجابايت كحد أقصى • WAV، MP3، M4A، FLAC، OGG";
    font-size: 0.875rem;
}
/* Only the upload button: uploaded-file chips (with their delete button) also live in the dropzone */
[data-testid="stFileUploaderDropzone"] > span button {
    visibility: hidden;
    position: relative;
}
[data-testid="stFileUploaderDropzone"] > span button::after {
    content: "تحميل";
    visibility: visible;
    position: absolute;
    inset: 0;
    background-color: #ffffff;
    color: #1F2A33;
    border: 1px solid rgba(31, 42, 51, 0.2);
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 400;
}
</style>
"""


def apply_styles(lang: Lang) -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    if lang == "AR":
        st.markdown(RTL_CSS, unsafe_allow_html=True)
