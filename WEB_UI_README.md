# MarkItDown Web Interface

## 🚀 Schnellstart

### Option 1: Doppelklick auf Batch-Datei (Windows)
1. Doppelklick auf `start_web_ui.bat`
2. Ihr Browser öffnet sich automatisch
3. Fertig! 🎉

### Option 2: Manuell starten
```bash
streamlit run markitdown_web_ui.py
```

Die Anwendung öffnet sich automatisch in Ihrem Browser unter: **http://localhost:8501**

## 📖 Verwendung

1. **Datei hochladen**: Klicken Sie auf "Browse files" oder ziehen Sie eine Datei per Drag & Drop
2. **Konvertieren**: Klicken Sie auf "Zu Markdown konvertieren"
3. **Ergebnis ansehen**:
   - **Vorschau-Tab**: Sehen Sie das formatierte Markdown
   - **Rohtext-Tab**: Sehen Sie den Markdown-Quellcode
4. **Download**: Klicken Sie auf "Markdown herunterladen" um die .md Datei zu speichern

## 🎨 Features

- ✅ Drag & Drop Datei-Upload
- ✅ Live-Vorschau des Markdown
- ✅ Direkter Download der konvertierten Datei
- ✅ Statistiken (Zeichen, Zeilen, Wörter)
- ✅ Unterstützt alle MarkItDown-Dateiformate
- ✅ Plugin-Unterstützung

## 📋 Unterstützte Formate

- **Dokumente**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx, .xls)
- **Bilder**: JPG, PNG, GIF (mit OCR)
- **Audio**: WAV, MP3 (mit Transkription)
- **Web**: HTML, RSS
- **Daten**: CSV, JSON, XML
- **Andere**: ZIP, EPUB, Outlook MSG

## ⚙️ Optionen

### Plugins verwenden
Aktivieren Sie die Checkbox "Plugins verwenden" in der Sidebar, um 3rd-party Plugins zu nutzen.

### Data URIs behalten
Aktivieren Sie "Data URIs behalten", um base64-codierte Bilder im Markdown beizubehalten.

## 🛑 Anwendung beenden

- Im Browser: Schließen Sie einfach den Tab
- Server stoppen: Drücken Sie `CTRL+C` im Terminal/Kommandozeilenfenster

## 🔧 Technische Details

- **Framework**: Streamlit
- **Backend**: MarkItDown (Microsoft AutoGen)
- **Python**: 3.10+

## 📝 Hinweise

- Die Anwendung läuft **lokal** auf Ihrem Computer
- Keine Dateien werden ins Internet hochgeladen
- Alle Konvertierungen erfolgen offline

## 🆘 Probleme?

Falls die Anwendung nicht startet:

1. Überprüfen Sie, ob Python installiert ist: `python --version`
2. Überprüfen Sie, ob Streamlit installiert ist: `pip list | grep streamlit`
3. Installieren Sie Streamlit: `pip install streamlit`
4. Installieren Sie MarkItDown: `pip install -e 'packages/markitdown[all]'`

## 📞 Support

Bei Fragen oder Problemen besuchen Sie: https://github.com/microsoft/markitdown
