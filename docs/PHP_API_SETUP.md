# PHP License API - Setup-Anleitung

Diese Anleitung beschreibt, wie du die PHP-basierte Lizenz-API in deinem Angular-Projekt (`mailer-campaigner.de`) einrichtest.

## Übersicht

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────┐
│  Desktop-App    │────▶│  mailer-campaigner.de   │────▶│   Stripe    │
│  (PyQt6)        │◀────│  /api/*.php             │◀────│   API       │
└─────────────────┘     └─────────────────────────┘     └─────────────┘
        │                         │
        │                         ▼
        │                 ┌───────────────┐
        │                 │   E-Mail an   │
        │                 │    Käufer     │
        │                 └───────────────┘
        │                         │
        ▼                         ▼
┌─────────────────┐     ┌─────────────────────────┐
│  Lizenz lokal   │◀────│  Lizenzschlüssel per    │
│  gespeichert    │     │  E-Mail zugestellt      │
└─────────────────┘     └─────────────────────────┘
```

---

## 1. Verzeichnisstruktur erstellen

Im Root deines Angular-Projekts (`mailer-campaigner.de/`):

```bash
mkdir -p api/includes
mkdir -p api/logs
```

**Resultierende Struktur:**
```
mailer-campaigner.de/
├── api/
│   ├── includes/
│   │   ├── config.php       # Stripe-Keys & E-Mail-Konfiguration
│   │   ├── LicenseManager.php
│   │   └── EmailService.php
│   ├── logs/                # API-Logs (chmod 755)
│   ├── checkout.php         # Erstellt Stripe Checkout
│   ├── webhook.php          # Stripe Webhook-Handler
│   ├── verify.php           # Lizenz verifizieren
│   ├── activate.php         # Lizenz aktivieren (optional)
│   └── .htaccess            # Sicherheit & CORS
├── dist/
│   └── mailer-campaigner.de/
├── src/
└── ...
```

---

## 2. Konfigurationsdatei erstellen

**`api/includes/config.php`**

```php
<?php
/**
 * Lizenz-API Konfiguration
 * WICHTIG: Diese Datei niemals committen!
 */

return [
    // ═══════════════════════════════════════════════════════════════
    // STRIPE KONFIGURATION
    // ═══════════════════════════════════════════════════════════════
    'stripe' => [
        // Live-Keys verwenden für Produktion (sk_live_..., pk_live_...)
        'secret_key' => 'sk_test_DEIN_SECRET_KEY',
        'publishable_key' => 'pk_test_DEIN_PUBLISHABLE_KEY',
        'price_id' => 'price_DEINE_PRICE_ID',  // Optional
        'webhook_secret' => 'whsec_DEIN_WEBHOOK_SECRET',  // Aus Stripe Dashboard
    ],
    
    // ═══════════════════════════════════════════════════════════════
    // PRODUKT-INFO
    // ═══════════════════════════════════════════════════════════════
    'product' => [
        'name' => 'Obscuras Campaign Manager Pro',
        'price_eur' => 129.00,
        'license_days' => 365,
    ],
    
    // ═══════════════════════════════════════════════════════════════
    // E-MAIL KONFIGURATION (SMTP)
    // ═══════════════════════════════════════════════════════════════
    'email' => [
        'smtp_host' => 'mail.dein-server.de',
        'smtp_port' => 465,
        'smtp_user' => 'license@mailer-campaigner.de',
        'smtp_pass' => 'DEIN_SMTP_PASSWORT',
        'smtp_secure' => 'ssl',  // 'ssl' oder 'tls'
        'from_email' => 'license@mailer-campaigner.de',
        'from_name' => 'Obscuras Campaign Manager',
    ],
    
    // ═══════════════════════════════════════════════════════════════
    // CHECKOUT URLS
    // ═══════════════════════════════════════════════════════════════
    'urls' => [
        'success' => 'https://mailer-campaigner.de/payment/success',
        'cancel' => 'https://mailer-campaigner.de/payment/cancel',
    ],
    
    // ═══════════════════════════════════════════════════════════════
    // DATENBANK (SQLite)
    // ═══════════════════════════════════════════════════════════════
    'database' => [
        'path' => __DIR__ . '/../data/licenses.db',
    ],
    
    // ═══════════════════════════════════════════════════════════════
    // SICHERHEIT
    // ═══════════════════════════════════════════════════════════════
    'security' => [
        // Erlaubte Origins für CORS (Desktop-App braucht das nicht)
        'allowed_origins' => [
            'https://mailer-campaigner.de',
        ],
        // API-Key für zusätzliche Absicherung (optional)
        'api_key' => null,  // Oder: 'ein-geheimer-api-key'
    ],
];
```

---

## 3. API-Dateien erstellen

### 3.1 License Manager

**`api/includes/LicenseManager.php`**

```php
<?php
/**
 * Lizenz-Verwaltung
 */

class LicenseManager {
    private $db;
    private $config;
    
    public function __construct(array $config) {
        $this->config = $config;
        $this->initDatabase();
    }
    
    private function initDatabase(): void {
        $dbPath = $this->config['database']['path'];
        $dbDir = dirname($dbPath);
        
        if (!is_dir($dbDir)) {
            mkdir($dbDir, 0755, true);
        }
        
        $this->db = new PDO("sqlite:$dbPath");
        $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        // Tabelle erstellen falls nicht vorhanden
        $this->db->exec("
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                stripe_session_id TEXT,
                stripe_payment_intent TEXT,
                product TEXT DEFAULT 'pro',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                activated_at DATETIME,
                machine_id TEXT,
                is_active INTEGER DEFAULT 1
            )
        ");
        
        // Index für schnelle Lookups
        $this->db->exec("
            CREATE INDEX IF NOT EXISTS idx_license_key ON licenses(license_key)
        ");
    }
    
    /**
     * Generiert einen neuen Lizenzschlüssel
     */
    public function generateLicenseKey(): string {
        $segments = [];
        for ($i = 0; $i < 4; $i++) {
            $segments[] = strtoupper(bin2hex(random_bytes(2)));
        }
        return implode('-', $segments);  // Format: XXXX-XXXX-XXXX-XXXX
    }
    
    /**
     * Erstellt eine neue Lizenz nach erfolgreicher Zahlung
     */
    public function createLicense(
        string $email, 
        string $sessionId, 
        string $paymentIntent
    ): array {
        $licenseKey = $this->generateLicenseKey();
        $licenseDays = $this->config['product']['license_days'];
        $expiresAt = date('Y-m-d H:i:s', strtotime("+$licenseDays days"));
        
        $stmt = $this->db->prepare("
            INSERT INTO licenses 
            (license_key, email, stripe_session_id, stripe_payment_intent, expires_at) 
            VALUES (?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([$licenseKey, $email, $sessionId, $paymentIntent, $expiresAt]);
        
        return [
            'license_key' => $licenseKey,
            'email' => $email,
            'expires_at' => $expiresAt,
            'product' => 'pro',
        ];
    }
    
    /**
     * Verifiziert einen Lizenzschlüssel
     */
    public function verifyLicense(string $licenseKey): array {
        $stmt = $this->db->prepare("
            SELECT * FROM licenses 
            WHERE license_key = ? AND is_active = 1
        ");
        $stmt->execute([$licenseKey]);
        $license = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if (!$license) {
            return ['valid' => false, 'error' => 'Lizenzschlüssel nicht gefunden'];
        }
        
        $now = new DateTime();
        $expires = new DateTime($license['expires_at']);
        
        if ($now > $expires) {
            return ['valid' => false, 'error' => 'Lizenz abgelaufen'];
        }
        
        return [
            'valid' => true,
            'email' => $license['email'],
            'product' => $license['product'],
            'expires' => $license['expires_at'],
            'activated' => !empty($license['activated_at']),
        ];
    }
    
    /**
     * Aktiviert eine Lizenz mit Machine-ID
     */
    public function activateLicense(string $licenseKey, string $machineId): array {
        // Zuerst verifizieren
        $verify = $this->verifyLicense($licenseKey);
        if (!$verify['valid']) {
            return $verify;
        }
        
        $stmt = $this->db->prepare("
            UPDATE licenses 
            SET activated_at = CURRENT_TIMESTAMP, machine_id = ?
            WHERE license_key = ?
        ");
        $stmt->execute([$machineId, $licenseKey]);
        
        return [
            'success' => true,
            'message' => 'Lizenz erfolgreich aktiviert',
            'expires' => $verify['expires'],
        ];
    }
    
    /**
     * Prüft ob für eine Session bereits eine Lizenz existiert
     */
    public function licenseExistsForSession(string $sessionId): bool {
        $stmt = $this->db->prepare("
            SELECT COUNT(*) FROM licenses WHERE stripe_session_id = ?
        ");
        $stmt->execute([$sessionId]);
        return $stmt->fetchColumn() > 0;
    }
}
```

### 3.2 Email Service

**`api/includes/EmailService.php`**

```php
<?php
/**
 * E-Mail Service für Lizenz-Versand
 * Verwendet PHPMailer (via Composer) oder PHP mail()
 */

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

class EmailService {
    private $config;
    
    public function __construct(array $config) {
        $this->config = $config['email'];
    }
    
    /**
     * Sendet die Lizenz per E-Mail an den Käufer
     */
    public function sendLicenseEmail(string $toEmail, array $licenseData): bool {
        $subject = "🎉 Dein Lizenzschlüssel für Obscuras Campaign Manager Pro";
        
        $htmlBody = $this->buildEmailHtml($licenseData);
        $textBody = $this->buildEmailText($licenseData);
        
        // Versuche PHPMailer, falls verfügbar
        if (class_exists('PHPMailer\PHPMailer\PHPMailer')) {
            return $this->sendWithPhpMailer($toEmail, $subject, $htmlBody, $textBody);
        }
        
        // Fallback auf PHP mail()
        return $this->sendWithMail($toEmail, $subject, $htmlBody, $textBody);
    }
    
    private function sendWithPhpMailer(
        string $toEmail, 
        string $subject, 
        string $htmlBody, 
        string $textBody
    ): bool {
        $mail = new PHPMailer(true);
        
        try {
            // Server-Einstellungen
            $mail->isSMTP();
            $mail->Host = $this->config['smtp_host'];
            $mail->SMTPAuth = true;
            $mail->Username = $this->config['smtp_user'];
            $mail->Password = $this->config['smtp_pass'];
            $mail->SMTPSecure = $this->config['smtp_secure'] === 'ssl' 
                ? PHPMailer::ENCRYPTION_SMTPS 
                : PHPMailer::ENCRYPTION_STARTTLS;
            $mail->Port = $this->config['smtp_port'];
            $mail->CharSet = 'UTF-8';
            
            // Empfänger
            $mail->setFrom($this->config['from_email'], $this->config['from_name']);
            $mail->addAddress($toEmail);
            
            // Inhalt
            $mail->isHTML(true);
            $mail->Subject = $subject;
            $mail->Body = $htmlBody;
            $mail->AltBody = $textBody;
            
            $mail->send();
            return true;
            
        } catch (Exception $e) {
            error_log("E-Mail Fehler: " . $mail->ErrorInfo);
            return false;
        }
    }
    
    private function sendWithMail(
        string $toEmail, 
        string $subject, 
        string $htmlBody, 
        string $textBody
    ): bool {
        $headers = [
            'MIME-Version: 1.0',
            'Content-type: text/html; charset=UTF-8',
            "From: {$this->config['from_name']} <{$this->config['from_email']}>",
            'X-Mailer: Obscuras License Server',
        ];
        
        return mail($toEmail, $subject, $htmlBody, implode("\r\n", $headers));
    }
    
    private function buildEmailHtml(array $licenseData): string {
        $licenseKey = htmlspecialchars($licenseData['license_key']);
        $expiresAt = date('d.m.Y', strtotime($licenseData['expires_at']));
        
        return <<<HTML
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fafafa; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
        .card { background: #18181b; border-radius: 12px; padding: 32px; border: 1px solid #27272a; }
        .logo { text-align: center; margin-bottom: 24px; color: #22c55e; font-size: 32px; }
        h1 { color: #fafafa; font-size: 24px; margin: 0 0 16px 0; }
        p { color: #a1a1aa; line-height: 1.6; margin: 0 0 16px 0; }
        .license-box { background: #09090b; border: 2px dashed #22c55e; border-radius: 8px; padding: 20px; text-align: center; margin: 24px 0; }
        .license-key { font-family: 'Monaco', 'Consolas', monospace; font-size: 24px; color: #22c55e; letter-spacing: 2px; font-weight: bold; }
        .info { background: #27272a; border-radius: 8px; padding: 16px; margin: 16px 0; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #3f3f46; }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #71717a; }
        .info-value { color: #fafafa; font-weight: 500; }
        .footer { text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid #27272a; }
        .footer p { font-size: 14px; color: #71717a; }
        .button { display: inline-block; background: #22c55e; color: #000; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">✓</div>
            <h1>Vielen Dank für deinen Kauf!</h1>
            <p>Deine Lizenz für <strong>Obscuras Campaign Manager Pro</strong> ist bereit.</p>
            
            <div class="license-box">
                <div style="color: #71717a; font-size: 14px; margin-bottom: 8px;">Dein Lizenzschlüssel:</div>
                <div class="license-key">{$licenseKey}</div>
            </div>
            
            <div class="info">
                <div class="info-row">
                    <span class="info-label">Produkt</span>
                    <span class="info-value">Campaign Manager Pro</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Gültig bis</span>
                    <span class="info-value">{$expiresAt}</span>
                </div>
            </div>
            
            <h2 style="font-size: 18px; color: #fafafa; margin: 24px 0 12px 0;">So aktivierst du deine Lizenz:</h2>
            <ol style="color: #a1a1aa; padding-left: 20px; line-height: 1.8;">
                <li>Öffne den Obscuras Campaign Manager</li>
                <li>Gehe zu <strong>Einstellungen → Lizenz</strong></li>
                <li>Gib deinen Lizenzschlüssel ein</li>
                <li>Klicke auf <strong>Aktivieren</strong></li>
            </ol>
            
            <p style="margin-top: 24px;">
                <a href="https://mailer-campaigner.de/download" class="button">
                    📥 Software herunterladen
                </a>
            </p>
        </div>
        
        <div class="footer">
            <p>Bei Fragen kontaktiere uns unter<br>
            <a href="mailto:support@mailer-campaigner.de" style="color: #22c55e;">support@mailer-campaigner.de</a></p>
            <p>© 2026 Obscuras Media Agency</p>
        </div>
    </div>
</body>
</html>
HTML;
    }
    
    private function buildEmailText(array $licenseData): string {
        $licenseKey = $licenseData['license_key'];
        $expiresAt = date('d.m.Y', strtotime($licenseData['expires_at']));
        
        return <<<TEXT
VIELEN DANK FÜR DEINEN KAUF!
=============================

Deine Lizenz für Obscuras Campaign Manager Pro ist bereit.

DEIN LIZENZSCHLÜSSEL:
{$licenseKey}

LIZENZ-DETAILS:
- Produkt: Campaign Manager Pro
- Gültig bis: {$expiresAt}

SO AKTIVIERST DU DEINE LIZENZ:
1. Öffne den Obscuras Campaign Manager
2. Gehe zu Einstellungen → Lizenz
3. Gib deinen Lizenzschlüssel ein
4. Klicke auf Aktivieren

Download: https://mailer-campaigner.de/download

Bei Fragen: support@mailer-campaigner.de

© 2026 Obscuras Media Agency
TEXT;
    }
}
```

### 3.3 Checkout Endpoint

**`api/checkout.php`**

```php
<?php
/**
 * POST /api/checkout.php
 * Erstellt eine Stripe Checkout Session
 * 
 * Request:  { "email": "kunde@example.com" }
 * Response: { "success": true, "checkout_url": "https://checkout.stripe.com/..." }
 */

require_once __DIR__ . '/includes/config.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Nur POST erlauben
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Konfiguration laden
$config = require __DIR__ . '/includes/config.php';

// Stripe SDK laden (via Composer)
require_once __DIR__ . '/vendor/autoload.php';

\Stripe\Stripe::setApiKey($config['stripe']['secret_key']);

// Request-Body parsen
$input = json_decode(file_get_contents('php://input'), true);
$email = $input['email'] ?? null;

try {
    // Checkout-Session Parameter
    $params = [
        'payment_method_types' => ['card'],
        'mode' => 'payment',
        'success_url' => $config['urls']['success'] . '?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url' => $config['urls']['cancel'],
        'metadata' => [
            'product' => 'campaign_manager_pro',
            'license_days' => (string) $config['product']['license_days'],
        ],
    ];
    
    // E-Mail vorausfüllen
    if ($email) {
        $params['customer_email'] = $email;
    }
    
    // Price ID verwenden falls konfiguriert
    if (!empty($config['stripe']['price_id'])) {
        $params['line_items'] = [[
            'price' => $config['stripe']['price_id'],
            'quantity' => 1,
        ]];
    } else {
        // Fallback: Preis dynamisch
        $params['line_items'] = [[
            'price_data' => [
                'currency' => 'eur',
                'product_data' => [
                    'name' => $config['product']['name'],
                    'description' => "Jahreslizenz - {$config['product']['license_days']} Tage gültig",
                ],
                'unit_amount' => (int) ($config['product']['price_eur'] * 100),
            ],
            'quantity' => 1,
        ]];
    }
    
    // Checkout Session erstellen
    $session = \Stripe\Checkout\Session::create($params);
    
    // Log
    error_log("[Checkout] Session erstellt: {$session->id} für {$email}");
    
    echo json_encode([
        'success' => true,
        'checkout_url' => $session->url,
        'session_id' => $session->id,
    ]);
    
} catch (\Stripe\Exception\ApiErrorException $e) {
    error_log("[Checkout] Stripe-Fehler: " . $e->getMessage());
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
    ]);
    
} catch (Exception $e) {
    error_log("[Checkout] Fehler: " . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Interner Fehler',
    ]);
}
```

### 3.4 Webhook Handler (WICHTIG!)

**`api/webhook.php`**

```php
<?php
/**
 * POST /api/webhook.php
 * Stripe Webhook Handler - wird von Stripe aufgerufen nach erfolgreicher Zahlung
 * 
 * WICHTIG: Diesen Endpoint in Stripe Dashboard registrieren unter:
 * https://dashboard.stripe.com/webhooks
 * 
 * Event: checkout.session.completed
 */

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/LicenseManager.php';
require_once __DIR__ . '/includes/EmailService.php';

// Stripe SDK
require_once __DIR__ . '/vendor/autoload.php';

$config = require __DIR__ . '/includes/config.php';

\Stripe\Stripe::setApiKey($config['stripe']['secret_key']);

// Raw POST body für Signatur-Verifizierung
$payload = file_get_contents('php://input');
$sigHeader = $_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '';
$webhookSecret = $config['stripe']['webhook_secret'];

try {
    // Webhook-Signatur verifizieren (WICHTIG für Sicherheit!)
    $event = \Stripe\Webhook::constructEvent(
        $payload, 
        $sigHeader, 
        $webhookSecret
    );
    
} catch (\UnexpectedValueException $e) {
    error_log("[Webhook] Invalid payload: " . $e->getMessage());
    http_response_code(400);
    exit;
    
} catch (\Stripe\Exception\SignatureVerificationException $e) {
    error_log("[Webhook] Invalid signature: " . $e->getMessage());
    http_response_code(400);
    exit;
}

// Event verarbeiten
switch ($event->type) {
    case 'checkout.session.completed':
        handleCheckoutCompleted($event->data->object, $config);
        break;
        
    case 'payment_intent.succeeded':
        // Optional: Zusätzliche Bestätigung
        error_log("[Webhook] Payment succeeded: " . $event->data->object->id);
        break;
        
    default:
        error_log("[Webhook] Unhandled event type: " . $event->type);
}

http_response_code(200);
echo json_encode(['received' => true]);

// ═══════════════════════════════════════════════════════════════════
// HANDLER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

function handleCheckoutCompleted($session, array $config): void {
    $sessionId = $session->id;
    $paymentIntent = $session->payment_intent ?? '';
    $customerEmail = $session->customer_details->email ?? $session->customer_email ?? '';
    
    error_log("[Webhook] Checkout completed: $sessionId, Email: $customerEmail");
    
    if (empty($customerEmail)) {
        error_log("[Webhook] FEHLER: Keine E-Mail-Adresse in Session!");
        return;
    }
    
    // Lizenz-Manager initialisieren
    $licenseManager = new LicenseManager($config);
    
    // Prüfen ob für diese Session bereits eine Lizenz existiert (Duplikat-Schutz)
    if ($licenseManager->licenseExistsForSession($sessionId)) {
        error_log("[Webhook] Lizenz für Session $sessionId existiert bereits");
        return;
    }
    
    // Neue Lizenz erstellen
    $licenseData = $licenseManager->createLicense(
        $customerEmail,
        $sessionId,
        $paymentIntent
    );
    
    error_log("[Webhook] Lizenz erstellt: {$licenseData['license_key']} für $customerEmail");
    
    // E-Mail mit Lizenzschlüssel senden
    $emailService = new EmailService($config);
    $emailSent = $emailService->sendLicenseEmail($customerEmail, $licenseData);
    
    if ($emailSent) {
        error_log("[Webhook] Lizenz-E-Mail gesendet an $customerEmail");
    } else {
        error_log("[Webhook] FEHLER: E-Mail konnte nicht gesendet werden an $customerEmail");
        // TODO: Retry-Mechanismus oder Admin-Benachrichtigung
    }
}
```

### 3.5 Verify Endpoint

**`api/verify.php`**

```php
<?php
/**
 * POST /api/verify.php
 * Verifiziert einen Lizenzschlüssel
 * 
 * Request:  { "license_key": "XXXX-XXXX-XXXX-XXXX" }
 * Response: { "valid": true, "email": "...", "expires": "2027-03-12", "product": "pro" }
 */

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/LicenseManager.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$config = require __DIR__ . '/includes/config.php';
$input = json_decode(file_get_contents('php://input'), true);
$licenseKey = $input['license_key'] ?? '';

if (empty($licenseKey)) {
    http_response_code(400);
    echo json_encode(['valid' => false, 'error' => 'Lizenzschlüssel fehlt']);
    exit;
}

// Format validieren (XXXX-XXXX-XXXX-XXXX)
if (!preg_match('/^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/', $licenseKey)) {
    http_response_code(400);
    echo json_encode(['valid' => false, 'error' => 'Ungültiges Lizenzformat']);
    exit;
}

$licenseManager = new LicenseManager($config);
$result = $licenseManager->verifyLicense($licenseKey);

echo json_encode($result);
```

### 3.6 Activate Endpoint

**`api/activate.php`**

```php
<?php
/**
 * POST /api/activate.php
 * Aktiviert eine Lizenz mit Machine-ID
 * 
 * Request:  { "license_key": "XXXX-XXXX-XXXX-XXXX", "machine_id": "..." }
 * Response: { "success": true, "message": "Lizenz aktiviert", "expires": "2027-03-12" }
 */

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/LicenseManager.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$config = require __DIR__ . '/includes/config.php';
$input = json_decode(file_get_contents('php://input'), true);

$licenseKey = $input['license_key'] ?? '';
$machineId = $input['machine_id'] ?? '';

if (empty($licenseKey)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Lizenzschlüssel fehlt']);
    exit;
}

$licenseManager = new LicenseManager($config);
$result = $licenseManager->activateLicense($licenseKey, $machineId);

if ($result['valid'] ?? $result['success'] ?? false) {
    echo json_encode($result);
} else {
    http_response_code(400);
    echo json_encode($result);
}
```

### 3.7 .htaccess (Sicherheit)

**`api/.htaccess`**

```apache
# ═══════════════════════════════════════════════════════════════════
# Sicherheits-Konfiguration für /api
# ═══════════════════════════════════════════════════════════════════

# PHP-Fehler nicht anzeigen (nur loggen)
php_flag display_errors Off
php_flag log_errors On

# Verzeichnis-Listing deaktivieren
Options -Indexes

# Zugriff auf sensible Dateien verbieten
<FilesMatch "^(config\.php|\.htaccess|\.env)$">
    Order allow,deny
    Deny from all
</FilesMatch>

# Zugriff auf includes-Ordner verbieten
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteRule ^includes/ - [F,L]
    RewriteRule ^data/ - [F,L]
    RewriteRule ^logs/ - [F,L]
    RewriteRule ^vendor/ - [F,L]
</IfModule>

# CORS Headers (falls nicht in PHP gesetzt)
<IfModule mod_headers.c>
    Header always set Access-Control-Allow-Origin "*"
    Header always set Access-Control-Allow-Methods "POST, OPTIONS"
    Header always set Access-Control-Allow-Headers "Content-Type"
</IfModule>
```

---

## 4. Composer für Stripe SDK

**`api/composer.json`**

```json
{
    "name": "obscuras/license-api",
    "description": "License Server API for Obscuras Campaign Manager",
    "require": {
        "php": ">=7.4",
        "stripe/stripe-php": "^14.0",
        "phpmailer/phpmailer": "^6.9"
    },
    "config": {
        "vendor-dir": "vendor"
    }
}
```

**Installation:**
```bash
cd mailer-campaigner.de/api
composer install
```

---

## 5. Stripe Webhook einrichten

1. Gehe zu https://dashboard.stripe.com/webhooks
2. Klicke **"+ Add endpoint"**
3. Endpoint URL: `https://mailer-campaigner.de/api/webhook.php`
4. Events auswählen:
   - `checkout.session.completed`
   - `payment_intent.succeeded` (optional)
5. Nach dem Erstellen: Kopiere das **"Signing secret"** (beginnt mit `whsec_`)
6. Füge es in `config.php` unter `webhook_secret` ein

---

## 6. Plesk-spezifische Einrichtung

### Ordner-Berechtigungen
```bash
chmod 755 api/
chmod 644 api/*.php
chmod 755 api/includes/
chmod 600 api/includes/config.php  # Wichtig: Nur lesbar für PHP
chmod 755 api/data/
chmod 755 api/logs/
```

### PHP-Version
Stelle sicher, dass PHP 7.4+ oder 8.x in Plesk ausgewählt ist.

### SSL
Die API muss über HTTPS erreichbar sein (für Stripe-Webhooks Pflicht).

---

## 7. Angular Success-Page

Erstelle eine Success-Page, die nach erfolgreicher Zahlung angezeigt wird:

**`src/app/pages/payment/success/success.component.ts`**

```typescript
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-payment-success',
  template: `
    <div class="success-container">
      <div class="success-icon">✓</div>
      <h1>Zahlung erfolgreich!</h1>
      <p>Vielen Dank für deinen Kauf.</p>
      <p>Dein Lizenzschlüssel wird in wenigen Minuten per E-Mail zugestellt.</p>
      <div class="info-box">
        <p>📧 Prüfe deinen Posteingang (auch den Spam-Ordner)</p>
        <p>📥 <a href="/download">Software herunterladen</a></p>
      </div>
    </div>
  `,
  styles: [`
    .success-container { max-width: 600px; margin: 100px auto; text-align: center; padding: 40px; }
    .success-icon { font-size: 80px; color: #22c55e; margin-bottom: 20px; }
    h1 { color: #fafafa; }
    p { color: #a1a1aa; }
    .info-box { background: #18181b; border-radius: 12px; padding: 24px; margin-top: 32px; }
    a { color: #22c55e; }
  `]
})
export class PaymentSuccessComponent implements OnInit {
  sessionId: string | null = null;
  
  constructor(private route: ActivatedRoute) {}
  
  ngOnInit() {
    this.sessionId = this.route.snapshot.queryParamMap.get('session_id');
  }
}
```

---

## 8. Desktop-App anpassen

Nach der API-Einrichtung muss `stripe_service.py` angepasst werden, um die Server-API zu nutzen statt direkt Stripe aufzurufen. Dies ist der nächste Schritt.

---

## Checkliste

- [ ] `/api` Ordner in Angular-Projekt erstellt
- [ ] `composer install` im `/api` Ordner ausgeführt
- [ ] `config.php` mit echten Keys befüllt
- [ ] Stripe Webhook registriert
- [ ] `.htaccess` konfiguriert
- [ ] SMTP-Zugangsdaten eingetragen
- [ ] Ordner-Berechtigungen gesetzt
- [ ] Success-Page in Angular erstellt
- [ ] Test-Checkout durchgeführt

---

## Test

```bash
# Checkout testen
curl -X POST https://mailer-campaigner.de/api/checkout.php \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Verify testen (nach Kauf)
curl -X POST https://mailer-campaigner.de/api/verify.php \
  -H "Content-Type: application/json" \
  -d '{"license_key":"XXXX-XXXX-XXXX-XXXX"}'
```

---

**Nächster Schritt:** Desktop-App (`stripe_service.py`) anpassen, um diese API zu nutzen.
