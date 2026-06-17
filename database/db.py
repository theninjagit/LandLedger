import sqlite3, os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'landledger.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # ── users — NO role restriction, one person can have multiple roles ──
    # We handle this by allowing role = any string.
    # A "buyer" who wants to sell just re-registers... wait no:
    # Better: roles stored as comma-separated or we allow seller+buyer in one account.
    # Simplest fix: role column has NO CHECK constraint — any value allowed.
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        id_type TEXT DEFAULT 'nid',
        nid_number TEXT,
        nid_dob TEXT,
        nid_verified INTEGER DEFAULT 0,
        nid_verified_at TIMESTAMP,
        nid_verification_token TEXT,
        nid_photo_path TEXT,
        private_key_pem TEXT,
        public_key_pem TEXT,
        cert_pem TEXT,
        cert_serial TEXT,
        cert_issued_at TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_number TEXT UNIQUE NOT NULL,
        owner_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        district TEXT NOT NULL,
        area_sqft REAL NOT NULL,
        description TEXT,
        property_hash TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        buyer_id INTEGER NOT NULL,
        govt_officer_id INTEGER,
        deed_hash TEXT NOT NULL,
        seller_signature BLOB,
        buyer_signature BLOB,
        deed_data TEXT NOT NULL,
        status TEXT DEFAULT 'pending_buyer',
        rejection_reason TEXT,
        seller_nid TEXT, buyer_nid TEXT,
        seller_nid_verified INTEGER DEFAULT 0,
        buyer_nid_verified INTEGER DEFAULT 0,
        seller_cert_valid INTEGER, buyer_cert_valid INTEGER,
        seller_sig_valid INTEGER,  buyer_sig_valid INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        seller_signed_at TIMESTAMP,
        buyer_signed_at TIMESTAMP,
        approved_at TIMESTAMP,
        FOREIGN KEY(property_id) REFERENCES properties(id),
        FOREIGN KEY(seller_id)   REFERENCES users(id),
        FOREIGN KEY(buyer_id)    REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_index INTEGER NOT NULL,
        transfer_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        buyer_id INTEGER NOT NULL,
        deed_hash TEXT NOT NULL,
        block_hash TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(transfer_id) REFERENCES transfers(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS nid_verification_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        nid_number TEXT,
        attempt_name TEXT,
        result TEXT,
        status TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()

    # ── Create default admin account ──────────────────────────────────
    existing = conn.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if not existing:
        conn.execute('''INSERT INTO users
            (full_name,email,phone,password_hash,role,id_type,nid_number,nid_verified,is_active)
            VALUES (?,?,?,?,?,?,?,1,1)''',
            ('System Admin','admin@landledger.com','9800000000',
             generate_password_hash('admin123'),'admin','nid','ADMIN-000'))
        conn.commit()
    conn.close()
