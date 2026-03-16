<p align="center">
  <img src="assets/logo.png" alt="Mailer Campaigner" width="120" height="120">
</p>

<h1 align="center">Mailer Campaigner</h1>

<p align="center">
  <strong>Professionelles E-Mail-Marketing leicht gemacht</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.3.1-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-GUI-22c55e?style=for-the-badge" alt="PyQt6">
  <img src="https://img.shields.io/badge/Lizenz-Proprietär-f59e0b?style=for-the-badge" alt="Lizenz">
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-schnellstart">Schnellstart</a> •
  <a href="#-dokumentation">Dokumentation</a> •
  <a href="#-lizenz">Lizenz</a>
</p>

---

## Was ist Mailer Campaigner?

**Mailer Campaigner** ist eine professionelle Desktop-Anwendung für personalisiertes E-Mail-Marketing. Mit der intuitiven grafischen Oberfläche verwalten Sie Kampagnen, Kontakte und Templates – ohne technisches Vorwissen.

Ideal für:
- 🏢 **Agenturen** – Kundenakquise mit personalisierten Anschreiben
- 👔 **Freelancer** – Professionelle Kaltakquise per E-Mail
- 🏪 **KMUs** – Newsletter und Angebote an Bestandskunden
- 📊 **Marketing-Teams** – Kampagnen-Management mit Tracking

---

## ✨ Features

### Kampagnen-Management
- 📧 **Unbegrenzte Kampagnen** – Erstellen Sie beliebig viele E-Mail-Kampagnen
- 👥 **Kontaktverwaltung** – CSV-Import, Status-Tracking, Bounce-Handling
- 🎨 **Template-Editor** – Wiederverwendbare Designs mit Live-Vorschau
- 📊 **Dashboard** – Echtzeit-Statistiken und Aktivitäts-Feed

### Personalisierung
- 🔄 **Dynamische Platzhalter** – `{{FIRMA}}`, `{{ANREDE}}`, `{{DOMAIN}}` und mehr
- 🎭 **Jinja2-Templates** – Volle Template-Engine mit Logik und Schleifen
- 📝 **HTML + Plaintext** – Multipart-E-Mails für maximale Kompatibilität

### Sicherheit & Compliance
- 🔐 **Verschlüsselte SMTP-Verbindung** – SSL/TLS auf Port 465 oder 587
- 📋 **Blacklist-Management** – Automatische Bounce-Erkennung
- ⏰ **Zeitfenster-Versand** – Nur Mo–Fr 9–17 Uhr (konfigurierbar)
- 🛡️ **Rate-Limiting** – Schutz vor Spam-Klassifizierung

### Technisch
- 💾 **SQLite-Datenbank** – Lokale Datenhaltung, keine Cloud erforderlich
- 🎯 **Stripe-Integration** – Lizenz-Management für kommerzielle Nutzung
- 🖥️ **Cross-Platform** – Windows, macOS, Linux

---

## 🚀 Installation

### Voraussetzungen

- Python 3.10 oder höher
- pip (Python Package Manager)

### Automatische Installation

```bash
# Repository klonen
git clone https://github.com/obscuras-media-agency/mailer-campaigner.git
cd mailer-campaigner

# Installer ausführen
python install.py
```

Der Installer:
1. Erstellt eine virtuelle Umgebung
2. Installiert alle Abhängigkeiten
3. Initialisiert die Datenbank
4. Erstellt einen Desktop-Shortcut (optional)

### Manuelle Installation

```bash
# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python main.py
```

---

## 🎯 Schnellstart

### 1. Anwendung starten

```bash
python main.py
```

Die GUI öffnet sich mit dem Dashboard.

### 2. SMTP konfigurieren

Navigieren Sie zu **Einstellungen → SMTP** und tragen Sie Ihre Serverdaten ein:

| Feld | Beispiel |
|------|----------|
| Host | `smtp.gmail.com` |
| Port | `465` |
| Benutzer | `ihre@email.de` |
| Passwort | `app-spezifisches-passwort` |

### 3. Erste Kampagne erstellen

1. Klicken Sie auf **Kampagnen → Neue Kampagne**
2. Geben Sie einen Namen und Betreff ein
3. Importieren Sie Kontakte per CSV
4. Wählen Sie ein Template
5. Klicken Sie auf **Vorschau** zum Testen
6. **Kampagne starten** zum Versand

---

## 📖 Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [Installation](docs/INSTALLATION.md) | Detaillierte Installationsanleitung |
| [GUI Setup](docs/GUI_SETUP.md) | PyQt6-Oberfläche konfigurieren |
| [PHP API](docs/PHP_API_SETUP.md) | Lizenz-Server einrichten |

### CLI-Modus

Für Automatisierung steht auch ein Kommandozeilen-Interface bereit:

```bash
# Kampagnen auflisten
python send_campaign.py --list

# Kampagne im Dry-Run testen
python send_campaign.py meine_kampagne --dry-run

# Mit Zeitfenster versenden
python send_campaign.py meine_kampagne --schedule
```

---

## 📁 Projektstruktur

```
mailer_campaigner/
├── main.py                 # Anwendungs-Einstiegspunkt
├── gui/                    # PyQt6-Oberfläche
│   ├── main_window.py      # Hauptfenster
│   ├── pages/              # Seiten (Dashboard, Kontakte, etc.)
│   └── widgets/            # Wiederverwendbare Komponenten
├── models/                 # SQLAlchemy-Datenmodelle
├── utils/                  # Hilfsfunktionen
├── templates/              # E-Mail-Templates (Jinja2)
├── config/                 # Konfigurationsdateien
└── docs/                   # Dokumentation
```

---

## 🔧 Konfiguration

### Absender (config/sender.yaml)

```yaml
sender:
  name: "Max Mustermann"
  title: "Geschäftsführer"
  email: "max@firma.de"

company:
  name: "Musterfirma GmbH"
  url: "https://musterfirma.de"

rate_limit:
  delay_seconds: 60  # 60 Mails/Stunde
```

### Platzhalter

| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{FIRMA}}` | Firmenname aus CSV |
| `{{ANREDE}}` | Persönliche Anrede |
| `{{DOMAIN}}` | Website-Domain |
| `{{SENDER_NAME}}` | Ihr Name |
| `{{YEAR}}` | Aktuelles Jahr |

---

## 🛡️ Sicherheit

- ✅ Passwörter werden **verschlüsselt** in der Datenbank gespeichert
- ✅ SMTP-Verbindungen erfolgen via **SSL/TLS**
- ✅ Keine Datenübertragung an externe Server (außer Lizenzprüfung)
- ✅ Lokale SQLite-Datenbank – Ihre Daten bleiben bei Ihnen

---

## 📄 Lizenz

**Mailer Campaigner** ist proprietäre Software der **Obscuras Media Agency**.

### Lizenzmodelle

| Plan | Preis | Features |
|------|-------|----------|
| **Free** | Kostenlos | 100 E-Mails/Monat, 1 Kampagne |
| **Pro** | 19€/Monat | Unbegrenzt E-Mails, alle Features |
| **Enterprise** | Auf Anfrage | Priority Support, Custom Features |

[Lizenz erwerben →](https://obscuras-media-agency.de/mailer-campaigner)

---

## 🤝 Support

- 📧 E-Mail: [support@obscuras-media-agency.de](mailto:support@obscuras-media-agency.de)
- 🌐 Website: [obscuras-media-agency.de](https://obscuras-media-agency.de)
- 🐛 Issues: [GitHub Issues](https://github.com/obscuras-media-agency/mailer-campaigner/issues)

---

<p align="center">
  <strong>Obscuras Media Agency</strong><br>
  Digitale Softwarelösungen<br>
  © 2026 Alle Rechte vorbehalten
</p>
