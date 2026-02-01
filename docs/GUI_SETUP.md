# 🖥️ Obscuras Campaign Manager - GUI Setup

## Neue PyQt6-basierte Benutzeroberfläche

Diese Dokumentation beschreibt die neue grafische Oberfläche des Campaign Managers.

---

## 🚀 Schnellstart GUI

```bash
# 1. Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. GUI starten
python main.py
```

---

## ✨ Features

### 📊 Dashboard

- Übersicht aller Kampagnen mit Status
- Live-Statistiken (Versendet, Bounce-Rate)
- Letzte Aktivitäten-Log

### 📧 Kampagnen-Manager

- Kampagnen erstellen und bearbeiten
- Zeitplan-Konfiguration (Wochentage, Uhrzeiten)
- Rate-Limiting-Einstellungen
- Start/Pause/Stop-Steuerung

### 👥 Kontakt-Manager

- CSV/Excel-Import mit Feld-Mapping
- Duplikat-Erkennung
- E-Mail-Validierung (optional mit MX-Check)
- Status-Tracking pro Kontakt

### 📝 Template-Editor

- HTML-Editor mit Syntax-Highlighting
- Live-Vorschau (benötigt PyQt6-WebEngine)
- Plaintext-Version für Fallback
- Variablen-Einfügung per Klick

### ⚙️ SMTP-Profile

- Mehrere Absender-Konten verwalten
- Sichere Passwort-Speicherung (Keyring oder verschlüsselt)
- Verbindungstest
- Rate-Limits pro Profil

### 🚫 Blacklist

- Automatische Hard-Bounce-Erkennung
- Manuelle Einträge (E-Mail oder Domain)
- DSGVO-konforme Abmeldungs-Verwaltung
- Import/Export

---

## 📁 Neue Projektstruktur

```bash
mailer_campaigner/
├── main.py                      # GUI-Einstiegspunkt
├── gui/
│   ├── __init__.py
│   ├── main_window.py           # Hauptfenster
│   ├── styles.py                # Dark-Theme CSS
│   ├── widgets/
│   │   └── sidebar.py           # Navigations-Sidebar
│   └── pages/
│       ├── dashboard.py         # Dashboard
│       ├── campaigns.py         # Kampagnen-Verwaltung
│       ├── contacts.py          # Kontakt-Manager
│       ├── templates.py         # Template-Editor
│       ├── smtp_settings.py     # SMTP-Profile
│       └── blacklist.py         # Blacklist
├── models/
│   ├── database.py              # SQLAlchemy Setup
│   ├── campaign.py              # Kampagnen-Model
│   ├── contact.py               # Kontakt-Model
│   ├── smtp_profile.py          # SMTP-Profile
│   ├── send_log.py              # Versand-Log
│   ├── template.py              # Templates
│   └── blacklist.py             # Blacklist
└── utils/
    ├── email_validator.py       # E-Mail-Validierung
    ├── crypto.py                # Verschlüsselung
    └── template_engine.py       # Jinja2 Templates
```

---

## 🎨 Design

Das UI verwendet das Obscuras-Branding:

- **Hintergrund:** `#0a0a0f` (fast schwarz)
- **Cards:** `#18181b` (dunkelgrau)
- **Akzent:** `#6366f1` (Indigo)
- **Gradient:** Indigo → Purple → Pink

---

## 📋 Logging-System

Das integrierte Logging-System bietet umfassende Protokollierung für Entwicklung und Produktion.

### Starten mit Debug-Modus

```bash
python main.py --debug
```

### Log-Dateien

| Datei | Inhalt | Level |
| ----- | ------ | ----- |
| `logs/app.log` | Allgemeine Anwendungslogs | INFO+ |
| `logs/error.log` | Fehler und Warnungen | WARNING+ |
| `logs/debug.log` | Detaillierte Debug-Logs | DEBUG+ |
| `logs/smtp.log` | SMTP-Operationen | DEBUG+ |

### Logging im Code verwenden

```python
from utils.logging_config import get_logger, log_user_action

# Modul-spezifischer Logger
logger = get_logger("gui.meine_seite")

logger.debug("Debug-Information")
logger.info("Normale Information")
logger.warning("Warnung")
logger.error("Fehler aufgetreten")

# Spezielle Logging-Funktionen
log_user_action("Button geklickt", "Details")
```

### Konfiguration

Die Logging-Konfiguration befindet sich in `utils/logging_config.py`:

- **DEBUG_MODE**: Standard-Debug-Modus (True/False)
- **MAX_LOG_SIZE**: Max. Dateigröße (Standard: 5 MB)
- **BACKUP_COUNT**: Anzahl der Backup-Dateien (Standard: 5)

---

## ⌨️ Tastenkürzel

| Kürzel | Aktion |
| ------ | ------ |
| `Ctrl+N` | Neue Kampagne |
| `Ctrl+I` | Kontakte importieren |
| `Ctrl+1-4` | Zwischen Seiten wechseln |
| `F5` | Kampagne starten |
| `F6` | Kampagne pausieren |
| `Ctrl+P` | Vorschau |
| `Ctrl+T` | Test-E-Mail senden |
| `Ctrl+,` | Einstellungen |

---

## 🔧 Technische Details

### Datenbank

- SQLite-Datenbank unter `data/campaigns.db`
- SQLAlchemy ORM für alle Models
- Automatische Migrationen mit Alembic (optional)

### Passwort-Speicherung

- Primär: System-Keyring (sicher)
- Fallback: Fernet-Verschlüsselung (AES-128)

### Template-Engine

- Jinja2 für variable Ersetzung
- Unterstützt `{{VARIABLE}}`-Syntax
- HTML und Plaintext

---

## 🛠️ Entwicklung

### Neue Seite hinzufügen

1. Erstelle `gui/pages/neue_seite.py`
2. Importiere in `gui/main_window.py`
3. Füge zur `self.pages`-Dict hinzu
4. Füge Navigation in `sidebar.py` hinzu

### Neues Model hinzufügen

1. Erstelle `models/neues_model.py`
2. Importiere in `models/database.py` (init_database)
3. Führe DB-Init aus: `python -c "from models.database import init_database; init_database()"`

---

## 📝 Lizenz

© 2025 Obscuras Media Agency
