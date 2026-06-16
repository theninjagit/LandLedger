import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask
from database.db import init_db
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.secret_key = 'landledger-secret-key-crypto-2024'
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n" + "="*55)
    print("  LandLedger — PKI Land Registry")
    print("  http://127.0.0.1:5000")
    print("  Admin: admin@landledger.com / admin123")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
