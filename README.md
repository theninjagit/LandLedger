# 🏛️ LandLedger
### PKI-Based Land Ownership & Property Transfer Verification

---

## Quick Start

<div align="center">

<img src="images/icons" width="100%" alt="LandLedger Banner">

# LandLedger

### PKI-Based Land Ownership Transfer System

A secure web application that uses **Public Key Infrastructure (PKI)** to make land ownership transfers verifiable, tamper-proof, and digitally signed.

<br>

<img src="https://img.shields.io/badge/Python-Flask-blue">
<img src="https://img.shields.io/badge/Cryptography-RSA%202048-green">
<img src="https://img.shields.io/badge/Database-SQLite-orange">
<img src="https://img.shields.io/badge/Security-PKI-red">

</div>

---

## Core Features

- Seller, Buyer, and Government Officer registration
- NID / PAN verification
- X.509 certificate generation
- Digital signature for land transfer
- Ownership transfer approval system
- SHA-256 ledger hash chain
- Audit log for every action

---

## Tech Stack

<div align="center">

<img src="https://img.shields.io/badge/Flask-3.0-black">
<img src="https://img.shields.io/badge/Python-3.x-blue">
<img src="https://img.shields.io/badge/SQLite-Database-lightgrey">
<img src="https://img.shields.io/badge/RSA-2048-red">
<img src="https://img.shields.io/badge/SHA--256-Ledger-green">

</div>

---

## How LandLedger Works

```mermaid
flowchart LR
    A[Seller Login] --> B[Create Transfer Request]
    B --> C[Seller Digital Signature]
    C --> D[Buyer Approval & Signature]
    D --> E[Certificate Verification]
    E --> F[Government Officer Approval]
    F --> G[Ownership Updated]
    G --> H[Hash Stored in Ledger]

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
