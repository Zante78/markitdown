"""
MarkItDown Web UI - Browser-basierte Benutzeroberfläche für MarkItDown
Starten Sie mit: streamlit run markitdown_web_ui.py
"""

import streamlit as st
import tempfile
import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs

try:
    from markitdown import MarkItDown
except ImportError:
    st.error("MarkItDown ist nicht installiert. Bitte führen Sie aus: pip install -e 'packages/markitdown[all]'")
    st.stop()

# Seitenkonfiguration
st.set_page_config(
    page_title="MarkItDown Converter",
    page_icon="📄",
    layout="wide"
)

# Header
st.title("📄 MarkItDown Converter")
st.markdown("Konvertieren Sie verschiedene Dateiformate zu Markdown")

# Sidebar mit Informationen
with st.sidebar:
    st.header("ℹ️ Unterstützte Formate")
    st.markdown("""
    - **Dokumente**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx, .xls)
    - **Bilder**: JPG, PNG, GIF (mit OCR)
    - **Audio**: WAV, MP3 (mit Transkription)
    - **Web**: HTML, RSS, **YouTube URLs**
    - **Daten**: CSV, JSON, XML
    - **Andere**: ZIP, EPUB, Outlook MSG
    """)

    st.header("⚙️ Optionen")
    use_plugins = st.checkbox("Plugins verwenden", value=False, help="3rd-party Plugins aktivieren")
    keep_data_uris = st.checkbox("Data URIs behalten", value=False, help="Base64-codierte Bilder im Output behalten")

# Hauptbereich
tab_file, tab_url = st.tabs(["📁 Datei hochladen", "🔗 URL konvertieren"])

with tab_file:
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Wählen Sie eine Datei zum Konvertieren",
            type=None,  # Alle Dateitypen erlauben
            help="Laden Sie eine unterstützte Datei hoch"
        )

        if uploaded_file is not None:
            st.success(f"Datei geladen: {uploaded_file.name}")
            file_details = {
                "Dateiname": uploaded_file.name,
                "Dateigröße": f"{uploaded_file.size / 1024:.2f} KB",
                "Dateityp": uploaded_file.type if uploaded_file.type else "Unbekannt"
            }
            st.json(file_details)

            if st.button("Zu Markdown konvertieren", type="primary", use_container_width=True, key="btn_file"):
                with st.spinner("Konvertiere Datei..."):
                    try:
                        md = MarkItDown(enable_plugins=use_plugins)

                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name

                        try:
                            result = md.convert(tmp_file_path)
                            st.session_state['markdown_content'] = result.text_content
                            st.session_state['original_filename'] = uploaded_file.name
                            st.success("Konvertierung erfolgreich!")
                        finally:
                            os.unlink(tmp_file_path)

                    except Exception as e:
                        st.error(f"Fehler bei der Konvertierung: {str(e)}")
                        st.exception(e)

    with col2:
        st.subheader("Markdown-Ausgabe")

        if 'markdown_content' in st.session_state:
            markdown_content = st.session_state['markdown_content']
            original_filename = st.session_state.get('original_filename', 'output')

            view_tab1, view_tab2 = st.tabs(["Vorschau", "Rohtext"])
            with view_tab1:
                st.markdown(markdown_content)
            with view_tab2:
                st.code(markdown_content, language="markdown", line_numbers=True)

            output_filename = Path(original_filename).stem + ".md"
            st.download_button(
                label="Markdown herunterladen",
                data=markdown_content,
                file_name=output_filename,
                mime="text/markdown",
                use_container_width=True,
                key="dl_file"
            )

            st.divider()
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Zeichen", len(markdown_content))
            with col_b:
                st.metric("Zeilen", len(markdown_content.splitlines()))
            with col_c:
                st.metric("Wörter", len(markdown_content.split()))
        else:
            st.info("Laden Sie eine Datei hoch und klicken Sie auf 'Konvertieren'.")

with tab_url:
    col_url1, col_url2 = st.columns([1, 1])

    with col_url1:
        url_input = st.text_input(
            "URL eingeben",
            placeholder="https://www.youtube.com/watch?v=... oder beliebige Webseite",
            help="YouTube-URLs, Webseiten, RSS-Feeds etc."
        )

        st.caption("Unterstützt: YouTube, Webseiten, RSS-Feeds und andere URLs")

        if url_input and st.button("URL zu Markdown konvertieren", type="primary", use_container_width=True, key="btn_url"):
            url_stripped = url_input.strip()
            if not url_stripped.startswith(("http://", "https://")):
                st.error("Bitte eine gültige URL eingeben (muss mit http:// oder https:// beginnen).")
            else:
                with st.spinner("Konvertiere URL..."):
                    try:
                        requests.packages.urllib3.disable_warnings()

                        # YouTube-URL erkennen
                        parsed = urlparse(url_stripped)
                        is_youtube = parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com")
                        video_id = None

                        if is_youtube and "v" in parse_qs(parsed.query):
                            video_id = parse_qs(parsed.query)["v"][0]
                        elif parsed.hostname == "youtu.be":
                            video_id = parsed.path.lstrip("/")
                            is_youtube = True

                        if is_youtube and video_id:
                            # YouTube via yt-dlp verarbeiten
                            import yt_dlp
                            import shutil

                            tmpdir = tempfile.mkdtemp()
                            webpage_text = "# YouTube\n"

                            try:
                                # Schritt 1: Metadaten holen
                                st.info("Lade Video-Metadaten...")
                                meta_opts = {
                                    'skip_download': True,
                                    'nocheckcertificate': True,
                                    'quiet': True,
                                    'no_warnings': True,
                                    'socket_timeout': 60,
                                }
                                with yt_dlp.YoutubeDL(meta_opts) as ydl:
                                    info = ydl.extract_info(url_stripped, download=False)

                                title = info.get('title', '')
                                author = info.get('channel', info.get('uploader', 'Unbekannt'))
                                duration = info.get('duration', 0)
                                view_count = info.get('view_count', 0)
                                description = info.get('description', '')
                                upload_date = info.get('upload_date', '')
                                tags = info.get('tags', [])

                                if title:
                                    webpage_text += f"\n## {title}\n"
                                webpage_text += f"\n### Video Metadata\n"
                                webpage_text += f"- **Autor:** {author}\n"
                                if view_count:
                                    webpage_text += f"- **Views:** {view_count:,}\n"
                                if duration:
                                    hours, remainder = divmod(duration, 3600)
                                    mins, secs = divmod(remainder, 60)
                                    if hours > 0:
                                        webpage_text += f"- **Dauer:** {hours}h {mins:02d}m {secs:02d}s\n"
                                    else:
                                        webpage_text += f"- **Dauer:** {mins}:{secs:02d}\n"
                                if upload_date:
                                    webpage_text += f"- **Upload:** {upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}\n"
                                if tags:
                                    webpage_text += f"- **Tags:** {', '.join(tags[:10])}\n"
                                if description:
                                    webpage_text += f"\n### Description\n{description}\n"

                                # Schritt 2: Untertitel separat holen (fehlertolerant)
                                duration_info = f" ({hours}h {mins}m)" if duration and duration > 3600 else ""
                                st.info(f"Lade Transkript{duration_info}... Das kann bei langen Videos etwas dauern.")
                                transcript_text = ""
                                try:
                                    sub_opts = {
                                        'skip_download': True,
                                        'writesubtitles': True,
                                        'writeautomaticsub': True,
                                        'subtitleslangs': ['de', 'en'],
                                        'subtitlesformat': 'json3',
                                        'nocheckcertificate': True,
                                        'quiet': True,
                                        'no_warnings': True,
                                        'socket_timeout': 120,
                                        'retries': 3,
                                        'ignoreerrors': True,
                                        'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
                                    }
                                    with yt_dlp.YoutubeDL(sub_opts) as ydl:
                                        ydl.extract_info(url_stripped, download=True)

                                    for lang in ['de', 'en']:
                                        for fname in os.listdir(tmpdir):
                                            if f'.{lang}.' in fname and fname.endswith('.json3') and os.path.getsize(os.path.join(tmpdir, fname)) > 0:
                                                with open(os.path.join(tmpdir, fname), 'r', encoding='utf-8') as fh:
                                                    data = json.load(fh)
                                                events = data.get('events', [])
                                                transcript_parts = []
                                                last_timestamp = ""
                                                for event in events:
                                                    segs = event.get('segs', [])
                                                    if not segs:
                                                        continue
                                                    seg_text = ''.join(seg.get('utf8', '') for seg in segs).strip()
                                                    if not seg_text or seg_text == '\n':
                                                        continue
                                                    start_ms = event.get('tStartMs', 0)
                                                    total_secs = start_ms // 1000
                                                    mins, secs = divmod(total_secs, 60)
                                                    hours, mins = divmod(mins, 60)
                                                    timestamp = f"[{hours}:{mins:02d}:{secs:02d}]"
                                                    if timestamp != last_timestamp:
                                                        transcript_parts.append(f"\n{timestamp} {seg_text}")
                                                        last_timestamp = timestamp
                                                    else:
                                                        transcript_parts.append(seg_text)
                                                transcript_text = ' '.join(transcript_parts)
                                                break
                                        if transcript_text:
                                            break
                                except Exception:
                                    pass

                                if transcript_text:
                                    word_count = len(transcript_text.split())
                                    webpage_text += f"\n### Transcript ({word_count:,} Woerter)\n{transcript_text}\n"
                                else:
                                    webpage_text += "\n### Transcript\n*Transkript konnte nicht geladen werden (Rate-Limit oder nicht verfuegbar).*\n"

                            finally:
                                shutil.rmtree(tmpdir, ignore_errors=True)

                            st.session_state['url_markdown_content'] = webpage_text
                            st.session_state['url_source'] = url_stripped
                            st.success("YouTube-Video erfolgreich konvertiert!")

                        else:
                            # Alle anderen URLs via MarkItDown
                            md = MarkItDown(enable_plugins=use_plugins)
                            md._requests_session.verify = False

                            result = md.convert_url(url_stripped)
                            st.session_state['url_markdown_content'] = result.text_content
                            st.session_state['url_source'] = url_stripped
                            st.success("Konvertierung erfolgreich!")

                    except Exception as e:
                        st.error(f"Fehler bei der Konvertierung: {str(e)}")
                        st.exception(e)

    with col_url2:
        st.subheader("Markdown-Ausgabe")

        if 'url_markdown_content' in st.session_state:
            url_markdown = st.session_state['url_markdown_content']
            url_source = st.session_state.get('url_source', 'url-output')

            url_view1, url_view2 = st.tabs(["Vorschau", "Rohtext"])
            with url_view1:
                st.markdown(url_markdown)
            with url_view2:
                st.code(url_markdown, language="markdown", line_numbers=True)

            # Dateiname aus URL ableiten
            parsed_dl = urlparse(url_source)
            if parsed_dl.hostname and "youtube" in parsed_dl.hostname:
                vid = parse_qs(parsed_dl.query).get("v", ["video"])[0]
                url_filename = f"youtube_{vid}.md"
            else:
                url_filename = parsed_dl.netloc.replace(".", "_") + ".md"
            st.download_button(
                label="Markdown herunterladen",
                data=url_markdown,
                file_name=url_filename,
                mime="text/markdown",
                use_container_width=True,
                key="dl_url"
            )

            st.divider()
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                st.metric("Zeichen", len(url_markdown))
            with col_u2:
                st.metric("Zeilen", len(url_markdown.splitlines()))
            with col_u3:
                st.metric("Wörter", len(url_markdown.split()))
        else:
            st.info("Geben Sie eine URL ein und klicken Sie auf 'Konvertieren'.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    Powered by <a href='https://github.com/microsoft/markitdown' target='_blank'>MarkItDown</a>
    | Microsoft AutoGen Team
</div>
""", unsafe_allow_html=True)
