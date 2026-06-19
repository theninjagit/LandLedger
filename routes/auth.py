import os, sys, datetime, uuid, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db
from pki.ca import ca
from pki.nid_service import verify_id, get_mock_citizens

auth_bp = Blueprint('auth', __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'nid_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def log_action(user_id, action, details=""):
    db = get_db()
    db.execute("INSERT INTO audit_logs (user_id,action,details) VALUES (?,?,?)",
               (user_id, action, details))
    db.commit(); db.close()


@auth_bp.route('/register', methods=['GET','POST'])
def register():
    mock_citizens = get_mock_citizens()

    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email     = request.form['email'].strip().lower()
        phone     = request.form['phone'].strip()
        password  = request.form['password']
        role      = request.form['role']
        id_type   = request.form.get('id_type', 'nid')
        id_number = request.form.get('id_number', '').strip()
        id_dob    = request.form.get('id_dob', '').strip()

        # ── Basic checks ─────────────────────────────────────────────
        if not full_name or not email or not password or not role:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html', mock=mock_citizens, form=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html', mock=mock_citizens, form=request.form)

        db = get_db()

        # ── Email uniqueness ─────────────────────────────────────────
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            flash('This email is already registered. Please login.', 'danger')
            db.close()
            return render_template('register.html', mock=mock_citizens, form=request.form)

        # ── Govt officer — internal verification, no ID needed ────────
        if role == 'govt_officer':
            id_type   = 'nid'
            id_number = f"GOVT-{uuid.uuid4().hex[:8].upper()}"
            nid_verified = 1
            nid_token    = f"GOVT-INTERNAL-{uuid.uuid4().hex}"
        else:
            # For PAN, phone IS the unique key — use it for duplicate check
            lookup_key = re.sub(r'\D','',phone) if id_type == 'pan' else id_number

            existing = db.execute(
                "SELECT id FROM users WHERE nid_number=?", (lookup_key,)
            ).fetchone()

            # ── Verify ID against mock database ───────────────────────
            result = verify_id(
                id_type    = id_type,
                id_number  = id_number,
                full_name  = full_name,
                mobile     = phone,
                dob        = id_dob if id_type == 'nid' else None,
                existing_id = existing
            )

            # Log attempt
            db.execute(
                "INSERT INTO nid_verification_log (nid_number,attempt_name,result,status) VALUES (?,?,?,?)",
                (lookup_key, full_name, result['message'], result['status'])
            )
            db.commit()

            if not result['verified']:
                flash(f'ID Verification Failed: {result["message"]}', 'danger')
                db.close()
                return render_template('register.html', mock=mock_citizens, form=request.form)

            nid_verified = 1
            nid_token    = result['token']
            # For PAN, store phone number as the stored ID (it's the unique identifier)
            if id_type == 'pan':
                id_number = re.sub(r'\D','',phone)

        # ── Handle photo upload ───────────────────────────────────────
        nid_photo_path = None
        if 'id_photo' in request.files:
            photo = request.files['id_photo']
            if photo and photo.filename:
                ext = photo.filename.rsplit('.', 1)[-1].lower()
                if ext in ('jpg','jpeg','png'):
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    photo.save(os.path.join(UPLOAD_FOLDER, filename))
                    nid_photo_path = filename

        # ── Save user to DB ──────────────────────────────────────────
        pw_hash = generate_password_hash(password)
        db.execute('''INSERT INTO users
            (full_name,email,phone,password_hash,role,id_type,
             nid_number,nid_dob,nid_verified,nid_verified_at,
             nid_verification_token,nid_photo_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (full_name, email, phone, pw_hash, role, id_type,
             id_number, (id_dob if id_type == 'nid' else None), nid_verified,
             datetime.datetime.utcnow().isoformat(),
             nid_token, nid_photo_path))
        db.commit()

        user_id = db.execute(
            "SELECT id FROM users WHERE email=?", (email,)
        ).fetchone()['id']

        # ── CA issues X.509 certificate ───────────────────────────────
        cert_data = ca.issue_certificate(full_name, email, role)
        db.execute('''UPDATE users SET
            private_key_pem=?,public_key_pem=?,cert_pem=?,
            cert_serial=?,cert_issued_at=? WHERE id=?''',
            (cert_data['private_key_pem'], cert_data['public_key_pem'],
             cert_data['cert_pem'], cert_data['serial_number'],
             datetime.datetime.utcnow().isoformat(), user_id))
        db.commit()

        log_action(user_id, 'USER_REGISTERED',
                   f"Role:{role}|ID:{id_type}:{id_number[:4]}****|Cert issued")
        db.close()

        flash('Registration successful! ID verified ✓  |  X.509 certificate issued ✓  |  You can now login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', mock=mock_citizens)


@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return render_template('login.html')
            session['user_id']      = user['id']
            session['user_name']    = user['full_name']
            session['user_role']    = user['role']
            session['user_email']   = user['email']
            session['nid_verified'] = bool(user['nid_verified'])
            log_action(user['id'], 'USER_LOGIN')
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        flash('Incorrect email or password.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        log_action(session['user_id'], 'USER_LOGOUT')
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
