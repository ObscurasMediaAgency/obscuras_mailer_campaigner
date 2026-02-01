import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# SMTP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
# Setze diese Werte als Umgebungsvariablen:
#   export SMTP_HOST="smtp.deinserver.de"
#   export SMTP_PORT="465"
#   export SMTP_USER="mail@obscuras-media-agency.de"
#   export SMTP_PASS="dein-passwort"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.deinserver.de")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "mail@obscuras-media-agency.de")
SMTP_PASS = os.getenv("SMTP_PASS")

if not SMTP_PASS:
    raise EnvironmentError(
        "⚠️  SMTP_PASS nicht gesetzt! "
        "Bitte als Umgebungsvariable setzen: export SMTP_PASS='dein-passwort'"
    )

# ═══════════════════════════════════════════════════════════════════
# SENDER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
FROM_NAME = "Sascha Gebel"
FROM_EMAIL = os.getenv("FROM_EMAIL", "mail@obscuras-media-agency.de")

# ═══════════════════════════════════════════════════════════════════
# EMAIL CONTENT
# ═══════════════════════════════════════════════════════════════════
SUBJECT = "Hinweis zur mobilen Darstellung Ihrer Website"

# ═══════════════════════════════════════════════════════════════════
# DYNAMIC TEMPLATE VARIABLES
# ═══════════════════════════════════════════════════════════════════
# Diese werden automatisch in Templates ersetzt
TEMPLATE_GLOBALS = {
    "YEAR": str(datetime.now().year),
}
