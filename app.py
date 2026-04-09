```python
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
from functools import wraps
from database import get_db  # removed init_db
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 🔐 Use environment variable for secret key
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback_key")

# 🔧 Proxy fix for Nginx
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# 📁 Upload config
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return generate_password_hash(password)

# ─── Auth Decorators ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── DB Helpers ───────────────────────────────────────────────────────────────
def db_fetchone(conn, query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    c.close()
    return row

def db_fetchall(conn, query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    c.close()
    return rows

def db_execute(conn, query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    c.close()

def db_fetchval(conn, query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    c.close()
    if row is None:
        return None
    return list(row.values())[0]

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        conn = get_db()
        try:
            user = db_fetchone(conn, "SELECT * FROM users WHERE email=%s AND is_active=1", (email,))
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['role'] = user['role']
                session['email'] = user['email']
                flash(f'Welcome back, {user["name"]}!', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login error.', 'danger')
        finally:
            conn.close()
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = hash_password(request.form['password'])
        role = request.form['role']
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) RETURNING id",
                (name, email, password, role)
            )
            user_id = c.fetchone()['id']

            if role == 'student':
                c.execute(
                    "INSERT INTO student_profiles (user_id) VALUES (%s)",
                    (user_id,)
                )
            elif role == 'company':
                c.execute(
                    "INSERT INTO company_profiles (user_id, company_name) VALUES (%s,%s)",
                    (user_id, name)
                )

            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            print(e)
            flash('Registration error.', 'danger')
        finally:
            conn.close()
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['role']
    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'company':
        return redirect(url_for('company_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))

@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    conn = get_db()
    profile = db_fetchone(conn, "SELECT * FROM student_profiles WHERE user_id=%s", (session['user_id'],))
    conn.close()
    return render_template('student/dashboard.html', profile=profile)

@app.route('/resume/<filename>')
@login_required
def serve_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── Run (development only) ────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run()
```
