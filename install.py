#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  Obscuras Mailer Campaigner - Universal Installer
  Unterstützt: Linux, Windows, macOS
═══════════════════════════════════════════════════════════════════════════════

  Verwendung:
      python install.py                 # Normale Installation
      python install.py --update        # Update mit Backup
      python install.py --uninstall     # Deinstallation
      python install.py --repair        # Reparatur-Installation
      python install.py --check         # Nur Systemprüfung
      python install.py --no-desktop    # Ohne Desktop-Integration
      python install.py --dev           # Entwickler-Modus (mit Dev-Dependencies)

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import platform
import subprocess
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# Konstanten
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "Obscuras Mailer Campaigner"
APP_ID = "obscuras-mailer-campaigner"
APP_VERSION = "1.3.1"
MIN_PYTHON_VERSION = (3, 10)
VENV_DIR = ".venv"
CONFIG_FILE = ".install_config.json"

# Farben für Terminal-Ausgabe
class Colors:
    """ANSI Farbcodes für Terminal-Ausgabe."""
    _colors: dict[str, str] = {
        'HEADER': '\033[95m',
        'BLUE': '\033[94m',
        'CYAN': '\033[96m',
        'GREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
    }
    
    HEADER: str = _colors['HEADER']
    BLUE: str = _colors['BLUE']
    CYAN: str = _colors['CYAN']
    GREEN: str = _colors['GREEN']
    WARNING: str = _colors['WARNING']
    FAIL: str = _colors['FAIL']
    ENDC: str = _colors['ENDC']
    BOLD: str = _colors['BOLD']
    UNDERLINE: str = _colors['UNDERLINE']
    
    _disabled: bool = False

    @classmethod
    def disable(cls) -> None:
        """Deaktiviert Farben (für Windows ohne ANSI-Support)."""
        if cls._disabled:
            return
        cls._disabled = True
        for key in cls._colors:
            setattr(cls, key, '')


# ═══════════════════════════════════════════════════════════════════════════════
# Hilfsfunktionen
# ═══════════════════════════════════════════════════════════════════════════════

def get_os() -> str:
    """Ermittelt das Betriebssystem."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def enable_windows_ansi() -> None:
    """Aktiviert ANSI-Farben unter Windows."""
    if get_os() == "windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)  # type: ignore[union-attr]
        except Exception:
            Colors.disable()


def print_banner():
    """Zeigt das Installations-Banner."""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗ ██████╗ ███████╗ ██████╗██╗   ██╗██████╗  █████╗ ███████╗  ║
║  ██╔═══██╗██╔══██╗██╔════╝██╔════╝██║   ██║██╔══██╗██╔══██╗██╔════╝  ║
║  ██║   ██║██████╔╝███████╗██║     ██║   ██║██████╔╝███████║███████╗  ║
║  ██║   ██║██╔══██╗╚════██║██║     ██║   ██║██╔══██╗██╔══██║╚════██║  ║
║  ╚██████╔╝██████╔╝███████║╚██████╗╚██████╔╝██║  ██║██║  ██║███████║  ║
║   ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝  ║
║                                                                      ║
║                    {Colors.BOLD}Mailer Campaigner Installer{Colors.ENDC}{Colors.CYAN}                       ║
║                           Version {APP_VERSION}                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)


def print_step(step: int, total: int, message: str):
    """Zeigt einen Fortschrittsschritt."""
    print(f"\n{Colors.BLUE}[{step}/{total}]{Colors.ENDC} {Colors.BOLD}{message}{Colors.ENDC}")


def print_success(message: str):
    """Zeigt eine Erfolgsmeldung."""
    print(f"  {Colors.GREEN}✔{Colors.ENDC} {message}")


def print_warning(message: str):
    """Zeigt eine Warnung."""
    print(f"  {Colors.WARNING}⚠{Colors.ENDC} {message}")


def print_error(message: str):
    """Zeigt einen Fehler."""
    print(f"  {Colors.FAIL}✘{Colors.ENDC} {message}")


def print_info(message: str):
    """Zeigt eine Information."""
    print(f"  {Colors.CYAN}ℹ{Colors.ENDC} {message}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Fragt den Benutzer eine Ja/Nein-Frage."""
    suffix = " [J/n]: " if default else " [j/N]: "
    while True:
        response = input(f"  {Colors.CYAN}?{Colors.ENDC} {question}{suffix}").strip().lower()
        if not response:
            return default
        if response in ('j', 'ja', 'y', 'yes'):
            return True
        if response in ('n', 'nein', 'no'):
            return False
        print_warning("Bitte antworte mit 'j' oder 'n'.")


def run_command(cmd: List[str], cwd: Optional[Path] = None, capture: bool = False, 
                env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
    """Führt einen Shell-Befehl aus."""
    try:
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=full_env
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Befehl nicht gefunden: {cmd[0]}"
    except Exception as e:
        return 1, "", str(e)


def get_project_root() -> Path:
    """Gibt das Projektverzeichnis zurück."""
    return Path(__file__).parent.absolute()


def get_venv_path() -> Path:
    """Gibt den Pfad zum Virtual Environment zurück."""
    return get_project_root() / VENV_DIR


def get_python_executable() -> Path:
    """Gibt den Pfad zur Python-Executable im venv zurück."""
    venv_path = get_venv_path()
    if get_os() == "windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def get_pip_executable() -> Path:
    """Gibt den Pfad zur pip-Executable im venv zurück."""
    venv_path = get_venv_path()
    if get_os() == "windows":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


# ═══════════════════════════════════════════════════════════════════════════════
# Systemprüfungen
# ═══════════════════════════════════════════════════════════════════════════════

class SystemChecker:
    """Überprüft die Systemvoraussetzungen."""
    
    def __init__(self) -> None:
        self.os_type: str = get_os()
        self.checks_passed: bool = True
        self.warnings: List[str] = []
        self.requirements: Dict[str, Any] = {}
    
    def check_python_version(self) -> bool:
        """Prüft die Python-Version."""
        current = sys.version_info[:2]
        required = MIN_PYTHON_VERSION
        
        if current >= required:
            print_success(f"Python {current[0]}.{current[1]} (benötigt: {required[0]}.{required[1]}+)")
            return True
        else:
            print_error(f"Python {current[0]}.{current[1]} ist zu alt (benötigt: {required[0]}.{required[1]}+)")
            self.checks_passed = False
            return False
    
    def check_pip(self) -> bool:
        """Prüft, ob pip verfügbar ist."""
        code, stdout, _ = run_command([sys.executable, "-m", "pip", "--version"])
        if code == 0:
            version = stdout.split()[1] if stdout else "unbekannt"
            print_success(f"pip {version}")
            return True
        else:
            print_error("pip ist nicht installiert")
            self.checks_passed = False
            return False
    
    def check_venv_module(self) -> bool:
        """Prüft, ob venv verfügbar ist."""
        code, _, _ = run_command([sys.executable, "-c", "import venv"])
        if code == 0:
            print_success("venv-Modul verfügbar")
            return True
        else:
            print_warning("venv-Modul nicht verfügbar")
            print_info("Auf Debian/Ubuntu: sudo apt install python3-venv")
            self.checks_passed = False
            return False
    
    def check_system_dependencies_linux(self) -> bool:
        """Prüft Linux-spezifische Abhängigkeiten für PyQt6."""
        # Qt6 benötigt bestimmte Systembibliotheken
        required_packages = {
            'libxcb': 'libxcb1',
            'libGL': 'libgl1-mesa-glx',
            'libEGL': 'libegl1',
        }
        
        # Prüfe, ob ldconfig verfügbar ist
        for _lib, _package in required_packages.items():
            code, _, _ = run_command(["ldconfig", "-p"])
            if code != 0:
                # ldconfig nicht verfügbar, überspringe
                break
        
        # Prüfe, ob Qt6-Abhängigkeiten für Wayland/X11 vorhanden sind
        print_info("System-Bibliotheken für Qt6 sollten automatisch verfügbar sein.")
        self.warnings.append("Falls GUI-Probleme auftreten: sudo apt install libxcb-cursor0 libxcb-xinerama0")
        return True
    
    def check_system_dependencies_macos(self) -> bool:
        """Prüft macOS-spezifische Abhängigkeiten."""
        # Homebrew prüfen (optional, aber empfohlen)
        code, _, _ = run_command(["which", "brew"])
        if code != 0:
            self.warnings.append("Homebrew nicht gefunden (optional, aber empfohlen)")
        else:
            print_success("Homebrew verfügbar")
        return True
    
    def check_system_dependencies_windows(self) -> bool:
        """Prüft Windows-spezifische Abhängigkeiten."""
        # Visual C++ Redistributable (für einige Python-Packages)
        print_info("Stelle sicher, dass Visual C++ Redistributable installiert ist")
        return True
    
    def check_disk_space(self) -> bool:
        """Prüft den verfügbaren Speicherplatz."""
        required_mb = 500  # 500 MB für venv + Dependencies
        
        try:
            if get_os() == "windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                    ctypes.c_wchar_p(str(get_project_root())),
                    None, None, ctypes.pointer(free_bytes)
                )
                free_mb = free_bytes.value / (1024 * 1024)
            else:
                stat = os.statvfs(get_project_root())
                free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            
            if free_mb >= required_mb:
                print_success(f"Speicherplatz: {free_mb:.0f} MB frei (benötigt: {required_mb} MB)")
                return True
            else:
                print_error(f"Nicht genug Speicherplatz: {free_mb:.0f} MB frei (benötigt: {required_mb} MB)")
                self.checks_passed = False
                return False
        except Exception:
            print_warning("Speicherplatz konnte nicht geprüft werden")
            return True
    
    def check_network(self) -> bool:
        """Prüft die Netzwerkverbindung."""
        import urllib.request
        try:
            urllib.request.urlopen("https://pypi.org", timeout=5)
            print_success("Netzwerkverbindung zu PyPI verfügbar")
            return True
        except Exception:
            print_warning("Keine Verbindung zu PyPI - Offline-Installation erforderlich")
            self.warnings.append("Ohne Netzwerk können Dependencies nicht installiert werden")
            return False
    
    def run_all_checks(self) -> bool:
        """Führt alle Systemprüfungen durch."""
        print_step(1, 1, "Systemvoraussetzungen prüfen...")
        
        self.check_python_version()
        self.check_pip()
        self.check_venv_module()
        self.check_disk_space()
        self.check_network()
        
        # OS-spezifische Prüfungen
        if self.os_type == "linux":
            self.check_system_dependencies_linux()
        elif self.os_type == "macos":
            self.check_system_dependencies_macos()
        elif self.os_type == "windows":
            self.check_system_dependencies_windows()
        
        # Warnungen anzeigen
        if self.warnings:
            print(f"\n  {Colors.WARNING}Hinweise:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"    • {warning}")
        
        return self.checks_passed


# ═══════════════════════════════════════════════════════════════════════════════
# Installation
# ═══════════════════════════════════════════════════════════════════════════════

class Installer:
    """Hauptinstallationsklasse."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = get_project_root()
        self.venv_path = get_venv_path()
        self.os_type = get_os()
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt die Installationskonfiguration."""
        config_path = self.project_root / CONFIG_FILE
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_config(self):
        """Speichert die Installationskonfiguration."""
        config_path = self.project_root / CONFIG_FILE
        self.config['last_install'] = datetime.now().isoformat()
        self.config['version'] = APP_VERSION
        self.config['os'] = self.os_type
        self.config['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_venv(self) -> bool:
        """Erstellt das Virtual Environment."""
        if self.venv_path.exists():
            if self.args.repair:
                print_info("Lösche vorhandenes venv für Reparatur...")
                shutil.rmtree(self.venv_path)
            else:
                print_success("Virtual Environment existiert bereits")
                return True
        
        print_info("Erstelle Virtual Environment...")
        code, _, stderr = run_command([sys.executable, "-m", "venv", str(self.venv_path)])
        
        if code == 0:
            print_success("Virtual Environment erstellt")
            return True
        else:
            print_error(f"Fehler beim Erstellen: {stderr}")
            return False
    
    def upgrade_pip(self) -> bool:
        """Aktualisiert pip im venv."""
        print_info("Aktualisiere pip...")
        pip = get_pip_executable()
        code, _, stderr = run_command([str(pip), "install", "--upgrade", "pip", "wheel", "six", "packaging", "appdirs", "setuptools"])
        
        if code == 0:
            print_success("pip aktualisiert")
            return True
        else:
            print_warning(f"pip-Update fehlgeschlagen: {stderr}")
            return True  # Nicht kritisch
    
    def install_dependencies(self) -> bool:
        """Installiert die Abhängigkeiten."""
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            print_error("requirements.txt nicht gefunden!")
            return False
        
        print_info("Installiere Abhängigkeiten (dies kann einige Minuten dauern)...")
        pip = get_pip_executable()
        
        # Hauptabhängigkeiten
        code, _stdout, stderr = run_command(
            [str(pip), "install", "-r", str(requirements_file)],
            cwd=self.project_root
        )
        
        if code != 0:
            print_error("Fehler bei der Installation:")
            print(f"    {stderr[:500]}")
            return False
        
        # Dev-Dependencies (wenn angefordert)
        if self.args.dev:
            print_info("Installiere Entwickler-Abhängigkeiten...")
            dev_packages = ["pytest", "black", "mypy", "pylint", "pre-commit"]
            code, _, stderr = run_command([str(pip), "install"] + dev_packages)
            if code != 0:
                print_warning("Dev-Dependencies teilweise fehlgeschlagen")
        
        print_success("Alle Abhängigkeiten installiert")
        return True
    
    def create_launcher_script(self) -> bool:
        """Erstellt plattformspezifische Launcher-Skripte."""
        print_info("Erstelle Launcher-Skripte...")
        
        if self.os_type == "windows":
            return self._create_windows_launcher()
        else:
            return self._create_unix_launcher()
    
    def _create_unix_launcher(self) -> bool:
        """Erstellt Launcher für Linux/macOS."""
        launcher_path = self.project_root / "start.sh"
        
        script = f'''#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# {APP_NAME} - Launcher
# ═══════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual Environment aktivieren
source "{VENV_DIR}/bin/activate"

# Anwendung starten
python main.py "$@"
'''
        
        try:
            with open(launcher_path, 'w') as f:
                f.write(script)
            os.chmod(launcher_path, 0o755)
            print_success(f"Launcher erstellt: {launcher_path.name}")
            return True
        except Exception as e:
            print_error(f"Fehler beim Erstellen des Launchers: {e}")
            return False
    
    def _create_windows_launcher(self) -> bool:
        """Erstellt Launcher für Windows."""
        # Batch-Datei
        bat_path = self.project_root / "start.bat"
        bat_script = f'''@echo off
REM ═══════════════════════════════════════════════════════════════════
REM {APP_NAME} - Launcher
REM ═══════════════════════════════════════════════════════════════════

cd /d "%~dp0"
call "{VENV_DIR}\\Scripts\\activate.bat"
python main.py %*
'''
        
        # PowerShell-Skript (moderner)
        ps_path = self.project_root / "start.ps1"
        ps_script = f'''# ═══════════════════════════════════════════════════════════════════
# {APP_NAME} - Launcher (PowerShell)
# ═══════════════════════════════════════════════════════════════════

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Virtual Environment aktivieren
& ".\\{VENV_DIR}\\Scripts\\Activate.ps1"

# Anwendung starten
python main.py $args
'''
        
        try:
            with open(bat_path, 'w') as f:
                f.write(bat_script)
            with open(ps_path, 'w') as f:
                f.write(ps_script)
            print_success("Launcher erstellt: start.bat, start.ps1")
            return True
        except Exception as e:
            print_error(f"Fehler beim Erstellen der Launcher: {e}")
            return False
    
    def create_desktop_entry(self) -> bool:
        """Erstellt einen Desktop-Eintrag/Shortcut."""
        if self.args.no_desktop:
            print_info("Desktop-Integration übersprungen (--no-desktop)")
            return True
        
        print_info("Erstelle Desktop-Integration...")
        
        if self.os_type == "linux":
            return self._create_linux_desktop_entry()
        elif self.os_type == "macos":
            return self._create_macos_app()
        elif self.os_type == "windows":
            return self._create_windows_shortcut()
        
        return True
    
    def _create_linux_desktop_entry(self) -> bool:
        """Erstellt .desktop-Datei für Linux."""
        # Icon suchen (verschiedene Varianten)
        icon_path = None
        for icon_name in ["icon.png", "logo.png", "icon.svg", "logo.svg"]:
            potential_icon = self.project_root / "assets" / icon_name
            if potential_icon.exists():
                icon_path = potential_icon
                break
        
        # Desktop-Eintrag
        icon_value = str(icon_path) if icon_path is not None else "mail-send"
        desktop_entry = f'''[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=E-Mail Kampagnen Management
Exec={self.project_root / "start.sh"}
Icon={icon_value}
Terminal=false
Categories=Office;Email;
Keywords=email;campaign;marketing;
StartupWMClass={APP_ID}
'''
        
        # Im lokalen Applications-Ordner speichern
        applications_dir = Path.home() / ".local" / "share" / "applications"
        applications_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_path = applications_dir / f"{APP_ID}.desktop"
        
        try:
            with open(desktop_path, 'w') as f:
                f.write(desktop_entry)
            os.chmod(desktop_path, 0o755)
            print_success(f"Desktop-Eintrag erstellt: {desktop_path}")
            
            # Desktop-Datenbank aktualisieren
            run_command(["update-desktop-database", str(applications_dir)])
            
            return True
        except Exception as e:
            print_warning(f"Desktop-Eintrag konnte nicht erstellt werden: {e}")
            return False
    
    def _create_macos_app(self) -> bool:
        """Erstellt ein macOS App-Bundle (vereinfacht)."""
        # Erstelle ein einfaches Shell-Skript im Applications-Ordner
        app_script = Path.home() / "Applications" / f"{APP_NAME}.command"
        
        script = f'''#!/bin/bash
cd "{self.project_root}"
source "{VENV_DIR}/bin/activate"
python main.py
'''
        
        try:
            with open(app_script, 'w') as f:
                f.write(script)
            os.chmod(app_script, 0o755)
            print_success(f"App-Launcher erstellt: {app_script}")
            return True
        except Exception as e:
            print_warning(f"App-Launcher konnte nicht erstellt werden: {e}")
            return False
    
    def _create_windows_shortcut(self) -> bool:
        """Erstellt eine Windows-Verknüpfung."""
        try:
            # PowerShell-basierte Shortcut-Erstellung
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / f"{APP_NAME}.lnk"
            target = self.project_root / "start.bat"
            
            ps_command = f'''
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.WorkingDirectory = "{self.project_root}"
$Shortcut.Description = "{APP_NAME} - E-Mail Kampagnen Management"
$Shortcut.Save()
'''
            
            code, _, stderr = run_command(
                ["powershell", "-Command", ps_command]
            )
            
            if code == 0:
                print_success(f"Desktop-Verknüpfung erstellt")
                return True
            else:
                print_warning(f"Shortcut-Erstellung fehlgeschlagen: {stderr}")
                return False
        except Exception as e:
            print_warning(f"Shortcut konnte nicht erstellt werden: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialisiert die Datenbank."""
        print_info("Initialisiere Datenbank...")
        
        python = get_python_executable()
        init_script = '''
from models.database import init_database
init_database()
print("OK")
'''
        
        code, stdout, stderr = run_command(
            [str(python), "-c", init_script],
            cwd=self.project_root
        )
        
        if code == 0 and "OK" in stdout:
            print_success("Datenbank initialisiert")
            return True
        else:
            print_warning(f"Datenbank-Initialisierung: {stderr or 'Unbekannter Fehler'}")
            return True  # Nicht kritisch, wird beim ersten Start erstellt
    
    def create_default_config(self) -> bool:
        """Erstellt Standard-Konfigurationsdateien, falls nicht vorhanden."""
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Prüfe, ob wichtige Configs existieren
        sender_yaml = config_dir / "sender.yaml"
        if not sender_yaml.exists():
            default_sender = '''# Absender-Konfiguration
sender:
  name: "Ihr Name"
  email: "ihre@email.de"
  company: "Ihre Firma"
  phone: "+49 123 456789"
  website: "https://ihre-website.de"
'''
            try:
                with open(sender_yaml, 'w') as f:
                    f.write(default_sender)
                print_info("Standard sender.yaml erstellt")
            except Exception:
                pass
        
        return True
    
    def run_installation(self) -> bool:
        """Führt die komplette Installation durch."""
        total_steps = 6
        
        # Schritt 1: Systemprüfung
        checker = SystemChecker()
        if not checker.run_all_checks():
            print_error("\nSystemvoraussetzungen nicht erfüllt!")
            if not ask_yes_no("Trotzdem fortfahren?", default=False):
                return False
        
        # Schritt 2: Virtual Environment
        print_step(2, total_steps, "Virtual Environment einrichten...")
        if not self.create_venv():
            return False
        
        # Schritt 3: pip aktualisieren
        print_step(3, total_steps, "Build-Tools aktualisieren...")
        self.upgrade_pip()
        
        # Schritt 4: Dependencies installieren
        print_step(4, total_steps, "Abhängigkeiten installieren...")
        if not self.install_dependencies():
            return False
        
        # Schritt 5: Launcher & Desktop
        print_step(5, total_steps, "Launcher & Desktop-Integration...")
        self.create_launcher_script()
        self.create_desktop_entry()
        
        # Schritt 6: Initialisierung
        print_step(6, total_steps, "Anwendung initialisieren...")
        self.initialize_database()
        self.create_default_config()
        
        # Konfiguration speichern
        self.save_config()
        
        # Erfolg!
        self._print_success_message()
        return True
    
    def _print_success_message(self):
        """Zeigt die Erfolgsmeldung."""
        print(f"""
{Colors.GREEN}═══════════════════════════════════════════════════════════════════════════════
  ✔ Installation erfolgreich abgeschlossen!
═══════════════════════════════════════════════════════════════════════════════{Colors.ENDC}

  {Colors.BOLD}Anwendung starten:{Colors.ENDC}
""")
        
        if self.os_type == "windows":
            print(f"    • Doppelklick auf {Colors.CYAN}start.bat{Colors.ENDC}")
            print(f"    • Oder Desktop-Verknüpfung nutzen")
        else:
            print(f"    • {Colors.CYAN}./start.sh{Colors.ENDC}")
            print(f"    • Oder über das Anwendungsmenü")
        
        print(f"""
  {Colors.BOLD}Manuell starten:{Colors.ENDC}
    1. source {VENV_DIR}/bin/activate    {'(Linux/macOS)' if self.os_type != 'windows' else ''}
       {VENV_DIR}\\Scripts\\activate.bat  {'(Windows)' if self.os_type == 'windows' else ''}
    2. python main.py

  {Colors.BOLD}Weitere Befehle:{Colors.ENDC}
    python install.py --update      # Update durchführen
    python install.py --uninstall   # Deinstallation
    python install.py --repair      # Reparatur-Installation

{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.ENDC}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# Update-Funktionalität
# ═══════════════════════════════════════════════════════════════════════════════

class Updater:
    """Handles application updates with backup functionality."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = get_project_root()
        self.backup_dir = self.project_root / "backups"
    
    def create_backup(self) -> Optional[Path]:
        """Erstellt ein Backup vor dem Update."""
        print_info("Erstelle Backup...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            # Wichtige Verzeichnisse sichern
            dirs_to_backup = ["config", "campaigns", "data", "templates"]
            
            for dir_name in dirs_to_backup:
                src = self.project_root / dir_name
                if src.exists():
                    dst = backup_path / dir_name
                    shutil.copytree(src, dst)
            
            # Datenbank sichern
            db_file = self.project_root / "campaign_manager.db"
            if db_file.exists():
                shutil.copy(db_file, backup_path / "campaign_manager.db")
            
            print_success(f"Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            print_error(f"Backup fehlgeschlagen: {e}")
            return None
    
    def run_update(self) -> bool:
        """Führt das Update durch."""
        print_step(1, 3, "Backup erstellen...")
        backup_path = self.create_backup()
        
        if not backup_path and not ask_yes_no("Ohne Backup fortfahren?", default=False):
            return False
        
        print_step(2, 3, "Abhängigkeiten aktualisieren...")
        pip = get_pip_executable()
        
        code, _, stderr = run_command(
            [str(pip), "install", "--upgrade", "-r", str(self.project_root / "requirements.txt")],
            cwd=self.project_root
        )
        
        if code != 0:
            print_error(f"Update fehlgeschlagen: {stderr}")
            if backup_path:
                print_info(f"Backup verfügbar unter: {backup_path}")
            return False
        
        print_step(3, 3, "Datenbank-Migrationen...")
        # Hier könnten Alembic-Migrationen laufen
        print_info("Keine Migrationen erforderlich")
        
        print_success("Update erfolgreich abgeschlossen!")
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# Deinstallation
# ═══════════════════════════════════════════════════════════════════════════════

class Uninstaller:
    """Handles application uninstallation."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = get_project_root()
        self.os_type = get_os()
    
    def run_uninstall(self) -> bool:
        """Führt die Deinstallation durch."""
        print(f"\n{Colors.WARNING}╔═══════════════════════════════════════════════════════════════════╗")
        print(f"║  WARNUNG: Dies wird alle installierten Komponenten entfernen!   ║")
        print(f"╚═══════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        keep_data = ask_yes_no("Benutzerdaten (Kampagnen, Kontakte, Datenbank) behalten?", default=True)
        
        if not ask_yes_no("Deinstallation wirklich durchführen?", default=False):
            print_info("Deinstallation abgebrochen.")
            return False
        
        # Virtual Environment entfernen
        print_step(1, 3, "Virtual Environment entfernen...")
        venv_path = get_venv_path()
        if venv_path.exists():
            shutil.rmtree(venv_path)
            print_success("Virtual Environment entfernt")
        
        # Desktop-Integration entfernen
        print_step(2, 3, "Desktop-Integration entfernen...")
        self._remove_desktop_entry()
        
        # Launcher entfernen
        print_step(3, 3, "Launcher entfernen...")
        for launcher in ["start.sh", "start.bat", "start.ps1"]:
            launcher_path = self.project_root / launcher
            if launcher_path.exists():
                launcher_path.unlink()
        print_success("Launcher entfernt")
        
        if not keep_data:
            # Datenbank entfernen
            db_file = self.project_root / "campaign_manager.db"
            if db_file.exists():
                db_file.unlink()
            print_success("Datenbank entfernt")
        
        # Konfigurationsdatei entfernen
        config_file = self.project_root / CONFIG_FILE
        if config_file.exists():
            config_file.unlink()
        
        print(f"""
{Colors.GREEN}═══════════════════════════════════════════════════════════════════════════════
  ✔ Deinstallation abgeschlossen
═══════════════════════════════════════════════════════════════════════════════{Colors.ENDC}
""")
        
        if keep_data:
            print_info("Benutzerdaten wurden beibehalten.")
            print_info("Um alles zu entfernen, löschen Sie den Projektordner manuell.")
        
        return True
    
    def _remove_desktop_entry(self):
        """Entfernt die Desktop-Integration."""
        if self.os_type == "linux":
            desktop_path = Path.home() / ".local" / "share" / "applications" / f"{APP_ID}.desktop"
            if desktop_path.exists():
                desktop_path.unlink()
                print_success("Desktop-Eintrag entfernt")
        elif self.os_type == "macos":
            app_script = Path.home() / "Applications" / f"{APP_NAME}.command"
            if app_script.exists():
                app_script.unlink()
                print_success("App-Launcher entfernt")
        elif self.os_type == "windows":
            shortcut_path = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
            if shortcut_path.exists():
                shortcut_path.unlink()
                print_success("Desktop-Verknüpfung entfernt")


# ═══════════════════════════════════════════════════════════════════════════════
# Hauptprogramm
# ═══════════════════════════════════════════════════════════════════════════════

def parse_arguments() -> argparse.Namespace:
    """Parst die Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python install.py              # Normale Installation
  python install.py --update     # Update mit Backup
  python install.py --uninstall  # Deinstallation
  python install.py --check      # Nur Systemprüfung
        """
    )
    
    parser.add_argument('--update', '-u', action='store_true',
                        help='Update durchführen (mit Backup)')
    parser.add_argument('--uninstall', action='store_true',
                        help='Anwendung deinstallieren')
    parser.add_argument('--repair', '-r', action='store_true',
                        help='Reparatur-Installation (venv neu erstellen)')
    parser.add_argument('--check', '-c', action='store_true',
                        help='Nur Systemvoraussetzungen prüfen')
    parser.add_argument('--no-desktop', action='store_true',
                        help='Keine Desktop-Integration erstellen')
    parser.add_argument('--dev', '-d', action='store_true',
                        help='Entwickler-Abhängigkeiten installieren')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Weniger Ausgaben')
    
    return parser.parse_args()


def main():
    """Hauptfunktion."""
    enable_windows_ansi()
    args = parse_arguments()
    
    # Banner anzeigen
    if not args.quiet:
        print_banner()
    
    print(f"  {Colors.CYAN}Betriebssystem:{Colors.ENDC} {platform.system()} {platform.release()}")
    print(f"  {Colors.CYAN}Python:{Colors.ENDC} {sys.version.split()[0]}")
    print(f"  {Colors.CYAN}Arbeitsverzeichnis:{Colors.ENDC} {get_project_root()}")
    
    try:
        # Nur Systemprüfung
        if args.check:
            checker = SystemChecker()
            success = checker.run_all_checks()
            sys.exit(0 if success else 1)
        
        # Deinstallation
        if args.uninstall:
            uninstaller = Uninstaller(args)
            success = uninstaller.run_uninstall()
            sys.exit(0 if success else 1)
        
        # Update
        if args.update:
            updater = Updater(args)
            success = updater.run_update()
            sys.exit(0 if success else 1)
        
        # Normale Installation
        installer = Installer(args)
        success = installer.run_installation()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Installation abgebrochen.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unerwarteter Fehler: {e}")
        if args.dev or "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
