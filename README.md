# 📧 Obscuras Mail Campaign Manager

Ein flexibles E-Mail-Kampagnen-Tool für personalisierte Akquise-Mails mit wiederverwendbaren Templates.

---

## 🚀 Schnellstart

```bash
# 1. Umgebungsvariablen setzen
cp .env.example .env
nano .env  # SMTP-Zugangsdaten eintragen
source .env

# 2. Kampagnen anzeigen
python send_campaign.py --list

# 3. Vorschau erstellen
python send_campaign.py kanzleien_mobile --preview

# 4. Test-Mail an sich selbst
python send_campaign.py kanzleien_mobile --test deine@email.de

# 5. Testlauf (ohne Versand)
python send_campaign.py kanzleien_mobile --dry-run

# 6. Kampagne starten (mit Zeitfenster Mo-Fr 9-17 Uhr)
python send_campaign.py kanzleien_mobile --schedule
```

---

## 📁 Projektstruktur

```bash
mail_compaign/
│
├── 📂 campaigns/                    # Alle Kampagnen
│   ├── kanzleien_mobile/
│   │   ├── campaign.yaml            # Anschreiben & Konfiguration
│   │   ├── contacts.csv             # Kontaktliste
│   │   └── preview.html             # Generierte Vorschau
│   │
│   ├── aerzte_website/
│   │   ├── campaign.yaml
│   │   └── contacts.csv
│   │
│   └── immobilien_hausverwaltung/
│       ├── campaign.yaml
│       └── contacts.csv
│
├── 📂 templates/
│   ├── base.html                    # Basis-Template (für alle Kampagnen)
│   ├── template.html                # Legacy-Template
│   └── template.txt                 # Legacy-Plaintext
│
├── 📂 config/
│   ├── sender.yaml                  # Absender-Daten
│   └── settings.py                  # SMTP-Konfiguration
│
├── 📂 logs/                         # Versand-Protokolle
│   ├── <kampagne>.log               # Versand-Log pro Kampagne
│   └── bounces.log                  # Permanente Zustellfehler
│
├── 📂 data/                         # Legacy-Kontakte
│   └── contacts.csv
│
├── send_campaign.py                 # 🎯 Kampagnen-Tool (NEU)
├── send_smtp.py                     # Legacy-Versand
├── .env.example                     # Vorlage für Umgebungsvariablen
├── .gitignore                       # Git-Ausnahmen
└── README.md                        # Diese Datei
```

---

## 🎯 Verwendung

### Alle Kampagnen anzeigen

```bash
python send_campaign.py --list
```

### Vorschau erstellen

Erstellt eine `preview.html` im Kampagnen-Ordner:

```bash
python send_campaign.py <kampagne> --preview
```

### Testlauf (Dry-Run)

Rendert alle E-Mails, ohne sie zu versenden:

```bash
python send_campaign.py <kampagne> --dry-run
```

### Kampagne starten

```bash
python send_campaign.py <kampagne>
```

### Anzahl begrenzen

```bash
python send_campaign.py <kampagne> --limit 10
```

### Test-Mail senden

Sendet eine einzelne Test-Mail an dich selbst (mit `[TEST]`-Prefix im Betreff):

```bash
python send_campaign.py <kampagne> --test sascha@example.com
```

### Zeitfenster aktivieren (Schedule)

Sendet nur Mo–Fr zwischen 9–17 Uhr – unauffälliger und professioneller:

```bash
python send_campaign.py <kampagne> --schedule
```

Mit angepasstem Zeitfenster:

```bash
# Nur Mo-Do, 10-16 Uhr
python send_campaign.py <kampagne> --schedule --schedule-days "1-4" --schedule-hours "10-16"
```

---

## 🚫 Bounce-Handling

### Bounces anzeigen

Zeigt alle permanent fehlgeschlagenen Zustellungen (550–554 Fehler):

```bash
python send_campaign.py --bounces
```

### CSV-Dateien bereinigen

Entfernt gebounced E-Mails aus allen Kampagnen-CSVs:

```bash
# Erst prüfen (Dry-Run)
python send_campaign.py --clean-bounces --dry-run

# Tatsächlich bereinigen (erstellt Backups)
python send_campaign.py --clean-bounces
```

**Features:**

- Bounces werden automatisch in `logs/bounces.log` protokolliert
- Gebounced E-Mails werden beim nächsten Versand automatisch übersprungen
- Mit `--include-bounced` können sie trotzdem erneut versucht werden

---

## ✨ Neue Kampagne erstellen

### 1. Ordner anlegen

```bash
mkdir campaigns/meine_kampagne
```

### 2. campaign.yaml erstellen

```yaml
name: "Meine Kampagne"
subject: "Betreffzeile der E-Mail"
contacts: "contacts.csv"

content:
  greeting: "Sehr geehrte Damen und Herren der <strong style=\"color:#a78bfa;\">{{FIRMA}}</strong>,"
  
  intro: |
    Einleitungstext mit Link zur 
    <a href="{{DOMAIN}}" style="color:#818cf8;">{{DOMAIN}}</a>.
  
  highlight: "{{PROBLEM}}"
  
  body:
    - "Erster Absatz des Haupttexts."
    - "Zweiter Absatz mit <strong style=\"color:#d4d4d8;\">Hervorhebung</strong>."
    - "Dritter Absatz als Abschluss."
  
  cta:
    text: "Jetzt kontaktieren →"
    url: "https://obscuras-media-agency.de/kontakt"

plaintext: |
  Sehr geehrte Damen und Herren der {{FIRMA}},
  
  Hier der Plaintext-Inhalt...
  
  Mit freundlichen Grüßen
  Sascha Gebel
```

### 3. contacts.csv erstellen

```csv
FIRMA,DOMAIN,PROBLEM,EMAIL
Musterfirma GmbH,https://musterfirma.de,"Das spezifische Problem.",kontakt@musterfirma.de
```

### 4. Testen

```bash
python send_campaign.py meine_kampagne --preview
python send_campaign.py meine_kampagne --dry-run
```

---

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
export SMTP_HOST="smtp.deinserver.de"
export SMTP_PORT="465"
export SMTP_USER="mail@obscuras-media-agency.de"
export SMTP_PASS="dein-sicheres-passwort"
```

### Absender-Daten (config/sender.yaml)

```yaml
sender:
  name: "Sascha Gebel"
  title: "Gründer & Entwickler"
  email: "mail@obscuras-media-agency.de"

company:
  name: "Obscuras Media Agency"
  domain: "obscuras-media-agency.de"
  url: "https://obscuras-media-agency.de"

rate_limit:
  delay_seconds: 80  # ~45 Mails/Stunde
```

---

## 📊 Verfügbare Platzhalter

### Globale Platzhalter (automatisch)

| Platzhalter | Beschreibung |
| ----------- | ------------ |
| `{{YEAR}}` | Aktuelles Jahr |
| `{{SENDER_NAME}}` | Name des Absenders |
| `{{SENDER_TITLE}}` | Titel des Absenders |
| `{{COMPANY_NAME}}` | Firmenname |
| `{{COMPANY_URL}}` | Website-URL |

### Kampagnen-spezifische Platzhalter

Definiert durch die Spalten in der `contacts.csv`:

| Kampagne | Platzhalter |
| -------- | ----------- |
| Kanzleien | `{{KANZLEINAME}}`, `{{DOMAIN}}`, `{{PROBLEM}}` |
| Ärzte | `{{PRAXISNAME}}`, `{{DOMAIN}}`, `{{PROBLEM}}` |
| Immobilien | `{{FIRMENNAME}}`, `{{DOMAIN}}`, `{{PROBLEM}}` |

---

## 📝 Logging

Jede Kampagne hat eine eigene Log-Datei unter `logs/<kampagne>.log`:

```text
2026-01-30 20:15:32 | info@kanzlei.de | OK
2026-01-30 20:16:52 | kontakt@firma.de | OK
2026-01-30 20:18:12 | mail@example.de | BOUNCE (550): Mailbox not found
```

Bounces werden zusätzlich in `logs/bounces.log` protokolliert:

```text
2026-01-30 20:18:12 | kanzleien_mobile | mail@example.de | 550 | Mailbox not found
```

- Bereits versendete E-Mails werden **automatisch übersprungen**
- Gebounced E-Mails werden beim nächsten Lauf **nicht erneut versucht**

---

## ⚡ Features

- ✅ **Kampagnen-basiert** – Verschiedene Anschreiben für verschiedene Zielgruppen
- ✅ **YAML-Konfiguration** – Einfach anpassbar ohne Code-Änderungen
- ✅ **HTML + Plaintext** – Multipart-E-Mails für maximale Kompatibilität
- ✅ **Personalisierung** – Beliebige Platzhalter aus CSV
- ✅ **Rate-Limiting** – Schutz vor Spam-Klassifizierung
- ✅ **Auto-Reconnect** – Verbindungsabbrüche werden automatisch behandelt
- ✅ **Duplikat-Schutz** – Keine doppelten E-Mails
- ✅ **Vorschau-Modus** – HTML-Preview vor dem Versand
- ✅ **Dry-Run** – Testlauf ohne echten Versand
- ✅ **Sichere Credentials** – Passwörter nur via Umgebungsvariablen
- ✅ **Test-Mail** – Einzelne Test-Mail an eigene Adresse senden
- ✅ **Zeitfenster (Schedule)** – Nur Mo–Fr 9–17 Uhr senden, unauffälliger
- ✅ **Bounce-Handling** – 550er-Fehler separat loggen & CSV automatisch bereinigen

---

## 🛡️ Sicherheit

- Passwörter werden **niemals** im Code gespeichert
- `.env` ist in `.gitignore` eingetragen
- SMTP-Verbindung erfolgt via **SSL (Port 465)**

---

## 📦 Abhängigkeiten

```bash
pip install pyyaml
```

Python 3.8+ erforderlich.

---

## 📄 Lizenz

Proprietär – Obscuras Media Agency © 2026

---

**Obscuras Media Agency**  
Digitale Softwarelösungen  
[obscuras-media-agency.de](https://obscuras-media-agency.de)
