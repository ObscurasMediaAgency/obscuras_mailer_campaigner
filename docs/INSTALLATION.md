# 📦 Obscuras Campaign Manager - Installationsanleitung

## Schnellstart

```bash
# Installation starten
python install.py
```

Das war's! Der Installer kümmert sich um alles weitere.

---

## Systemvoraussetzungen

| Komponente | Minimum | Empfohlen |
| ---------- | ------- | --------- |
| Python | 3.10 | 3.11+ |
| RAM | 2 GB | 4 GB |
| Speicher | 500 MB | 1 GB |
| OS | Linux, Windows 10, macOS 10.15 | Linux (Ubuntu 22.04+), Windows 11, macOS 12+ |

### Linux (Debian/Ubuntu)

```bash
# Python und venv installieren
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Optional: Qt6-Abhängigkeiten (falls GUI-Probleme auftreten)
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon0
```

### Windows

1. Python 3.10+ von [python.org](https://www.python.org/downloads/) installieren
2. Bei Installation "Add Python to PATH" aktivieren
3. Visual C++ Redistributable installieren (falls nicht vorhanden)

### macOS

```bash
# Mit Homebrew
brew install python@3.11

# Oder von python.org herunterladen
```

---

## Installationsoptionen

### Normale Installation

```bash
python install.py
```

Dieser Befehl:

- ✅ Prüft Systemvoraussetzungen
- ✅ Erstellt Virtual Environment
- ✅ Installiert alle Abhängigkeiten
- ✅ Erstellt Launcher-Skript
- ✅ Erstellt Desktop-Eintrag
- ✅ Initialisiert Datenbank

### Nur Systemprüfung

```bash
python install.py --check
```

Prüft nur, ob alle Voraussetzungen erfüllt sind, ohne etwas zu installieren.

### Installation ohne Desktop-Eintrag

```bash
python install.py --no-desktop
```

### Entwickler-Installation

```bash
python install.py --dev
```

Installiert zusätzlich:

- pytest (Testing)
- black (Code-Formatierung)
- mypy (Typ-Prüfung)
- pylint (Linting)
- pre-commit (Git Hooks)

### Reparatur-Installation

```bash
python install.py --repair
```

Löscht das Virtual Environment und erstellt es neu. Nützlich bei:

- Beschädigten Dependencies
- Python-Version-Wechsel
- Unerklärlichen Fehlern

---

## Updates

### Update mit automatischem Backup

```bash
python install.py --update
```

Dieser Befehl:

1. Erstellt Backup von: `config/`, `campaigns/`, `data/`, `templates/`, Datenbank
2. Aktualisiert alle Dependencies
3. Führt Datenbank-Migrationen durch (falls vorhanden)

**Backups werden gespeichert unter:** `backups/backup_YYYYMMDD_HHMMSS/`

### Manuelles Update

```bash
# Virtual Environment aktivieren
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# Dependencies aktualisieren
pip install --upgrade -r requirements.txt
```

---

## Deinstallation

```bash
python install.py --uninstall
```

Der Deinstaller fragt nach:

- **Benutzerdaten behalten?** (Kampagnen, Kontakte, Datenbank)

Was entfernt wird:

- Virtual Environment (`.venv/`)
- Desktop-Eintrag
- Launcher-Skripte

Was optional behalten wird:

- `campaigns/` - Ihre Kampagnen
- `config/` - Ihre Konfiguration
- `data/` - Ihre Kontaktlisten
- `campaign_manager.db` - Datenbank

---

## Anwendung starten

### Linux / macOS

```bash
./start.sh
```

Oder über das Anwendungsmenü.

### Windows Desktop-Verknüpfung

Doppelklick auf `start.bat` oder Desktop-Verknüpfung.

### Manuell (alle Systeme)

```bash
# Virtual Environment aktivieren
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# Anwendung starten
python main.py

# Mit Debug-Modus
python main.py --debug
```

---

## Fehlerbehebung

### "venv-Modul nicht gefunden"

**Linux (Debian/Ubuntu):**

```bash
sudo apt install python3-venv
```

**Andere Distributionen:**

```bash
pip install virtualenv
```

### "Qt-Platform-Plugin nicht gefunden" (Linux)

```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon0 libegl1
```

Oder als Workaround:

```bash
export QT_QPA_PLATFORM=xcb
./start.sh
```

### "pip: Befehl nicht gefunden"

```bash
python -m ensurepip --upgrade
```

### Netzwerkprobleme bei Installation

Falls keine Internetverbindung verfügbar:

1. Auf einem anderen Rechner Dependencies herunterladen:

   ```bash
   pip download -r requirements.txt -d ./offline_packages
   ```

2. `offline_packages/` auf den Zielrechner kopieren

3. Offline installieren:

   ```bash
   pip install --no-index --find-links=./offline_packages -r requirements.txt
   ```

### Datenbank-Fehler

```bash
# Datenbank reparieren (Backup vorher erstellen!)
python install.py --repair
```

### Komplette Neuinstallation

```bash
python install.py --uninstall
python install.py
```

---

## Verzeichnisstruktur nach Installation

```bash
obscuras-campaign-manager/
├── .venv/                    # Virtual Environment
├── start.sh / start.bat      # Launcher-Skript
├── install.py                # Installer
├── main.py                   # Hauptanwendung
├── config/                   # Konfiguration
│   ├── sender.yaml           # Absender-Daten
│   └── settings.py           # SMTP-Einstellungen
├── campaigns/                # Ihre Kampagnen
├── data/                     # Kontaktdaten
├── backups/                  # Update-Backups
└── campaign_manager.db       # SQLite-Datenbank
```

---

## Umgebungsvariablen (optional)

| Variable | Beschreibung | Standard |
| -------- | ------------ | -------- |
| `OCM_DEBUG` | Debug-Modus aktivieren | `0` |
| `OCM_DB_PATH` | Pfad zur Datenbank | `./campaign_manager.db` |
| `OCM_LOG_LEVEL` | Log-Level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

---

## Kommandozeilen-Referenz

```bash
python install.py [OPTIONEN]

Optionen:
  --update, -u      Update mit Backup durchführen
  --uninstall       Anwendung deinstallieren
  --repair, -r      Reparatur-Installation (venv neu erstellen)
  --check, -c       Nur Systemvoraussetzungen prüfen
  --no-desktop      Keine Desktop-Integration erstellen
  --dev, -d         Entwickler-Abhängigkeiten installieren
  --quiet, -q       Weniger Ausgaben
  --help, -h        Hilfe anzeigen
```

---

## Support

Bei Problemen:

1. `python install.py --check` ausführen
2. Fehlermeldung notieren
3. Issue erstellen oder Support kontaktieren

---

### Letzte Aktualisierung: März 2026
