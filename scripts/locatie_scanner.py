"""
Locatie Scanner - Vaste artikellocaties toewijzen in RidderIQ
Open op telefoon via https://<pc-ip>:5050
"""

import datetime
import ipaddress
import logging
import os
import socket
import ssl

import pyodbc
from flask import Flask, request, jsonify, render_template_string

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("locatie_scanner")

app = Flask(__name__)

# --- Database ---
WAREHOUSE_CODE = "SPI"  # Ieper


def get_conn_str():
    """Return connection string — localhost when running on server, remote otherwise."""
    hostname = socket.gethostname().upper()
    if hostname == "VMSERVERRUM":
        server = "localhost\\RIDDERIQ"
    else:
        server = "10.0.1.5\\RIDDERIQ"
    return (
        "DRIVER={ODBC Driver 13 for SQL Server};"
        f"SERVER={server};"
        "DATABASE=Spinnekop Live 2;"
        "UID=ridderadmin;PWD=riad01*;"
        "Trusted_Connection=no;Connection Timeout=5;"
    )


def get_db():
    return pyodbc.connect(get_conn_str())


# --- SSL Certificate ---
def ensure_ssl_cert(cert_dir=None):
    """Generate self-signed SSL certificate if not present. Returns (cert_path, key_path)."""
    if cert_dir is None:
        cert_dir = os.path.dirname(os.path.abspath(__file__))

    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")

    if os.path.exists(cert_path) and os.path.exists(key_path):
        log.info("Using existing SSL cert: %s", cert_path)
        return cert_path, key_path

    log.info("Generating self-signed SSL certificate...")
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Generate RSA 2048-bit key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Spinnekop"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Locatie Scanner"),
    ])

    # SAN with IP and DNS names — critical for Chrome to accept the cert
    san = x509.SubjectAlternativeName([
        x509.IPAddress(ipaddress.IPv4Address("10.0.1.5")),
        x509.DNSName("VMSERVERRUM"),
        x509.DNSName("localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(san, critical=False)
        .sign(private_key, hashes.SHA256())
    )

    # Write key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Write cert
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    log.info("SSL certificate generated: %s", cert_path)
    return cert_path, key_path


# --- HTML (single page, mobile-first) ---
HTML = """
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Locatie Scanner</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', -apple-system, system-ui, sans-serif; background: #F8FAFC; padding: 16px; color: #334155; }
h1 { font-size: 20px; margin-bottom: 12px; color: #334155; }
.card { background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
label { font-size: 14px; font-weight: 600; color: #64748B; display: block; margin-bottom: 4px; }
input[type=text] { width: 100%; padding: 14px; font-size: 18px; border: 2px solid #CBD5E1; border-radius: 8px; font-family: 'Inter', sans-serif; color: #334155; transition: border-color 150ms ease; }
input[type=text]:focus { border-color: #F97316; outline: none; box-shadow: 0 0 0 3px rgba(249,115,22,0.15); }
.locked input { background: #F0FDF4; border-color: #4caf50; }
button { width: 100%; padding: 14px; font-size: 16px; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; margin-top: 8px; min-height: 44px; min-width: 44px; transition: all 150ms ease; font-family: 'Inter', sans-serif; }
button:active { transform: scale(0.97); }
.btn-lock { background: #F97316; color: white; }
.btn-lock:active { background: #EA580C; }
.btn-unlock { background: #64748B; color: white; }
.btn-unlock:active { background: #475569; }
.btn-scan { background: #64748B; color: white; font-size: 18px; padding: 16px; }
.btn-scan.active { background: #DC2626; }
.btn-save { background: #F97316; color: white; font-size: 18px; padding: 16px; }
.btn-save:disabled { background: #CBD5E1; color: #94A3B8; }
.status { padding: 10px; border-radius: 8px; margin-top: 8px; font-size: 14px; }
.status.ok { background: #F0FDF4; color: #16A34A; }
.status.err { background: #FEF2F2; color: #DC2626; }
.status.info { background: #FFF7ED; color: #EA580C; }
.log { margin-top: 8px; max-height: 300px; overflow-y: auto; }
.log-item { padding: 8px; border-bottom: 1px solid #F1F5F9; font-size: 14px; }
.log-item .code { font-weight: 700; font-size: 16px; color: #334155; }
.log-item .desc { color: #64748B; }
.count { font-size: 32px; font-weight: 700; color: #F97316; text-align: center; }
#artikelInput { font-size: 22px; text-align: center; letter-spacing: 2px; }
#scanner { width: 100%; margin-top: 8px; }
.input-row { display: flex; gap: 8px; align-items: stretch; }
.input-row input { flex: 1; }
.input-row button { width: auto; min-width: 60px; margin-top: 0; padding: 14px; }
.btn-mini-scan { background: #64748B; color: white; font-size: 20px; border-radius: 8px; border: none; cursor: pointer; min-height: 44px; min-width: 44px; transition: all 150ms ease; }
.btn-mini-scan:active { background: #475569; transform: scale(0.95); }
.wifi-bar { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
.wifi-bar.online { background: #F0FDF4; color: #16A34A; }
.wifi-bar.offline { background: #FEF2F2; color: #DC2626; }
.wifi-bar .dot { width: 10px; height: 10px; border-radius: 50%; }
.wifi-bar.online .dot { background: #16A34A; }
.wifi-bar.offline .dot { background: #DC2626; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.3; } }
.queue-badge { background: #F97316; color: white; border-radius: 12px; padding: 2px 8px; font-size: 12px; margin-left: auto; }
#scanCard { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 100; margin: 0; border-radius: 0; flex-direction: column; background: black; display: none; }
#scanCard.open { display: flex; }
#scanCard label { color: white; text-align: center; padding: 12px 16px; font-size: 18px; background: rgba(0,0,0,0.8); margin: 0; }
#scanner { flex: 1; min-height: 0; }
#scanCard button { border-radius: 0; margin: 0; flex-shrink: 0; padding: 18px; font-size: 20px; min-height: 56px; }
</style>
</head>
<body>

<div class="wifi-bar online" id="wifiBar">
  <span class="dot"></span>
  <span id="wifiText">Verbonden</span>
</div>
<h1>Locatie Scanner</h1>

<!-- Locatie -->
<div class="card" id="locCard">
  <label>Locatie (bv. SPI-C-04-02-01)</label>
  <div class="input-row">
    <input type="text" id="locInput" placeholder="Typ locatie of scan..."
           inputmode="text" autocomplete="off" autocapitalize="characters">
    <button class="btn-mini-scan" onclick="startScan('loc')">&#128247;</button>
  </div>
  <button class="btn-lock" id="locBtn" onclick="toggleLock()">Vergrendel locatie</button>
  <div id="locStatus"></div>
</div>

<!-- Artikel scan -->
<div class="card" id="artCard" style="display:none">
  <label>Scan artikelcode</label>
  <div class="input-row">
    <input type="text" id="artikelInput" placeholder="Typ of scan..."
           inputmode="text" autocomplete="off" autocapitalize="characters">
    <button class="btn-mini-scan" onclick="startScan('art')">&#128247;</button>
  </div>
  <button class="btn-save" id="saveBtn" onclick="saveArtikel()">Opslaan</button>
  <div id="artStatus"></div>
</div>

<!-- Camera scanner -->
<div id="scanCard">
  <label id="scanLabel">Camera scanner</label>
  <div id="scanner"></div>
  <button class="btn-scan active" onclick="stopScan()">Stop camera</button>
</div>

<!-- Resultaten -->
<div class="card" id="resultCard" style="display:none">
  <div class="count" id="scanCount">0</div>
  <label style="text-align:center">artikelen toegewezen</label>
  <div class="log" id="scanLog"></div>
</div>

<script>
let locked = false;
let locPK = null;
let whPK = null;
let count = 0;
let scanner = null;
let scanTarget = null; // 'loc' or 'art'
let scanning = false;
let isOnline = true;

const locInput = document.getElementById('locInput');
const artInput = document.getElementById('artikelInput');
const locBtn = document.getElementById('locBtn');

// --- Offline queue ---
function getQueue() {
  try { return JSON.parse(localStorage.getItem('scanQueue') || '[]'); } catch(e) { return []; }
}
function saveQueue(q) { localStorage.setItem('scanQueue', JSON.stringify(q)); updateQueueBadge(); }
function updateQueueBadge() {
  var q = getQueue();
  var bar = document.getElementById('wifiBar');
  var existing = document.getElementById('queueBadge');
  if (existing) existing.remove();
  if (q.length > 0) {
    var badge = document.createElement('span');
    badge.className = 'queue-badge';
    badge.id = 'queueBadge';
    badge.textContent = q.length + ' in wachtrij';
    bar.appendChild(badge);
  }
}
function setOnline(online) {
  isOnline = online;
  var bar = document.getElementById('wifiBar');
  var txt = document.getElementById('wifiText');
  bar.className = 'wifi-bar ' + (online ? 'online' : 'offline');
  txt.textContent = online ? 'Verbonden' : 'Geen verbinding';
  if (online) flushQueue();
}
async function flushQueue() {
  var q = getQueue();
  if (q.length === 0) return;
  var remaining = [];
  for (var i = 0; i < q.length; i++) {
    try {
      var res = await fetch('/api/toewijzen', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(q[i])
      });
      var data = await res.json();
      if (data.exists) {
        addLog(data.artikel || q[i].artikel_code, 'stond al op locatie');
      } else if (!data.error) {
        count++;
        document.getElementById('scanCount').textContent = count;
        addLog(data.artikel || q[i].artikel_code, (data.description || '') + ' (wachtrij)');
      } else {
        addLog(q[i].artikel_code, 'FOUT: ' + data.error);
      }
    } catch(e) {
      remaining.push(q[i]);
    }
  }
  saveQueue(remaining);
  if (remaining.length === 0) showStatus('artStatus', '✓ Wachtrij volledig verstuurd', 'ok');
}
// Check verbinding elke 5 sec
setInterval(function() {
  fetch('/api/ping', {method:'GET'}).then(function() { setOnline(true); }).catch(function() { setOnline(false); });
}, 5000);
window.addEventListener('online', function() { setOnline(true); });
window.addEventListener('offline', function() { setOnline(false); });
updateQueueBadge();

// Enter in locatie = vergrendel
locInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); toggleLock(); }
});

// Enter in artikel = opslaan
artInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); saveArtikel(); }
});

// --- Live camera barcode scanner ---
function startScan(target) {
  // Sluit virtueel toetsenbord door actief element te blurren
  if (document.activeElement) { document.activeElement.blur(); }

  scanTarget = target;
  var scanCard = document.getElementById('scanCard');
  var scannerDiv = document.getElementById('scanner');
  var label = document.getElementById('scanLabel');

  // Toon scanner als fullscreen overlay
  scanCard.classList.add('open');
  label.textContent = target === 'loc' ? 'Scan locatie-barcode...' : 'Scan artikel-barcode...';

  // Maak scanner div leeg
  scannerDiv.innerHTML = '';

  // Maak nieuwe scanner
  var qr = new Html5Qrcode("scanner");
  window._qr = qr;

  qr.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: { width: 200, height: 120 } },
    function(text) {
      // Barcode gevonden!
      qr.stop().then(function() {
        qr.clear();
        window._qr = null;
        scanCard.classList.remove('open');

        if (scanTarget === 'loc') {
          locInput.value = text.trim();
          toggleLock();
        } else {
          artInput.value = text.trim();
          showStatus('artStatus', 'Gescand: ' + text, 'info');
          saveArtikel();
          // Heropen voor volgende artikel
          setTimeout(function() { if (locked) startScan('art'); }, 1000);
        }
      });
    },
    function() {} // negeer mislukte frames
  ).catch(function(err) {
    alert('Camera fout: ' + err);
    scanCard.classList.remove('open');
  });
}

function stopScan() {
  var scanCard = document.getElementById('scanCard');
  scanCard.classList.remove('open');
  if (window._qr) {
    try { window._qr.stop().then(function() { window._qr.clear(); }); } catch(e) {}
    window._qr = null;
  }
}

async function toggleLock() {
  if (locked) {
    // Unlock
    locked = false;
    locInput.disabled = false;
    locInput.focus();
    document.getElementById('locCard').classList.remove('locked');
    locBtn.textContent = 'Vergrendel locatie';
    locBtn.className = 'btn-lock';
    document.getElementById('artCard').style.display = 'none';
    document.getElementById('locStatus').innerHTML = '';
    return;
  }

  const code = locInput.value.trim().toUpperCase();
  if (!code) return;

  // Auto-prefix: als ze bv "04-02-01" typen → SPI-C-04-02-01
  let lookupCode = code;
  if (/^\\d{2}-\\d{2}-\\d{2}$/.test(code)) {
    lookupCode = 'SPI-C-' + code;
    locInput.value = lookupCode;
  } else if (/^C-\\d{2}-\\d{2}-\\d{2}$/.test(code)) {
    lookupCode = 'SPI-' + code;
    locInput.value = lookupCode;
  }

  // Validate location
  const res = await fetch('/api/locatie?code=' + encodeURIComponent(lookupCode));
  const data = await res.json();

  if (data.error) {
    showStatus('locStatus', data.error, 'err');
    return;
  }

  locPK = data.pk_location;
  whPK = data.pk_warehouse;
  locked = true;
  locInput.disabled = true;
  document.getElementById('locCard').classList.add('locked');
  locBtn.textContent = 'Andere locatie kiezen';
  locBtn.className = 'btn-unlock';
  showStatus('locStatus', '✓ ' + data.description, 'ok');

  document.getElementById('artCard').style.display = 'block';
  document.getElementById('resultCard').style.display = 'block';
  artInput.value = '';
  artInput.focus();
}

async function saveArtikel() {
  const code = artInput.value.trim();
  if (!code || !locPK) return;

  var payload = { artikel_code: code, pk_location: locPK, pk_warehouse: whPK };
  document.getElementById('saveBtn').disabled = true;

  try {
    const res = await fetch('/api/toewijzen', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    document.getElementById('saveBtn').disabled = false;

    var loc = locInput.value.trim();
    if (data.error) {
      showStatus('artStatus', data.error, 'err');
    } else if (data.exists) {
      showStatus('artStatus', '⚠ ' + (data.artikel || code) + ' stond al op ' + loc, 'info');
    } else {
      count++;
      document.getElementById('scanCount').textContent = count;
      showStatus('artStatus', '✓ ' + (data.artikel || code) + ' → ' + loc + ' (' + data.description + ')', 'ok');
      addLog(data.artikel || code, loc + ' — ' + data.description);
    }
  } catch(e) {
    // Geen verbinding → in wachtrij
    document.getElementById('saveBtn').disabled = false;
    var q = getQueue();
    q.push(payload);
    saveQueue(q);
    setOnline(false);
    showStatus('artStatus', '⏳ ' + code + ' in wachtrij (wordt verstuurd bij verbinding)', 'info');
    addLog(code, 'wachtrij');
  }

  artInput.value = '';
  artInput.focus();
}

function showStatus(id, msg, type) {
  document.getElementById(id).innerHTML = '<div class="status ' + type + '">' + msg + '</div>';
}

function addLog(code, desc) {
  const log = document.getElementById('scanLog');
  log.innerHTML = '<div class="log-item"><span class="code">' + code + '</span> <span class="desc">' + desc + '</span></div>' + log.innerHTML;
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    resp = app.make_response(render_template_string(HTML))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route("/api/ping")
def api_ping():
    log.info("GET /api/ping -> ok")
    return jsonify(ok=True)


@app.route("/api/locatie")
def api_locatie():
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify(error="Geen locatiecode opgegeven")

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wl.PK_R_WAREHOUSELOCATION, wl.DESCRIPTION, w.PK_R_WAREHOUSE, w.CODE
            FROM R_WAREHOUSELOCATION wl
            JOIN R_WAREHOUSE w ON wl.FK_WAREHOUSE = w.PK_R_WAREHOUSE
            WHERE wl.CODE = ? AND w.CODE = ?
        """, code, WAREHOUSE_CODE)
        row = cursor.fetchone()
        conn.close()

        if not row:
            log.info("GET /api/locatie code=%s -> niet gevonden", code)
            return jsonify(error=f"Locatie '{code}' niet gevonden in magazijn {WAREHOUSE_CODE}")

        log.info("GET /api/locatie code=%s -> ok (%s)", code, row.DESCRIPTION)
        return jsonify(
            pk_location=row.PK_R_WAREHOUSELOCATION,
            pk_warehouse=row.PK_R_WAREHOUSE,
            description=row.DESCRIPTION,
            warehouse=row.CODE
        )
    except Exception as e:
        log.error("GET /api/locatie code=%s -> error: %s", code, e)
        return jsonify(error=str(e))


@app.route("/api/toewijzen", methods=["POST"])
def api_toewijzen():
    data = request.json
    artikel_code = data.get("artikel_code", "").strip()
    pk_loc = data.get("pk_location")
    pk_wh = data.get("pk_warehouse")

    if not artikel_code or not pk_loc or not pk_wh:
        return jsonify(error="Onvolledige data")

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Zoek artikel: barcode bevat PK_R_ITEM (numeriek), anders zoek op CODE
        if artikel_code.isdigit():
            cursor.execute(
                "SELECT PK_R_ITEM, CODE, DESCRIPTION FROM R_ITEM WHERE PK_R_ITEM = ?",
                int(artikel_code),
            )
        else:
            cursor.execute(
                "SELECT PK_R_ITEM, CODE, DESCRIPTION FROM R_ITEM WHERE CODE = ?",
                artikel_code,
            )
        item = cursor.fetchone()
        if not item:
            conn.close()
            return jsonify(error=f"Artikel '{artikel_code}' niet gevonden")

        artikel_code_display = item.CODE if hasattr(item, 'CODE') else artikel_code

        # Check of combinatie al bestaat
        cursor.execute("""
            SELECT PK_R_ITEMWAREHOUSELOCATION
            FROM R_ITEMWAREHOUSELOCATION
            WHERE FK_ITEM = ? AND FK_WAREHOUSELOCATION = ? AND FK_WAREHOUSE = ?
        """, item.PK_R_ITEM, pk_loc, pk_wh)

        if cursor.fetchone():
            conn.close()
            log.info("POST /api/toewijzen artikel=%s -> al toegewezen", artikel_code_display)
            return jsonify(exists=True, description=item.DESCRIPTION, artikel=artikel_code_display)

        # INSERT nieuwe vaste artikellocatie
        cursor.execute("""
            INSERT INTO R_ITEMWAREHOUSELOCATION
                (FK_ITEM, FK_WAREHOUSELOCATION, FK_WAREHOUSE, PREFERREDLOCATION,
                 CREATOR, DATECREATED, USERCHANGED, DATECHANGED)
            VALUES (?, ?, ?, 1, 'LOCATIESCANNER', GETDATE(), 'LOCATIESCANNER', GETDATE())
        """, item.PK_R_ITEM, pk_loc, pk_wh)
        conn.commit()
        conn.close()

        log.info("POST /api/toewijzen artikel=%s -> opgeslagen", artikel_code_display)
        return jsonify(
            ok=True,
            description=item.DESCRIPTION,
            artikel=artikel_code_display
        )
    except Exception as e:
        log.error("POST /api/toewijzen artikel=%s -> error: %s", artikel_code, e)
        return jsonify(error=str(e))


if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    conn_str = get_conn_str()
    server_mode = "SERVER (localhost)" if hostname.upper() == "VMSERVERRUM" else "REMOTE (10.0.1.5)"

    log.info("Starting Locatie Scanner — mode: %s", server_mode)

    # Generate or load SSL certificate
    cert_path, key_path = ensure_ssl_cert()
    log.info("SSL cert: %s", cert_path)

    print(f"\n{'='*50}")
    print(f"  Locatie Scanner draait! (HTTPS)")
    print(f"  Mode:     {server_mode}")
    print(f"  PC:       https://localhost:5050")
    print(f"  Telefoon: https://{local_ip}:5050")
    print(f"  SSL cert: {cert_path}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=5050, debug=False, ssl_context=(cert_path, key_path))
