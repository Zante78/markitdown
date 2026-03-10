# MarkItDown — Projektdokumentation

> **Fork mit Streamlit Web UI & verbesserter YouTube-Transkript-Extraktion**

| | |
|---|---|
| **Version** | 0.1.5 |
| **Datum** | 2026-03-10 |
| **Upstream** | [microsoft/markitdown](https://github.com/microsoft/markitdown) |
| **Lizenz** | MIT (Microsoft Corporation) |

---

## Inhaltsverzeichnis

1. [Projektuebersicht](#1-projektuebersicht)
2. [Architektur](#2-architektur)
3. [Installation & Setup](#3-installation--setup)
4. [Nutzung](#4-nutzung)
5. [YouTube-Feature (JSON3)](#5-youtube-feature-json3)
6. [Unterstuetzte Formate](#6-unterstuetzte-formate)
7. [Konfiguration](#7-konfiguration)
8. [Projektstruktur](#8-projektstruktur)
9. [Technische Details](#9-technische-details)
10. [Troubleshooting](#10-troubleshooting)
11. [Entwicklung](#11-entwicklung)
12. [Lizenz & Credits](#12-lizenz--credits)

---

## 1. Projektuebersicht

### Was ist MarkItDown?

[MarkItDown](https://github.com/microsoft/markitdown) ist ein Open-Source-Tool von **Microsoft** (MIT-Lizenz), das ueber 20 Dateiformate in Markdown konvertiert — von PDF und Word ueber Excel und PowerPoint bis hin zu HTML, YouTube-Videos, Bildern und Audio. Es ist als Python-Bibliothek, CLI-Tool und MCP-Server verfuegbar.

### Warum dieser Fork?

Dieser Fork erweitert das Original um drei Funktionen:

| Feature | Beschreibung |
|---------|-------------|
| **Streamlit Web UI** | Browser-basierte Oberflaeche mit Drag & Drop, Live-Vorschau und Download — komplett auf Deutsch |
| **YouTube JSON3-Transkripte** | Saubere Transkript-Extraktion via `yt-dlp` im JSON3-Format statt des fehleranfaelligen VTT-Formats |
| **Deutsche Oberflaeche** | Alle UI-Elemente, Fehlermeldungen und Statusanzeigen in Deutsch |

### Was wurde NICHT veraendert

Der gesamte MarkItDown-Core bleibt **unberuehrt**:

- Alle 18+ Built-in Converter (PDF, DOCX, PPTX, XLSX, HTML, etc.)
- CLI-Interface (`markitdown` Befehl)
- Python API (`from markitdown import MarkItDown`)
- MCP-Server (Model Context Protocol fuer LLM-Integration)
- Plugin-System (Entry Points)
- Test-Suite

### Fork-Dateien vs Original

| Datei | Typ | Beschreibung |
|-------|-----|-------------|
| `markitdown_web_ui.py` | **[FORK]** Neu | Streamlit Web UI (334 Zeilen) |
| `start_web_ui.bat` | **[FORK]** Neu | Windows-Startskript |
| `WEB_UI_README.md` | **[FORK]** Neu | Web UI Kurzanleitung (Deutsch) |
| `PROJEKTDOKUMENTATION.md` | **[FORK]** Neu | Diese Dokumentation |
| `packages/markitdown/` | Original | Core-Bibliothek (unveraendert) |
| `packages/markitdown-mcp/` | Original | MCP-Server (unveraendert) |
| `packages/markitdown-sample-plugin/` | Original | Plugin-Beispiel (unveraendert) |

---

## 2. Architektur

### Systemuebersicht

```
                         +---------------------------+
                         |        Browser            |
                         |   http://localhost:8501    |
                         +------------+--------------+
                                      |
                              Streamlit WebSocket
                                      |
                         +------------+--------------+
                         |   markitdown_web_ui.py    |
                         |       [FORK]              |
                         |                           |
                         |  +-----+  +-----------+  |
                         |  | Tab |  |   Tab     |  |
                         |  |Datei|  |   URL     |  |
                         |  +--+--+  +-----+-----+  |
                         +-----|-----------|--------+
                               |           |
                    +----------+    +------+------+
                    |               |             |
               Temp-File      YouTube?       Andere URL
                    |           |                 |
                    v           v                 v
            +-------+----+ +---+-------+  +------+-----+
            | MarkItDown | | yt-dlp    |  | MarkItDown |
            | .convert() | | JSON3     |  |.convert_url|
            +------+-----+ +---+-------+  +------+-----+
                   |            |                 |
                   v            v                 v
         +--------+------------+-----------------+------+
         |              Converter Pipeline               |
         |                                               |
         |  accepts() -> convert() -> Markdown-Output    |
         |                                               |
         |  PlainText | HTML | PDF | DOCX | PPTX | XLSX |
         |  YouTube | Wikipedia | RSS | Bing | Image ... |
         +-----------------------------------------------+
```

### Monorepo-Struktur (3 Packages)

Das Repository ist als Python-Monorepo organisiert:

| Package | Pfad | Zweck |
|---------|------|-------|
| **markitdown** | `packages/markitdown/` | Core-Bibliothek mit allen Convertern |
| **markitdown-mcp** | `packages/markitdown-mcp/` | MCP-Server fuer Claude Desktop & LLMs |
| **markitdown-sample-plugin** | `packages/markitdown-sample-plugin/` | Beispiel-Plugin (RTF-Converter) |

### Converter-Pattern

Jeder Converter implementiert zwei Methoden:

```python
class DocumentConverter:
    def accepts(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs) -> bool:
        """Prueft ob dieser Converter die Datei verarbeiten kann"""

    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs) -> DocumentConverterResult:
        """Konvertiert die Datei zu Markdown"""
```

**Priority-System:** Converter werden nach Prioritaet sortiert (niedrigere Werte zuerst):

| Prioritaet | Konstante | Verwendung |
|-----------|-----------|-----------|
| `0.0` | `PRIORITY_SPECIFIC_FILE_FORMAT` | Spezifische Formate (.docx, .pdf, YouTube, etc.) |
| `10.0` | `PRIORITY_GENERIC_FILE_FORMAT` | Generische Formate (PlainText, HTML, ZIP) |

Ablauf: Fuer jede Datei werden alle Converter der Reihe nach gefragt (`accepts()`). Der erste, der akzeptiert und erfolgreich konvertiert, gewinnt.

### Web UI: Session State & Tabs

Die Streamlit-App nutzt `st.session_state` fuer persistente Daten zwischen Interaktionen:

- **Tab "Datei hochladen"**: Upload → Temp-File → `MarkItDown.convert()` → Session State
- **Tab "URL konvertieren"**: URL-Eingabe → YouTube-Erkennung → yt-dlp ODER `convert_url()` → Session State
- **Ausgabe**: Vorschau (gerendertes Markdown) + Rohtext (Quellcode) + Download-Button + Statistiken

---

## 3. Installation & Setup

### Voraussetzungen

| Anforderung | Version | Pruefung |
|-------------|---------|----------|
| Python | 3.10+ | `python --version` |
| pip | aktuell | `pip --version` |
| Git | beliebig | `git --version` |
| yt-dlp | aktuell | `pip install yt-dlp` (fuer YouTube) |

### Schritt-fuer-Schritt Installation

**1. Repository klonen**

```bash
git clone https://github.com/Zante78/markitdown.git
cd markitdown
```

**2. Virtuelle Umgebung erstellen**

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Core-Bibliothek installieren (mit allen optionalen Dependencies)**

```bash
pip install -e "packages/markitdown[all]"
```

Oder nur mit bestimmten Formaten (spart Speicher):

```bash
# Nur PDF + Word
pip install -e "packages/markitdown[pdf,docx]"
```

**4. Web UI Dependencies installieren**

```bash
pip install streamlit yt-dlp
```

**5. Installation verifizieren**

```bash
# Core pruefen
python -c "from markitdown import MarkItDown; print('Core OK')"

# CLI pruefen
markitdown --help

# Streamlit pruefen
streamlit --version
```

**6. Web UI starten**

Windows (Doppelklick):
```
start_web_ui.bat
```

Oder manuell:
```bash
streamlit run markitdown_web_ui.py
```

Die App oeffnet sich automatisch unter **http://localhost:8501**.

### Optionale Dependencies

| Feature-Gruppe | Pakete | Format |
|---------------|--------|--------|
| `pdf` | pdfminer.six, pdfplumber | PDF-Dateien |
| `docx` | mammoth, lxml | Word-Dokumente |
| `pptx` | python-pptx | PowerPoint |
| `xlsx` | pandas, openpyxl | Excel (modern) |
| `xls` | pandas, xlrd | Excel (legacy) |
| `outlook` | olefile | Outlook MSG |
| `audio-transcription` | pydub, SpeechRecognition | Audio-Dateien |
| `youtube-transcription` | youtube-transcript-api | YouTube (Core-Methode) |
| `az-doc-intel` | azure-ai-documentintelligence, azure-identity | Azure Document Intelligence |
| `all` | Alle obigen | Alles installieren |

---

## 4. Nutzung

### 4.1 Web UI (Hauptfokus)

#### Tab: Datei hochladen

1. **Datei waehlen**: Drag & Drop oder "Browse files" klicken
2. **Datei-Info**: Name, Groesse und Typ werden angezeigt
3. **Konvertieren**: Button "Zu Markdown konvertieren" klicken
4. **Ergebnis ansehen**:
   - **Vorschau**: Gerendertes Markdown mit Formatierung
   - **Rohtext**: Markdown-Quellcode mit Zeilennummern
5. **Download**: "Markdown herunterladen" speichert die `.md`-Datei
6. **Statistiken**: Zeichen, Zeilen und Woerter werden angezeigt

#### Tab: URL konvertieren

1. **URL eingeben**: YouTube-Link, Webseite, RSS-Feed etc.
2. **Konvertieren**: Button klicken
3. YouTube-URLs werden automatisch erkannt und mit `yt-dlp` verarbeitet (Metadaten + Transkript)
4. Alle anderen URLs werden ueber `MarkItDown.convert_url()` verarbeitet
5. Ergebnis, Download und Statistiken wie bei Datei-Upload

#### Sidebar-Optionen

| Option | Standard | Beschreibung |
|--------|---------|-------------|
| Plugins verwenden | Aus | 3rd-party Converter-Plugins aktivieren |
| Data URIs behalten | Aus | Base64-codierte Bilder im Output behalten |

### 4.2 CLI

Die wichtigsten Befehle:

```bash
# Datei konvertieren
markitdown dokument.pdf

# Ausgabe in Datei speichern
markitdown dokument.pdf -o ausgabe.md

# Von Stdin lesen
cat dokument.pdf | markitdown

# URL konvertieren
markitdown https://example.com/seite.html
```

### 4.3 Python API

```python
from markitdown import MarkItDown

md = MarkItDown()

# Lokale Datei
result = md.convert("dokument.pdf")
print(result.text_content)

# URL
result = md.convert("https://example.com")
print(result.text_content)

# Mit optionalen Features
md = MarkItDown(enable_plugins=True)
result = md.convert("praesentation.pptx")
```

---

## 5. YouTube-Feature (JSON3)

### Das Problem: VTT-Format

Das Standard-VTT-Untertitelformat (WebVTT) liefert bei YouTube-Videos **ueberlappende Cues**. Jeder Untertitelblock wiederholt einen Teil des vorherigen Textes, was bei langen Videos zu **80-90% Duplikaten** fuehrt:

```
00:00:01.000 --> 00:00:04.000
Willkommen zu diesem Video

00:00:02.500 --> 00:00:06.000
zu diesem Video ueber Python     <-- "zu diesem Video" ist Duplikat

00:00:05.000 --> 00:00:09.000
ueber Python Programmierung      <-- "ueber Python" ist Duplikat
```

Der Core-YouTubeConverter nutzt `youtube-transcript-api`, das diese Probleme hat und bei Rate-Limits unzuverlaessig ist.

### Die Loesung: JSON3 via yt-dlp

Die Web UI verwendet stattdessen `yt-dlp` mit dem **JSON3-Format**. Dieses Format liefert strukturierte, ueberlappungsfreie Segmente:

```json
{
  "events": [
    {
      "tStartMs": 1000,
      "segs": [
        { "utf8": "Willkommen " },
        { "utf8": "zu diesem Video" }
      ]
    },
    {
      "tStartMs": 5000,
      "segs": [
        { "utf8": "ueber Python " },
        { "utf8": "Programmierung" }
      ]
    }
  ]
}
```

### Verarbeitungslogik

Die Web UI verarbeitet JSON3 in diesen Schritten:

1. **yt-dlp Konfiguration**: Untertitel im JSON3-Format fuer `de` und `en` anfordern

```python
sub_opts = {
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['de', 'en'],
    'subtitlesformat': 'json3',
    'socket_timeout': 120,
    'retries': 3,
}
```

2. **Segmente zusammenfuegen**: Alle `segs[].utf8`-Werte eines Events werden konkateniert
3. **Leere Segmente filtern**: Leere Strings und reine Newlines werden uebersprungen
4. **Timestamps formatieren**: `tStartMs` wird zu `[H:MM:SS]` konvertiert
5. **Deduplizierung**: Gleiche Timestamps werden ohne erneuten Zeitstempel angehaengt

```python
start_ms = event.get('tStartMs', 0)
total_secs = start_ms // 1000
mins, secs = divmod(total_secs, 60)
hours, mins = divmod(mins, 60)
timestamp = f"[{hours}:{mins:02d}:{secs:02d}]"
```

### Ausgabeformat

```markdown
# YouTube

## Videotitel

### Video Metadata
- **Autor:** Channel-Name
- **Views:** 1,234,567
- **Dauer:** 15:30
- **Upload:** 2025-01-15
- **Tags:** python, tutorial, programmierung

### Description
Vollstaendige Video-Beschreibung...

### Transcript (2,500 Woerter)
[0:00:01] Willkommen zu diesem Video [0:00:05] ueber Python Programmierung
[0:00:10] Heute werden wir lernen...
```

### Vergleich: Vorher vs Nachher

| | VTT (Core) | JSON3 (Fork) |
|---|---|---|
| **Quelle** | youtube-transcript-api | yt-dlp |
| **Format** | Ueberlappende Cues | Strukturierte Events |
| **Duplikate** | 80-90% bei langen Videos | Keine |
| **Timestamps** | Keine in Ausgabe | `[H:MM:SS]` pro Segment |
| **Sprachen** | Eine (mit Fallback) | Deutsch + Englisch Fallback |
| **Rate-Limiting** | Haeufig | Seltener (yt-dlp Retries) |
| **Metadaten** | Titel, Views, Keywords | Titel, Autor, Views, Dauer, Upload, Tags, Beschreibung |

---

## 6. Unterstuetzte Formate

| Format | Erweiterungen | Optionale Dependencies | Hinweise |
|--------|--------------|----------------------|----------|
| PDF | `.pdf` | `pdfminer.six`, `pdfplumber` | Text-Extraktion, Tabellen |
| Word | `.docx` | `mammoth`, `lxml` | Formatierung bleibt erhalten |
| PowerPoint | `.pptx` | `python-pptx` | Folien als Markdown-Sektionen |
| Excel (modern) | `.xlsx` | `pandas`, `openpyxl` | Tabellen als Markdown-Tables |
| Excel (legacy) | `.xls` | `pandas`, `xlrd` | Aeltere Excel-Dateien |
| CSV | `.csv` | `pandas` | Komma-separierte Daten |
| HTML | `.html`, `.htm` | — (Core) | Webseiten zu Markdown |
| Plain Text | `.txt` | — (Core) | Durchgereicht |
| RSS/Atom | — | — (Core) | Feed-Titel und Eintraege |
| Wikipedia | — | — (Core) | Artikel-Extraktion |
| YouTube | — | `youtube-transcript-api` (Core) / `yt-dlp` (Web UI) | Video-Metadaten + Transkript |
| Bing SERP | — | — (Core) | Suchergebnisse |
| Bilder | `.jpg`, `.png`, `.gif`, `.bmp`, `.tiff` | — (Core, `magika`) | EXIF-Metadaten, LLM-Beschreibung moeglich |
| Audio | `.wav`, `.mp3` | `pydub`, `SpeechRecognition` | Speech-to-Text Transkription |
| Outlook | `.msg` | `olefile` | E-Mail zu Markdown |
| EPUB | `.epub` | — (Core) | E-Books |
| Jupyter | `.ipynb` | — (Core) | Notebooks mit Code + Output |
| ZIP | `.zip` | — (Core) | Rekursive Konvertierung aller Dateien |
| Azure Doc Intel | Diverse | `azure-ai-documentintelligence` | Cloud-basierte Dokumentanalyse |

---

## 7. Konfiguration

### Web UI Sidebar

Die Streamlit-App bietet zwei Konfigurations-Optionen in der Sidebar:

- **Plugins verwenden** (`enable_plugins`): Aktiviert 3rd-party Converter-Plugins, die via Python Entry Points registriert sind. Standard: Aus.
- **Data URIs behalten** (`keep_data_uris`): Behalt Base64-codierte Bilder im Markdown-Output. Standard: Aus.

### yt-dlp Einstellungen (YouTube)

Die Web UI konfiguriert yt-dlp mit diesen Parametern:

| Parameter | Wert | Zweck |
|-----------|------|-------|
| `subtitleslangs` | `['de', 'en']` | Bevorzugte Transkript-Sprachen |
| `subtitlesformat` | `json3` | Strukturiertes Untertitelformat |
| `writeautomaticsub` | `True` | Automatisch generierte Untertitel nutzen |
| `socket_timeout` | `120` | Timeout fuer Netzwerkanfragen (Sekunden) |
| `retries` | `3` | Anzahl Wiederholungsversuche |
| `nocheckcertificate` | `True` | SSL-Zertifikats-Pruefung ueberspringen |

### Plugin-System

Plugins werden ueber Python Entry Points registriert. In der `pyproject.toml` des Plugins:

```toml
[project.entry-points."markitdown.plugin"]
mein_plugin = "mein_paket:register_converters"
```

Die `register_converters`-Funktion erhaelt die MarkItDown-Instanz:

```python
def register_converters(markitdown, **kwargs):
    markitdown.register_converter(MeinConverter(), priority=5.0)
```

Ein Beispiel-Plugin (RTF-Converter) findet sich in `packages/markitdown-sample-plugin/`.

---

## 8. Projektstruktur

```
markitdown/
├── markitdown_web_ui.py              [FORK] Streamlit Web UI (334 Zeilen)
├── start_web_ui.bat                  [FORK] Windows-Startskript
├── WEB_UI_README.md                  [FORK] Web UI Kurzanleitung
├── PROJEKTDOKUMENTATION.md           [FORK] Diese Dokumentation
│
├── packages/
│   ├── markitdown/                   Core-Bibliothek
│   │   ├── pyproject.toml            Dependencies & Build-Konfiguration
│   │   ├── README.md                 Upstream-Dokumentation
│   │   ├── src/markitdown/
│   │   │   ├── __init__.py           Public API Exports
│   │   │   ├── __about__.py          Version (0.1.5)
│   │   │   ├── __main__.py           CLI Entry Point
│   │   │   ├── _markitdown.py        Haupt-Orchestrator (784 Zeilen)
│   │   │   ├── _base_converter.py    Abstrakte Basis-Klasse
│   │   │   ├── _stream_info.py       StreamInfo Dataclass
│   │   │   ├── _uri_utils.py         URI-Parsing Utilities
│   │   │   ├── _exceptions.py        Exception-Klassen
│   │   │   │
│   │   │   ├── converters/           18+ Converter-Implementierungen
│   │   │   │   ├── __init__.py       Exportiert alle Converter
│   │   │   │   ├── _youtube_converter.py    YouTube (Metadaten + Transkript)
│   │   │   │   ├── _pdf_converter.py        PDF-Extraktion
│   │   │   │   ├── _docx_converter.py       Word-Dokumente
│   │   │   │   ├── _pptx_converter.py       PowerPoint
│   │   │   │   ├── _xlsx_converter.py       Excel (modern)
│   │   │   │   ├── _xls_converter.py        Excel (legacy)
│   │   │   │   ├── _html_converter.py       HTML/Webseiten
│   │   │   │   ├── _plain_text_converter.py Plain Text
│   │   │   │   ├── _rss_converter.py        RSS/Atom Feeds
│   │   │   │   ├── _wikipedia_converter.py  Wikipedia-Artikel
│   │   │   │   ├── _image_converter.py      Bilder (EXIF)
│   │   │   │   ├── _audio_converter.py      Audio (Speech-to-Text)
│   │   │   │   ├── _csv_converter.py        CSV-Dateien
│   │   │   │   ├── _epub_converter.py       E-Books
│   │   │   │   ├── _zip_converter.py        ZIP-Archive
│   │   │   │   ├── _ipynb_converter.py      Jupyter Notebooks
│   │   │   │   ├── _outlook_msg_converter.py  Outlook-Mails
│   │   │   │   ├── _bing_serp_converter.py  Bing-Suchergebnisse
│   │   │   │   └── _doc_intel_converter.py  Azure Document Intelligence
│   │   │   │
│   │   │   └── converter_utils/      Shared Utilities
│   │   │       └── docx/             Word-spezifische Helfer (OMML/LaTeX)
│   │   │
│   │   └── tests/                    Test-Suite
│   │       ├── test_*.py             20+ Test-Dateien
│   │       └── test_files/           Test-Fixtures + Expected Outputs
│   │
│   ├── markitdown-mcp/              MCP-Server
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/markitdown_mcp/
│   │       ├── __init__.py
│   │       ├── __main__.py          MCP Server Entry Point
│   │       └── __about__.py
│   │
│   └── markitdown-sample-plugin/    Beispiel-Plugin (RTF)
│       ├── pyproject.toml           Entry Point Konfiguration
│       ├── README.md
│       └── src/markitdown_sample_plugin/
│           ├── __init__.py
│           └── _plugin.py           RtfConverter Implementierung
│
├── .github/
│   └── workflows/
│       ├── tests.yml                CI: Automatisierte Tests
│       ├── pre-commit.yml           CI: Linting & Formatierung
│       └── dependabot.yml           Dependency-Updates
│
├── README.md                        Upstream-Projekt-README
├── LICENSE                          MIT License
├── Dockerfile                       Container-Build
├── .pre-commit-config.yaml          Pre-Commit Hooks
└── .gitignore
```

---

## 9. Technische Details

### Core Dependencies

Diese Pakete werden immer installiert:

| Paket | Version | Zweck |
|-------|---------|-------|
| beautifulsoup4 | latest | HTML-Parsing |
| requests | latest | HTTP-Client |
| markdownify | latest | HTML → Markdown Konvertierung |
| magika | ~0.6.1 | Dateityp-Erkennung (Google) |
| charset-normalizer | latest | Zeichensatz-Erkennung |
| defusedxml | latest | Sichere XML-Verarbeitung |

### Web UI Dependencies

| Paket | Zweck |
|-------|-------|
| streamlit | Web-Framework fuer die Oberflaeche |
| yt-dlp | YouTube-Video-Download & Transkript-Extraktion |

### Build-System

| Eigenschaft | Wert |
|------------|------|
| Build-Tool | Hatchling |
| Python-Version | >= 3.10 |
| Unterstuetzte Versionen | 3.10, 3.11, 3.12, 3.13 (CPython + PyPy) |
| Versionierung | `packages/markitdown/src/markitdown/__about__.py` |
| CLI Entry Point | `markitdown = "markitdown.__main__:main"` |
| Plugin Entry Point | `markitdown.plugin` (Gruppe) |

### Oeffentliche API

```python
from markitdown import (
    MarkItDown,                     # Haupt-Klasse
    DocumentConverter,              # Basis-Klasse fuer eigene Converter
    DocumentConverterResult,        # Rueckgabe-Typ
    StreamInfo,                     # Metadaten-Container
    PRIORITY_SPECIFIC_FILE_FORMAT,  # Prioritaet 0.0
    PRIORITY_GENERIC_FILE_FORMAT,   # Prioritaet 10.0
)
```

---

## 10. Troubleshooting

### Problem 1: ModuleNotFoundError: No module named 'markitdown'

**Ursache:** Core-Paket nicht installiert oder falsche virtuelle Umgebung.

**Loesung:**
```bash
# Virtuelle Umgebung aktivieren
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Core installieren
pip install -e "packages/markitdown[all]"
```

### Problem 2: YouTube-Transkript wird nicht geladen

**Ursache:** Rate-Limiting durch YouTube oder kein Transkript verfuegbar.

**Loesung:**
- Einige Minuten warten und erneut versuchen
- Pruefen ob das Video Untertitel hat (auf YouTube direkt schauen)
- `yt-dlp` aktualisieren: `pip install -U yt-dlp`

### Problem 3: SSL-Zertifikatsfehler

**Ursache:** Firmen-Proxy oder veraltete Zertifikate.

**Loesung:** Die Web UI deaktiviert SSL-Pruefung bereits fuer URL-Konvertierungen. Fuer CLI:
```bash
markitdown --no-verify https://example.com
```

### Problem 4: Encoding-Fehler (UnicodeDecodeError)

**Ursache:** Datei hat unerwartete Zeichenkodierung.

**Loesung:** MarkItDown nutzt `charset-normalizer` fuer automatische Erkennung. Falls das fehlschlaegt:
```bash
# Datei-Encoding pruefen
python -c "import charset_normalizer; print(charset_normalizer.from_path('datei.txt').best())"
```

### Problem 5: Port 8501 ist bereits belegt

**Ursache:** Eine andere Streamlit-Instanz laeuft bereits.

**Loesung:**
```bash
# Anderen Port verwenden
streamlit run markitdown_web_ui.py --server.port 8502

# Oder bestehende Instanz beenden
# Windows:
taskkill /F /IM streamlit.exe
# Linux:
pkill -f streamlit
```

### Problem 6: PDF-Konvertierung liefert leeren Output

**Ursache:** PDF enthaelt nur Bilder (gescanntes Dokument), keinen Text.

**Loesung:** Azure Document Intelligence verwenden (OCR-faehig) oder externes OCR-Tool vorschalten.

### Problem 7: PPTX/DOCX-Konvertierung schlaegt fehl

**Ursache:** Optionale Dependencies nicht installiert.

**Loesung:**
```bash
pip install -e "packages/markitdown[pptx,docx]"
```

### Problem 8: Web UI zeigt "MarkItDown ist nicht installiert"

**Ursache:** Streamlit laeuft in einer anderen Python-Umgebung als die Installation.

**Loesung:**
```bash
# Pruefen welches Python Streamlit nutzt
streamlit --version
which python  # oder: where python (Windows)

# Sicherstellen dass beide in derselben venv sind
pip install -e "packages/markitdown[all]"
pip install streamlit yt-dlp
```

---

## 11. Entwicklung

### Upstream-Sync Workflow

So holen Sie Aenderungen vom Original-Repository:

```bash
# 1. Upstream als Remote hinzufuegen (einmalig)
git remote add upstream https://github.com/microsoft/markitdown.git

# 2. Upstream-Aenderungen holen
git fetch upstream

# 3. In den main-Branch wechseln
git checkout main

# 4. Upstream mergen
git merge upstream/main

# 5. Konflikte loesen (falls vorhanden) und pushen
git push origin main
```

### Fork-Strategie: Konfliktfreie Merges

Alle Fork-spezifischen Dateien befinden sich **im Root-Verzeichnis**:

- `markitdown_web_ui.py`
- `start_web_ui.bat`
- `WEB_UI_README.md`
- `PROJEKTDOKUMENTATION.md`

Da Microsoft diese Dateien nicht hat, entstehen beim Upstream-Sync **keine Merge-Konflikte**. Der gesamte `packages/`-Ordner bleibt unberuehrt.

### Tests ausfuehren

```bash
# Alle Tests (via Hatch)
cd packages/markitdown
hatch test

# Einzelnen Test
hatch test -- tests/test_pdf.py -v

# Type-Checking
hatch run types:check
```

### Pre-Commit Hooks

```bash
# Hooks installieren
pip install pre-commit
pre-commit install

# Manuell ausfuehren
pre-commit run --all-files
```

### Eigenen Converter erstellen

1. Neue Datei in `packages/markitdown/src/markitdown/converters/` anlegen
2. `DocumentConverter` implementieren (`accepts()` + `convert()`)
3. In `converters/__init__.py` exportieren
4. In `_markitdown.py` → `enable_builtins()` registrieren

Oder als Plugin (empfohlen fuer Fork-Erweiterungen):

```python
# mein_converter.py
from markitdown import DocumentConverter, DocumentConverterResult, StreamInfo

class MeinConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info, **kwargs):
        return (stream_info.extension or "").lower() == ".meinformat"

    def convert(self, file_stream, stream_info, **kwargs):
        content = file_stream.read().decode("utf-8")
        return DocumentConverterResult(markdown=f"# Konvertiert\n\n{content}")
```

---

## 12. Lizenz & Credits

### Lizenz

Dieses Projekt steht unter der **MIT License**.

```
MIT License

Copyright (c) Microsoft Corporation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

### Credits

| Beitrag | Verantwortlich |
|---------|---------------|
| **MarkItDown Core** | Microsoft Corporation / Adam Fourney |
| **Web UI, YouTube JSON3, Dokumentation** | [Zante78](https://github.com/Zante78) |

### Links

- **Upstream:** https://github.com/microsoft/markitdown
- **Dieser Fork:** https://github.com/Zante78/markitdown
- **Issues:** https://github.com/Zante78/markitdown/issues
- **PyPI:** https://pypi.org/project/markitdown/

---

*Erstellt: 2026-03-10 · Version 0.1.5 · Sprache: Deutsch*
