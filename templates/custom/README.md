# Custom Templates

Lege hier deine eigenen E-Mail-Templates ab.

## Verwendung

1. Kopiere ein Basis-Template (z.B. `../base_generic.html`) in diesen Ordner
2. Passe das Design an deine Bedürfnisse an
3. Wähle das Template in der Kampagnen-Konfiguration

## Verfügbare Platzhalter

### Pflichtfelder
| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{EMAIL_SUBJECT}}` | Betreffzeile |
| `{{SENDER_NAME}}` | Absender-Name |
| `{{COMPANY_NAME}}` | Firmenname |
| `{{YEAR}}` | Aktuelles Jahr |

### Inhalt
| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{CONTENT_GREETING}}` | Begrüßung (z.B. "Sehr geehrte Damen und Herren,") |
| `{{CONTENT_INTRO}}` | Einleitungstext |
| `{{CONTENT_BODY}}` | Hauptinhalt (HTML) |
| `{{CONTENT_HIGHLIGHT}}` | Hervorgehobenes Zitat |
| `{{CONTENT_CTA_TEXT}}` | Call-to-Action Text |
| `{{CONTENT_CTA_URL}}` | Call-to-Action Link |

### Kontakt-Personalisierung
| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{EMAIL}}` | E-Mail des Empfängers |
| `{{ANREDE}}` | Anrede (Herr/Frau) |
| `{{VORNAME}}` | Vorname |
| `{{NACHNAME}}` | Nachname |
| `{{FIRMA}}` | Firmenname des Empfängers |
| `{{POSITION}}` | Position/Titel |

### Design/Theme (optional)
| Platzhalter | Standard | Beschreibung |
|-------------|----------|--------------|
| `{{THEME_PRIMARY_COLOR}}` | #3b82f6 | Primärfarbe |
| `{{THEME_SECONDARY_COLOR}}` | #8b5cf6 | Sekundärfarbe |
| `{{THEME_BG_COLOR}}` | #f4f4f5 | Hintergrundfarbe |
| `{{THEME_CARD_BG}}` | #ffffff | Karten-Hintergrund |
| `{{THEME_TEXT_COLOR}}` | #52525b | Textfarbe |
| `{{THEME_HEADING_COLOR}}` | #18181b | Überschriften |
| `{{THEME_MUTED_COLOR}}` | #71717a | Gedämpfte Farbe |
| `{{THEME_BORDER_COLOR}}` | #e4e4e7 | Rahmenfarbe |
| `{{THEME_ACCENT_COLOR}}` | - | Akzentlinie (optional) |

### Firmen-Infos
| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{COMPANY_URL}}` | Website-URL |
| `{{COMPANY_DOMAIN}}` | Domain (z.B. example.de) |
| `{{COMPANY_ADDRESS}}` | Adresse |
| `{{LOGO_URL}}` | Logo-URL |
| `{{SENDER_TITLE}}` | Titel/Position des Absenders |
| `{{UNSUBSCRIBE_URL}}` | Abmelde-Link (optional) |

## Jinja2-Syntax

Templates unterstützen Jinja2-Syntax:

```html
<!-- Bedingte Anzeige -->
{% if LOGO_URL %}
<img src="{{LOGO_URL}}" alt="Logo">
{% endif %}

<!-- Standardwerte -->
<p style="color:{{THEME_TEXT_COLOR|default('#333333')}};">Text</p>

<!-- Schleifen (für Listen) -->
{% for item in items %}
<li>{{item}}</li>
{% endfor %}
```

## Beispiel: Eigenes Template

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>{{EMAIL_SUBJECT}}</title>
</head>
<body style="margin:0;padding:20px;font-family:Arial,sans-serif;">
  
  <h1 style="color:#333;">{{CONTENT_GREETING}}</h1>
  
  <div>{{CONTENT_BODY}}</div>
  
  {% if CONTENT_CTA_URL %}
  <p>
    <a href="{{CONTENT_CTA_URL}}" style="background:#007bff;color:#fff;padding:10px 20px;text-decoration:none;">
      {{CONTENT_CTA_TEXT}}
    </a>
  </p>
  {% endif %}
  
  <hr>
  <p>{{SENDER_NAME}}<br>{{COMPANY_NAME}}</p>
  
</body>
</html>
```

## Tipps

1. **Inline-CSS verwenden** - E-Mail-Clients ignorieren externe Stylesheets
2. **Tabellen für Layout** - Flexbox/Grid werden nicht überall unterstützt
3. **Bilder mit voller URL** - Relative Pfade funktionieren nicht
4. **Testen** - Vorschau unter "Kampagnen → Vorschau" nutzen
5. **Responsive** - `max-width` und `width:100%` für mobile Ansicht
