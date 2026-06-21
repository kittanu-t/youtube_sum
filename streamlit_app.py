"""Streamlit frontend for the YouTube Summarization Agent."""

import os

import requests
import streamlit as st

# ── Page config ────────────────────────────────────────────────────

st.set_page_config(
    page_title="youtube_sum",
    page_icon="🎬",
    layout="wide",
)

# ── State ──────────────────────────────────────────────────────────

if "summary_result" not in st.session_state:
    st.session_state.summary_result = None
if "notes_result" not in st.session_state:
    st.session_state.notes_result = None
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "error" not in st.session_state:
    st.session_state.error = None
if "loading" not in st.session_state:
    st.session_state.loading = False

# ── API config ─────────────────────────────────────────────────────

API_URL = os.environ.get("API_URL", "http://localhost:8000/api")


def api_post(endpoint: str, payload: dict) -> dict:
    """POST to the API and return JSON response."""
    resp = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()


def api_get(endpoint: str, params: dict = None) -> dict:
    """GET from the API and return JSON response."""
    resp = requests.get(f"{API_URL}/{endpoint}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Sidebar ────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Settings")

    api_url = st.text_input("API URL", value=API_URL)
    if api_url != API_URL:
        API_URL = api_url

    language = st.selectbox(
        "Output Language",
        options=["en", "th"],
        format_func=lambda x: "English" if x == "en" else "Thai (ไทย)",
    )

    summary_level = st.selectbox(
        "Summary Level",
        options=["short", "detailed", "bullet"],
        format_func=lambda x: {"short": "Short", "detailed": "Detailed", "bullet": "Bullet Points"}[
            x
        ],
    )

    st.divider()

    if st.button("🗑️ Clear History", type="secondary"):
        try:
            requests.delete(f"{API_URL}/history", timeout=10)
            st.success("History cleared")
        except Exception as exc:
            st.error(f"Failed: {exc}")

    st.divider()
    st.caption("youtube_sum v0.1.0")

# ── Main UI ────────────────────────────────────────────────────────

st.title("🎬 YouTube Summarization Agent")
st.markdown("Paste a YouTube URL to get a summary, study notes, and more.")

# URL Input
url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    summarize_clicked = st.button("📝 Summarize", type="primary", use_container_width=True)
with col2:
    notes_clicked = st.button("📚 Study Notes", type="primary", use_container_width=True)

# ── Processing ─────────────────────────────────────────────────────

if summarize_clicked and url:
    st.session_state.error = None
    st.session_state.summary_result = None
    st.session_state.video_info = None

    try:
        with st.spinner("🔍 Fetching video info..."):
            info = api_get("video-info", params={"url": url})
            st.session_state.video_info = info

        with st.spinner("📝 Generating summary..."):
            result = api_post(
                "summarize",
                {
                    "url": url,
                    "level": summary_level,
                    "language": language,
                },
            )
            st.session_state.summary_result = result

    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc)) if exc.response else str(exc)
        st.session_state.error = detail
    except Exception as exc:
        st.session_state.error = str(exc)

if notes_clicked and url:
    st.session_state.error = None
    st.session_state.notes_result = None
    st.session_state.video_info = None

    try:
        with st.spinner("🔍 Fetching video info..."):
            info = api_get("video-info", params={"url": url})
            st.session_state.video_info = info

        with st.spinner("📚 Generating study notes..."):
            result = api_post(
                "notes",
                {
                    "url": url,
                    "language": language,
                },
            )
            st.session_state.notes_result = result

    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc)) if exc.response else str(exc)
        st.session_state.error = detail
    except Exception as exc:
        st.session_state.error = str(exc)

# ── Error display ──────────────────────────────────────────────────

if st.session_state.error:
    st.error(f"❌ {st.session_state.error}")

# ── Video info ─────────────────────────────────────────────────────

if st.session_state.video_info:
    info = st.session_state.video_info
    st.divider()

    # Thumbnail + metadata
    if info.get("thumbnail"):
        thumb_col, meta_col = st.columns([1, 3])
        with thumb_col:
            st.image(info["thumbnail"], use_container_width=True)
        with meta_col:
            st.subheader(info.get("title", "Unknown Title"))
            st.markdown(f"**Channel:** {info.get('channel', 'Unknown')}")
            st.markdown(f"**Duration:** {info.get('duration', 'Unknown')}")
            st.markdown(f"**Language:** {language}")
    else:
        st.subheader(info.get("title", "Unknown Title"))
        st.markdown(
            f"**Channel:** {info.get('channel', 'Unknown')} | **Duration:** {info.get('duration', 'Unknown')}"
        )

# ── Summary output ─────────────────────────────────────────────────

if st.session_state.summary_result:
    result = st.session_state.summary_result
    st.divider()
    st.header("📝 Summary")

    st.markdown(result.get("summary", ""))

    # Chapters
    chapters = result.get("chapters", [])
    if chapters:
        st.divider()
        st.header("⏱️ Chapters")
        for ch in chapters:
            ts = ch.get("timestamp", "00:00")
            title = ch.get("title", "Untitled")
            st.markdown(f"**{ts}** — {title}")

    # Key Points
    key_points = result.get("key_points", [])
    if key_points:
        st.divider()
        st.header("📌 Key Points")
        for point in key_points:
            st.markdown(f"- {point}")

    # Export buttons
    st.divider()
    st.header("📥 Export")

    export_col1, export_col2, export_col3, export_col4 = st.columns(4)

    try:
        export_payload = {
            "video_id": result.get("video_id", ""),
            "video_title": result.get("title", ""),
            "channel": result.get("channel", ""),
            "duration": result.get("duration", ""),
            "language": language,
            "summary": result.get("summary", ""),
            "chapters": chapters,
            "key_points": key_points,
        }

        with export_col1:
            md_resp = api_post("export", {**export_payload, "format": "markdown"})
            st.download_button(
                "📄 Download Markdown",
                data=md_resp["content"],
                file_name=md_resp["filename"],
                mime=md_resp["mime_type"],
                use_container_width=True,
            )

        with export_col2:
            txt_resp = api_post("export", {**export_payload, "format": "txt"})
            st.download_button(
                "📝 Download TXT",
                data=txt_resp["content"],
                file_name=txt_resp["filename"],
                mime=txt_resp["mime_type"],
                use_container_width=True,
            )

        with export_col3:
            json_resp = api_post("export", {**export_payload, "format": "json"})
            st.download_button(
                "🔧 Download JSON",
                data=json_resp["content"],
                file_name=json_resp["filename"],
                mime=json_resp["mime_type"],
                use_container_width=True,
            )

        with export_col4:
            if st.button("📋 Copy Summary", use_container_width=True):
                st.code(result.get("summary", ""), language="markdown")

    except Exception as exc:
        st.warning(f"Export unavailable: {exc}")

# ── Study Notes output ─────────────────────────────────────────────

if st.session_state.notes_result:
    result = st.session_state.notes_result
    st.divider()
    st.header("📚 Study Notes")

    st.markdown(result.get("study_notes", ""))

    # Chapters
    chapters = result.get("chapters", [])
    if chapters:
        st.divider()
        st.header("⏱️ Timeline")
        for ch in chapters:
            ts = ch.get("timestamp", "00:00")
            title = ch.get("title", "Untitled")
            st.markdown(f"**{ts}** — {title}")

    # Export
    st.divider()
    st.header("📥 Export Notes")

    export_col1, export_col2, export_col3 = st.columns(3)

    try:
        export_payload = {
            "video_id": result.get("video_id", ""),
            "video_title": result.get("title", ""),
            "study_notes": result.get("study_notes", ""),
            "chapters": chapters,
            "language": language,
        }

        with export_col1:
            md_resp = api_post("export", {**export_payload, "format": "markdown"})
            st.download_button(
                "📄 Download Markdown",
                data=md_resp["content"],
                file_name=md_resp["filename"],
                mime=md_resp["mime_type"],
                use_container_width=True,
            )

        with export_col2:
            txt_resp = api_post("export", {**export_payload, "format": "txt"})
            st.download_button(
                "📝 Download TXT",
                data=txt_resp["content"],
                file_name=txt_resp["filename"],
                mime=txt_resp["mime_type"],
                use_container_width=True,
            )

        with export_col3:
            csv_resp = api_post("export", {**export_payload, "format": "csv"})
            st.download_button(
                "🃏 Flashcards CSV",
                data=csv_resp["content"],
                file_name=csv_resp["filename"],
                mime=csv_resp["mime_type"],
                use_container_width=True,
            )

    except Exception as exc:
        st.warning(f"Export unavailable: {exc}")

# ── History section ────────────────────────────────────────────────

st.divider()
with st.expander("📜 History", expanded=False):
    try:
        history = api_get("history", params={"limit": 20})
        entries = history.get("entries", [])
        if entries:
            for entry in entries:
                col1, col2 = st.columns([6, 1])
                with col1:
                    title = entry.get("video_title") or entry.get("video_id", "Unknown")
                    st.markdown(f"**{title}** — {entry.get('created_at', '')}")
                with col2:
                    if st.button("🗑️", key=f"del_{entry['id']}"):
                        requests.delete(f"{API_URL}/history/{entry['id']}", timeout=10)
                        st.rerun()
        else:
            st.info("No history yet.")
    except Exception as exc:
        st.warning(f"Could not load history: {exc}")
