#!/usr/bin/env python3
"""
Obscuras Media Agency – Kampagnen-basiertes E-Mail-Tool
Versendet personalisierte E-Mails basierend auf Kampagnen-Konfiguration.

Usage:
    python send_campaign.py <kampagnen-ordner>
    python send_campaign.py kanzleien_mobile
    python send_campaign.py aerzte_website --dry-run
"""

import argparse
import csv
import os
import re
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

import yaml

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
SENDER_CONFIG = BASE_DIR / "config" / "sender.yaml"
BOUNCE_LOG = LOGS_DIR / "bounces.log"

MAX_RETRIES = 3
RETRY_DELAY = 10

# Bounce-Error-Codes (permanente Zustellfehler)
BOUNCE_CODES = {
    "550": "Mailbox not found",
    "551": "User not local",
    "552": "Mailbox full",
    "553": "Invalid mailbox name",
    "554": "Transaction failed",
}


# ═══════════════════════════════════════════════════════════════════
# SCHEDULE / TIMING
# ═══════════════════════════════════════════════════════════════════
class ScheduleChecker:
    """Prüft, ob E-Mails im erlaubten Zeitfenster gesendet werden dürfen."""
    
    def __init__(self, days: str = "1-5", hours: str = "9-17"):
        """
        Initialisiert den Schedule-Checker.
        
        Args:
            days: Wochentage (1=Mo, 7=So), z.B. "1-5" für Mo-Fr
            hours: Stundenbereich, z.B. "9-17" für 9-17 Uhr
        """
        self.allowed_days = self._parse_range(days, 1, 7)
        self.allowed_hours = self._parse_range(hours, 0, 23)
    
    def _parse_range(self, range_str: str, min_val: int, max_val: int) -> Set[int]:
        """Parst einen Bereich wie '1-5' oder '9,10,11' in ein Set."""
        result: Set[int] = set()
        
        for part in range_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                for i in range(int(start), int(end) + 1):
                    if min_val <= i <= max_val:
                        result.add(i)
            else:
                val = int(part)
                if min_val <= val <= max_val:
                    result.add(val)
        
        return result
    
    def is_allowed_now(self) -> Tuple[bool, str]:
        """
        Prüft, ob jetzt gesendet werden darf.
        
        Returns:
            Tuple[bool, str]: (erlaubt, Grund)
        """
        now = datetime.now()
        weekday = now.isoweekday()  # 1=Mo, 7=So
        hour = now.hour
        
        if weekday not in self.allowed_days:
            day_names = {1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr", 6: "Sa", 7: "So"}
            allowed_days_str = ", ".join(day_names[d] for d in sorted(self.allowed_days))
            return False, f"Heute ist {day_names[weekday]}, erlaubt: {allowed_days_str}"
        
        if hour not in self.allowed_hours:
            return False, f"Aktuelle Stunde: {hour}:00, erlaubt: {min(self.allowed_hours)}-{max(self.allowed_hours)} Uhr"
        
        return True, "OK"
    
    def wait_until_allowed(self) -> None:
        """Wartet, bis das Senden wieder erlaubt ist."""
        while True:
            allowed, reason = self.is_allowed_now()
            if allowed:
                return
            
            print(f"\n⏰ Außerhalb des Zeitfensters: {reason}")
            print("   Warte 5 Minuten...\n")
            time.sleep(300)  # 5 Minuten warten


# ═══════════════════════════════════════════════════════════════════
# BOUNCE HANDLING
# ═══════════════════════════════════════════════════════════════════
def is_bounce_error(error: Exception) -> Tuple[bool, str]:
    """
    Prüft, ob ein SMTP-Fehler ein permanenter Bounce ist.
    
    Returns:
        Tuple[bool, str]: (ist_bounce, error_code)
    """
    error_str = str(error)
    
    for code in BOUNCE_CODES:
        if code in error_str:
            return True, code
    
    return False, ""


def log_bounce(email: str, error_code: str, error_message: str, campaign_name: str):
    """Protokolliert einen Bounce in der separaten Bounce-Log-Datei."""
    BOUNCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(BOUNCE_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {campaign_name} | {email} | {error_code} | {error_message}\n")


def get_bounced_emails() -> Set[str]:
    """Lädt alle E-Mail-Adressen aus dem Bounce-Log."""
    if not BOUNCE_LOG.exists():
        return set()
    
    bounced: Set[str] = set()
    for line in BOUNCE_LOG.read_text(encoding="utf-8").splitlines():
        parts = line.split(" | ")
        if len(parts) >= 3:
            bounced.add(parts[2].strip())
    
    return bounced


def clean_bounces_from_csv(contacts_file: Path, dry_run: bool = True) -> int:
    """
    Entfernt gebounced E-Mails aus einer CSV-Datei.
    
    Args:
        contacts_file: Pfad zur CSV-Datei
        dry_run: Wenn True, nur simulieren
    
    Returns:
        Anzahl der entfernten E-Mails
    """
    bounced = get_bounced_emails()
    
    if not bounced:
        return 0
    
    # CSV laden
    with open(contacts_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        contacts = list(reader)
    
    # Bounced filtern
    clean_contacts = [c for c in contacts if c.get("EMAIL") not in bounced]
    removed_count = len(contacts) - len(clean_contacts)
    
    if removed_count > 0 and not dry_run:
        # Backup erstellen
        backup_file = contacts_file.with_suffix(".csv.backup")
        contacts_file.rename(backup_file)
        
        # Bereinigte CSV schreiben
        with open(contacts_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(clean_contacts)
    
    return removed_count


# ═══════════════════════════════════════════════════════════════════
# HELPER CLASSES
# ═══════════════════════════════════════════════════════════════════
class Campaign:
    """Repräsentiert eine E-Mail-Kampagne."""
    
    def __init__(self, campaign_path: Path):
        self.path = campaign_path
        self.config_file = campaign_path / "campaign.yaml"
        
        if not self.config_file.exists():
            raise FileNotFoundError(f"Kampagnen-Konfiguration nicht gefunden: {self.config_file}")
        
        with open(self.config_file, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        self.name = self.config.get("name", campaign_path.name)
        self.subject = self.config.get("subject", "Nachricht von Obscuras Media Agency")
        self.contacts_file = campaign_path / self.config.get("contacts", "contacts.csv")
        self.log_file = LOGS_DIR / f"{campaign_path.name}.log"
    
    def get_contacts(self) -> List[Dict[str, str]]:
        """Lädt die Kontakte aus der CSV-Datei."""
        if not self.contacts_file.exists():
            raise FileNotFoundError(f"Kontaktdatei nicht gefunden: {self.contacts_file}")
        
        with open(self.contacts_file, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    
    def get_content(self) -> Dict[str, Any]:
        """Gibt den Anschreiben-Inhalt zurück."""
        return self.config.get("content", {})
    
    def get_plaintext(self) -> str:
        """Gibt die Plaintext-Version zurück."""
        return self.config.get("plaintext", "")


class TemplateRenderer:
    """Rendert E-Mail-Templates mit Kampagnen- und Kontaktdaten."""
    
    def __init__(self, sender_config: Dict[str, Any]):
        self.sender = sender_config
        self.base_template = self._load_base_template()
    
    def _load_base_template(self) -> str:
        """Lädt das Basis-Template."""
        template_path = TEMPLATES_DIR / "base.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Basis-Template nicht gefunden: {template_path}")
        return template_path.read_text(encoding="utf-8")
    
    def render_html(self, campaign: Campaign, contact: Dict[str, str]) -> str:
        """Rendert das HTML für einen Kontakt."""
        content = campaign.get_content()
        html = self.base_template
        
        # Globale Variablen
        replacements: Dict[str, str] = {
            "{{YEAR}}": str(datetime.now().year),
            "{{EMAIL_SUBJECT}}": campaign.subject,
            "{{SENDER_NAME}}": self.sender["sender"]["name"],
            "{{SENDER_TITLE}}": self.sender["sender"]["title"],
            "{{COMPANY_NAME}}": self.sender["company"]["name"],
            "{{COMPANY_DOMAIN}}": self.sender["company"]["domain"],
            "{{COMPANY_URL}}": self.sender["company"]["url"],
        }
        
        # Content-Variablen
        replacements["{{CONTENT_GREETING}}"] = content.get("greeting", "")
        replacements["{{CONTENT_INTRO}}"] = content.get("intro", "")
        replacements["{{CONTENT_HIGHLIGHT}}"] = content.get("highlight", "")
        replacements["{{CONTENT_CTA_TEXT}}"] = content.get("cta", {}).get("text", "Kontakt aufnehmen")
        replacements["{{CONTENT_CTA_URL}}"] = content.get("cta", {}).get("url", self.sender["company"]["url"])
        
        # Body-Paragraphen rendern
        body_paragraphs = content.get("body", [])
        body_html = "\n".join([
            f'<p style="margin:0 0 20px;color:#a1a1aa;font-size:15px;line-height:1.8;">{p}</p>'
            for p in body_paragraphs
        ])
        replacements["{{CONTENT_BODY}}"] = body_html
        
        # Ersetzungen durchführen
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, value)
        
        # Kontakt-spezifische Variablen
        for key, value in contact.items():
            html = html.replace(f"{{{{{key}}}}}", value)
        
        return html
    
    def render_plaintext(self, campaign: Campaign, contact: Dict[str, str]) -> str:
        """Rendert den Plaintext für einen Kontakt."""
        text = campaign.get_plaintext()
        
        # Kontakt-spezifische Variablen
        for key, value in contact.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        
        return text


class EmailSender:
    """Versendet E-Mails über SMTP."""
    
    def __init__(self, sender_config: Dict[str, Any]):
        self.config = sender_config
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.delay = sender_config.get("rate_limit", {}).get("delay_seconds", 80)
        
        self._validate_config()
        self.connection = None
    
    def _validate_config(self):
        """Prüft die SMTP-Konfiguration."""
        missing: List[str] = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.smtp_user:
            missing.append("SMTP_USER")
        if not self.smtp_pass:
            missing.append("SMTP_PASS")
        
        if missing:
            raise EnvironmentError(
                f"⚠️  Fehlende Umgebungsvariablen: {', '.join(missing)}\n"
                f"   Bitte setzen: source .env"
            )
    
    def connect(self):
        """Stellt eine SMTP-Verbindung her."""
        assert self.smtp_host is not None and self.smtp_user is not None and self.smtp_pass is not None
        self.connection = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30)
        self.connection.login(self.smtp_user, self.smtp_pass)
    
    def disconnect(self):
        """Trennt die SMTP-Verbindung."""
        if self.connection:
            try:
                self.connection.quit()
            except:
                pass
            self.connection = None
    
    def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Sendet eine E-Mail mit Retry-Logik."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.config['sender']['name']} <{self.config['sender']['email']}>"
        msg["To"] = to_email
        msg["X-Mailer"] = "Obscuras Campaign Manager"
        
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not self.connection:
                    self.connect()
                assert self.connection is not None
                self.connection.send_message(msg)
                return True
            except smtplib.SMTPServerDisconnected:
                print(f"  ↻ Verbindung verloren, reconnect... ({attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
                self.connect()
            except smtplib.SMTPException as e:
                if attempt == MAX_RETRIES:
                    raise e
                print(f"  ↻ SMTP-Fehler, retry... ({attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
        
        return False


# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════
def load_sent_emails(log_file: Path) -> Set[str]:
    """Lädt bereits versendete E-Mails."""
    if not log_file.exists():
        return set()
    
    sent: Set[str] = set()
    for line in log_file.read_text(encoding="utf-8").splitlines():
        if " | " in line and " | OK" in line:
            parts = line.split(" | ")
            if len(parts) >= 2:
                sent.add(parts[1].strip())
    return sent


def log_result(log_file: Path, email: str, status: str):
    """Protokolliert das Versandergebnis."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {email} | {status}\n")


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════
def list_campaigns():
    """Listet alle verfügbaren Kampagnen."""
    print("\n📂 Verfügbare Kampagnen:\n")
    
    if not CAMPAIGNS_DIR.exists():
        print("   Keine Kampagnen gefunden.")
        return
    
    for campaign_dir in sorted(CAMPAIGNS_DIR.iterdir()):
        if campaign_dir.is_dir() and (campaign_dir / "campaign.yaml").exists():
            try:
                campaign = Campaign(campaign_dir)
                contacts = campaign.get_contacts()
                print(f"   • {campaign_dir.name}")
                print(f"     {campaign.name}")
                print(f"     {len(contacts)} Kontakte")
                print()
            except Exception as e:
                print(f"   • {campaign_dir.name} (Fehler: {e})")
                print()


def run_campaign(
    campaign_name: str,
    dry_run: bool = False,
    limit: Optional[int] = None,
    schedule: Optional[ScheduleChecker] = None,
    skip_bounced: bool = True
):
    """Führt eine Kampagne aus."""
    campaign_path = CAMPAIGNS_DIR / campaign_name
    
    if not campaign_path.exists():
        print(f"\n❌ Kampagne nicht gefunden: {campaign_name}")
        list_campaigns()
        sys.exit(1)
    
    # Konfiguration laden
    campaign = Campaign(campaign_path)
    
    with open(SENDER_CONFIG, encoding="utf-8") as f:
        sender_config = yaml.safe_load(f)
    
    print("\n" + "═" * 60)
    print(f"  KAMPAGNE: {campaign.name}")
    print("═" * 60)
    
    if dry_run:
        print("\n🔍 DRY-RUN MODUS – Keine E-Mails werden versendet!\n")
    
    if schedule:
        allowed, reason = schedule.is_allowed_now()
        if not allowed:
            print(f"\n⏰ Schedule aktiv: {reason}")
            print("   Warte auf erlaubtes Zeitfenster...\n")
            schedule.wait_until_allowed()
    
    # Kontakte und bereits versendete laden
    contacts = campaign.get_contacts()
    sent_emails = load_sent_emails(campaign.log_file)
    bounced_emails: Set[str] = get_bounced_emails() if skip_bounced else set()
    
    pending = [
        c for c in contacts 
        if c["EMAIL"] not in sent_emails and c["EMAIL"] not in bounced_emails
    ]
    
    if limit:
        pending = pending[:limit]
    
    print(f"\n📋 Kontakte: {len(contacts)} gesamt, {len(sent_emails)} bereits versendet")
    if bounced_emails:
        print(f"🚫 Übersprungen (Bounce): {len([c for c in contacts if c['EMAIL'] in bounced_emails])}")
    print(f"📨 Ausstehend: {len(pending)}\n")
    
    if not pending:
        print("✅ Alle E-Mails wurden bereits versendet!")
        return
    
    # Renderer und Sender initialisieren
    renderer = TemplateRenderer(sender_config)
    sender: Optional[EmailSender] = None
    
    if not dry_run:
        sender = EmailSender(sender_config)
        print(f"🔌 Verbinde mit SMTP-Server...")
        sender.connect()
        print("✅ Verbunden!\n")
    
    success_count = 0
    error_count = 0
    
    try:
        for i, contact in enumerate(pending, 1):
            email = contact["EMAIL"]
            
            # Ersten Kontakt-Wert als Bezeichner nehmen
            identifier = list(contact.values())[0] if contact else "Unbekannt"
            
            print(f"[{i}/{len(pending)}] {identifier}")
            print(f"         → {email}")
            
            # Templates rendern
            html_body = renderer.render_html(campaign, contact)
            text_body = renderer.render_plaintext(campaign, contact)
            
            if dry_run:
                print("         📝 Template gerendert (Dry-Run)")
                success_count += 1
            else:
                assert sender is not None
                try:
                    sender.send(email, campaign.subject, html_body, text_body)
                    log_result(campaign.log_file, email, "OK")
                    success_count += 1
                    print("         ✅ Gesendet!")
                except Exception as e:
                    # Bounce-Handling
                    is_bounce, bounce_code = is_bounce_error(e)
                    if is_bounce:
                        log_bounce(email, bounce_code, str(e), campaign_name)
                        log_result(campaign.log_file, email, f"BOUNCE ({bounce_code}): {e}")
                        print(f"         🚫 Bounce ({bounce_code}): {BOUNCE_CODES.get(bounce_code, 'Unbekannt')}")
                    else:
                        log_result(campaign.log_file, email, f"ERROR: {e}")
                        print(f"         ❌ Fehler: {e}")
                    error_count += 1
            
            print()
            
            # Schedule-Check vor nächster Mail
            if schedule and not dry_run and i < len(pending):
                allowed, reason = schedule.is_allowed_now()
                if not allowed:
                    print(f"\n⏰ Zeitfenster beendet: {reason}")
                    print("   Warte auf nächstes Fenster...\n")
                    schedule.wait_until_allowed()
            
            # Delay (außer bei letzter Mail oder Dry-Run)
            if not dry_run and sender is not None and i < len(pending):
                print(f"         ⏳ Warte {sender.delay}s...")
                time.sleep(sender.delay)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer!")
    
    finally:
        if not dry_run and sender is not None:
            sender.disconnect()
        
        print("\n" + "═" * 60)
        print(f"  FERTIG: {success_count} {'gerendert' if dry_run else 'gesendet'}, {error_count} Fehler")
        print("═" * 60 + "\n")


def send_test_email(campaign_name: str, test_email: str):
    """Sendet eine Test-Mail an eine einzelne Adresse."""
    campaign_path = CAMPAIGNS_DIR / campaign_name
    
    if not campaign_path.exists():
        print(f"\n❌ Kampagne nicht gefunden: {campaign_name}")
        sys.exit(1)
    
    # E-Mail-Format validieren
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", test_email):
        print(f"\n❌ Ungültige E-Mail-Adresse: {test_email}")
        sys.exit(1)
    
    campaign = Campaign(campaign_path)
    
    with open(SENDER_CONFIG, encoding="utf-8") as f:
        sender_config = yaml.safe_load(f)
    
    contacts = campaign.get_contacts()
    if not contacts:
        print("\n❌ Keine Kontakte in der Kampagne für Template-Daten!")
        sys.exit(1)
    
    print("\n" + "═" * 60)
    print(f"  TEST-MAIL: {campaign.name}")
    print("═" * 60)
    print(f"\n📧 Sende Test-Mail an: {test_email}")
    
    # Ersten Kontakt als Template-Daten verwenden, aber Test-E-Mail als Empfänger
    test_contact = contacts[0].copy()
    test_contact["EMAIL"] = test_email
    
    renderer = TemplateRenderer(sender_config)
    html_body = renderer.render_html(campaign, test_contact)
    text_body = renderer.render_plaintext(campaign, test_contact)
    
    sender = EmailSender(sender_config)
    
    try:
        print("🔌 Verbinde mit SMTP-Server...")
        sender.connect()
        print("✅ Verbunden!")
        
        sender.send(test_email, f"[TEST] {campaign.subject}", html_body, text_body)
        print(f"\n✅ Test-Mail erfolgreich gesendet an {test_email}!")
        print("   Prüfe deinen Posteingang (auch Spam-Ordner).\n")
        
    except Exception as e:
        print(f"\n❌ Fehler beim Senden: {e}\n")
        sys.exit(1)
    
    finally:
        sender.disconnect()


def preview_campaign(campaign_name: str):
    """Zeigt eine Vorschau der ersten E-Mail."""
    campaign_path = CAMPAIGNS_DIR / campaign_name
    
    if not campaign_path.exists():
        print(f"\n❌ Kampagne nicht gefunden: {campaign_name}")
        sys.exit(1)
    
    campaign = Campaign(campaign_path)
    
    with open(SENDER_CONFIG, encoding="utf-8") as f:
        sender_config = yaml.safe_load(f)
    
    contacts = campaign.get_contacts()
    if not contacts:
        print("\n❌ Keine Kontakte in der Kampagne!")
        sys.exit(1)
    
    renderer = TemplateRenderer(sender_config)
    html = renderer.render_html(campaign, contacts[0])
    
    # HTML in Datei speichern für Vorschau
    preview_file = campaign_path / "preview.html"
    preview_file.write_text(html, encoding="utf-8")
    
    print(f"\n✅ Vorschau erstellt: {preview_file}")
    print(f"   Öffne in Browser: file://{preview_file.absolute()}\n")


def show_bounces():
    """Zeigt alle geloggten Bounces an."""
    print("\n" + "═" * 60)
    print("  BOUNCE-LOG")
    print("═" * 60 + "\n")
    
    if not BOUNCE_LOG.exists():
        print("   Keine Bounces protokolliert.\n")
        return
    
    bounces = BOUNCE_LOG.read_text(encoding="utf-8").splitlines()
    
    if not bounces:
        print("   Keine Bounces protokolliert.\n")
        return
    
    print(f"   {len(bounces)} Bounce(s) gefunden:\n")
    
    for line in bounces:
        parts = line.split(" | ")
        if len(parts) >= 4:
            timestamp, campaign, email, code = parts[:4]
            reason = BOUNCE_CODES.get(code, "Unbekannt")
            print(f"   • {email}")
            print(f"     {timestamp} | {campaign} | {code}: {reason}")
            print()


def clean_bounces(campaign_name: Optional[str] = None, dry_run: bool = True):
    """Bereinigt CSV-Dateien von gebouncten E-Mails."""
    bounced = get_bounced_emails()
    
    if not bounced:
        print("\n✅ Keine Bounces zum Bereinigen.\n")
        return
    
    print("\n" + "═" * 60)
    print("  CSV-BEREINIGUNG")
    print("═" * 60 + "\n")
    
    if dry_run:
        print("🔍 DRY-RUN MODUS – Keine Dateien werden geändert!\n")
    
    print(f"🚫 {len(bounced)} gebounced E-Mail(s) gefunden:\n")
    for email in sorted(bounced):
        print(f"   • {email}")
    print()
    
    # Kampagnen durchsuchen
    if campaign_name:
        campaign_dirs = [CAMPAIGNS_DIR / campaign_name]
    else:
        campaign_dirs = [d for d in CAMPAIGNS_DIR.iterdir() if d.is_dir()]
    
    total_removed = 0
    
    for campaign_dir in campaign_dirs:
        contacts_file = campaign_dir / "contacts.csv"
        if contacts_file.exists():
            removed = clean_bounces_from_csv(contacts_file, dry_run=dry_run)
            if removed > 0:
                action = "würden entfernt" if dry_run else "entfernt"
                print(f"   {campaign_dir.name}: {removed} E-Mail(s) {action}")
                total_removed += removed
    
    if total_removed > 0:
        if dry_run:
            print(f"\n⚠️  Führe ohne --dry-run aus, um {total_removed} E-Mail(s) zu entfernen.\n")
        else:
            print(f"\n✅ {total_removed} E-Mail(s) aus CSV-Dateien entfernt.")
            print("   Backups wurden als .csv.backup gespeichert.\n")
    else:
        print("\n✅ Keine betroffenen E-Mails in Kampagnen-CSVs.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Obscuras Mail Campaign Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python send_campaign.py --list              Alle Kampagnen anzeigen
  python send_campaign.py kanzleien_mobile    Kampagne starten
  python send_campaign.py kanzleien_mobile --dry-run    Testlauf
  python send_campaign.py kanzleien_mobile --preview    Vorschau erstellen
  python send_campaign.py kanzleien_mobile --limit 5    Nur 5 Mails senden
  python send_campaign.py kanzleien_mobile --test me@example.com   Test-Mail
  python send_campaign.py kanzleien_mobile --schedule   Mo-Fr 9-17 Uhr
  python send_campaign.py --bounces           Alle Bounces anzeigen
  python send_campaign.py --clean-bounces     CSV-Dateien bereinigen
        """
    )
    
    parser.add_argument("campaign", nargs="?", help="Name des Kampagnen-Ordners")
    parser.add_argument("--list", "-l", action="store_true", help="Verfügbare Kampagnen anzeigen")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Testlauf ohne Versand")
    parser.add_argument("--preview", "-p", action="store_true", help="HTML-Vorschau erstellen")
    parser.add_argument("--limit", "-n", type=int, help="Maximale Anzahl E-Mails")
    
    # Neue Features
    parser.add_argument("--test", "-t", metavar="EMAIL", help="Test-Mail an einzelne Adresse senden")
    parser.add_argument("--schedule", "-s", action="store_true", 
                        help="Nur im Zeitfenster senden (Mo-Fr, 9-17 Uhr)")
    parser.add_argument("--schedule-days", default="1-5", 
                        help="Erlaubte Wochentage (1=Mo, 7=So), z.B. '1-5' (default: Mo-Fr)")
    parser.add_argument("--schedule-hours", default="9-17", 
                        help="Erlaubte Stunden, z.B. '9-17' (default: 9-17 Uhr)")
    
    # Bounce-Handling
    parser.add_argument("--bounces", action="store_true", help="Alle Bounces anzeigen")
    parser.add_argument("--clean-bounces", action="store_true", 
                        help="Gebounced E-Mails aus CSV-Dateien entfernen")
    parser.add_argument("--include-bounced", action="store_true",
                        help="Gebounced E-Mails nicht überspringen")
    
    args = parser.parse_args()
    
    # Bounce-Befehle
    if args.bounces:
        show_bounces()
        return
    
    if args.clean_bounces:
        clean_bounces(campaign_name=args.campaign, dry_run=args.dry_run)
        return
    
    if args.list or not args.campaign:
        list_campaigns()
        return
    
    if args.preview:
        preview_campaign(args.campaign)
        return
    
    if args.test:
        send_test_email(args.campaign, args.test)
        return
    
    # Schedule erstellen wenn aktiviert
    schedule = None
    if args.schedule:
        schedule = ScheduleChecker(days=args.schedule_days, hours=args.schedule_hours)
        print(f"\n⏰ Schedule aktiv: Tage={args.schedule_days}, Stunden={args.schedule_hours}")
    
    run_campaign(
        args.campaign,
        dry_run=args.dry_run,
        limit=args.limit,
        schedule=schedule,
        skip_bounced=not args.include_bounced
    )


if __name__ == "__main__":
    main()
