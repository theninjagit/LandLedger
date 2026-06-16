# 🏛️ LandLedger
### PKI-Based Land Ownership & Property Transfer Verification

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run
python app.py

# 3. Open browser
http://127.0.0.1:5000
```

---

## Demo Walkthrough

### Step 1 — Register 3 accounts:
| Role | Email (example) | Password |
|------|----------------|----------|
| Land Owner (Seller) | seller@demo.com | test123 |
| Buyer | buyer@demo.com | test123 |
| Govt Officer | officer@demo.com | test123 |

### Step 2 — As Seller:
- Login → Dashboard → **Add Property**
- Fill in property details → SHA-256 hash is generated

### Step 3 — As Seller:
- Dashboard → **Transfer Property**
- Select property, enter buyer@demo.com
- System signs deed hash with seller's RSA key

### Step 4 — As Buyer:
- Login → Dashboard → **Sign Deed**
- Buyer counter-signs with their RSA key

### Step 5 — As Govt Officer:
- Login → Dashboard → **Verify & Approve**
- System verifies ALL signatures + X.509 certs
- Block is added to immutable ledger

### Step 6 — Verify:
- Go to /verify → paste deed hash → all green ✅

---

## Cryptography Used

| Concept | Implementation |
|---------|---------------|
| Certificate Authority | LandLedger CA (self-signed X.509) |
| User Certificates | X.509 v3, signed by CA |
| Key Algorithm | RSA-2048 |
| Signature Algorithm | RSA + SHA-256 (PKCS1v15) |
| Hash Function | SHA-256 (deed hash, block hash, property hash) |
| Blockchain | SHA-256 hash chaining |
| Storage | SQLite (dev) |
| Transport | Flask dev server (use HTTPS in production) |

---

## Project Structure

```
landledger/
├── app.py                 # Flask entry point
├── requirements.txt
├── pki/
│   └── ca.py             # LandLedger CA (X.509, RSA, signing)
├── database/
│   └── db.py             # SQLite schema & connection
├── routes/
│   ├── auth.py           # Register, login, logout
│   └── main.py           # Dashboard, property, transfer, ledger, verify
├── templates/            # Jinja2 HTML templates
├── static/
│   ├── css/main.css
│   └── js/main.js
└── certs/                # CA keys stored here (auto-generated)
```

---

## Teacher Notes (Keycloak + MinIO Integration)

Your teacher suggested:
- **Keycloak** → Replace auth_bp with Keycloak OIDC for identity management
- **MinIO** → Replace SQLite file storage with MinIO for encrypted deed documents

These are production-grade additions. The PKI/crypto core remains identical.
