from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os, hashlib
from functools import wraps
from database import get_db, init_db
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "placement_cell_secret_2024"
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

# ─── Helper: run query and fetch results ─────────────────────────────────────
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
    """Fetch a single scalar value."""
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    c.close()
    if row is None:
        return None
    return list(row.values())[0]

# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = hash_password(request.form['password'])
        conn = get_db()
        user = db_fetchone(conn, "SELECT * FROM users WHERE email=%s AND password=%s AND is_active=1", (email, password))
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['role']    = user['role']
            session['email']   = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip()
        password = hash_password(request.form['password'])
        role     = request.form['role']
        conn = get_db()
        try:
            c = conn.cursor()
            # Insert user and get new id
            c.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) RETURNING id",
                (name, email, password, role)
            )
            user_id = c.fetchone()['id']

            if role == 'student':
                roll   = request.form.get('roll_number', '')
                branch = request.form.get('branch', '')
                year   = request.form.get('year', 1)
                c.execute(
                    "INSERT INTO student_profiles (user_id, roll_number, branch, year) VALUES (%s,%s,%s,%s)",
                    (user_id, roll, branch, year)
                )
            elif role == 'company':
                cname = request.form.get('company_name', name)
                c.execute(
                    "INSERT INTO company_profiles (user_id, company_name) VALUES (%s,%s)",
                    (user_id, cname)
                )
            c.close()
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ─── Dashboard ────────────────────────────────────────────────────────────────
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

# ─── Student Routes ───────────────────────────────────────────────────────────
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    conn = get_db()
    profile = db_fetchone(conn, "SELECT * FROM student_profiles WHERE user_id=%s", (session['user_id'],))
    applications = []
    if profile:
        applications = db_fetchall(conn, """
            SELECT a.*, j.title, j.job_type, j.location, j.salary, cp.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN company_profiles cp ON j.company_id = cp.id
            WHERE a.student_id = %s
            ORDER BY a.applied_at DESC
        """, (profile['id'],))
    stats = {
        'total':       len(applications),
        'shortlisted': sum(1 for a in applications if a['status'] == 'shortlisted'),
        'selected':    sum(1 for a in applications if a['status'] in ('selected', 'offered')),
        'rejected':    sum(1 for a in applications if a['status'] == 'rejected'),
    }
    conn.close()
    return render_template('student/dashboard.html', profile=profile, applications=applications, stats=stats)

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_profile():
    conn = get_db()
    if request.method == 'POST':
        fields = ['branch', 'year', 'cgpa', 'skills', 'phone', 'linkedin', 'github', 'bio', 'roll_number']
        values = {f: request.form.get(f, '') for f in fields}
        resume_path = None
        if 'resume' in request.files:
            f = request.files['resume']
            if f and allowed_file(f.filename):
                filename = secure_filename(f"resume_{session['user_id']}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resume_path = filename

        existing = db_fetchone(conn, "SELECT * FROM student_profiles WHERE user_id=%s", (session['user_id'],))
        if existing:
            if resume_path:
                db_execute(conn, """
                    UPDATE student_profiles
                    SET roll_number=%s, branch=%s, year=%s, cgpa=%s, skills=%s,
                        phone=%s, linkedin=%s, github=%s, bio=%s, resume_path=%s
                    WHERE user_id=%s
                """, (values['roll_number'], values['branch'], values['year'], values['cgpa'],
                      values['skills'], values['phone'], values['linkedin'], values['github'],
                      values['bio'], resume_path, session['user_id']))
            else:
                db_execute(conn, """
                    UPDATE student_profiles
                    SET roll_number=%s, branch=%s, year=%s, cgpa=%s, skills=%s,
                        phone=%s, linkedin=%s, github=%s, bio=%s
                    WHERE user_id=%s
                """, (values['roll_number'], values['branch'], values['year'], values['cgpa'],
                      values['skills'], values['phone'], values['linkedin'], values['github'],
                      values['bio'], session['user_id']))
        conn.commit()
        flash('Profile updated!', 'success')
        conn.close()
        return redirect(url_for('student_profile'))

    profile = db_fetchone(conn, """
        SELECT sp.*, u.name, u.email
        FROM student_profiles sp
        JOIN users u ON sp.user_id = u.id
        WHERE sp.user_id = %s
    """, (session['user_id'],))
    conn.close()
    return render_template('student/profile.html', profile=profile)

@app.route('/student/jobs')
@login_required
@role_required('student')
def student_jobs():
    conn = get_db()
    profile     = db_fetchone(conn, "SELECT * FROM student_profiles WHERE user_id=%s", (session['user_id'],))
    filter_type = request.args.get('type', 'all')
    student_id  = profile['id'] if profile else 0

    query = """
        SELECT j.*, cp.company_name, cp.industry,
            (SELECT COUNT(*) FROM applications WHERE job_id = j.id) AS applicant_count,
            (SELECT id FROM applications WHERE job_id = j.id AND student_id = %s) AS applied
        FROM jobs j
        JOIN company_profiles cp ON j.company_id = cp.id
        WHERE j.is_active = 1
    """
    params = [student_id]
    if filter_type in ('fulltime', 'internship'):
        query += " AND j.job_type = %s"
        params.append(filter_type)
    query += " ORDER BY j.created_at DESC"

    jobs = db_fetchall(conn, query, params)
    conn.close()
    return render_template('student/jobs.html', jobs=jobs, filter_type=filter_type)

@app.route('/student/apply/<int:job_id>', methods=['POST'])
@login_required
@role_required('student')
def apply_job(job_id):
    conn = get_db()
    profile = db_fetchone(conn, "SELECT * FROM student_profiles WHERE user_id=%s", (session['user_id'],))
    if not profile:
        flash('Complete your profile first.', 'warning')
        conn.close()
        return redirect(url_for('student_profile'))

    job = db_fetchone(conn, "SELECT * FROM jobs WHERE id=%s AND is_active=1", (job_id,))
    if not job:
        flash('Job not found.', 'danger')
        conn.close()
        return redirect(url_for('student_jobs'))

    if job['cgpa_cutoff'] and profile['cgpa'] and float(profile['cgpa']) < float(job['cgpa_cutoff']):
        flash(f'CGPA requirement is {job["cgpa_cutoff"]}. You are not eligible.', 'warning')
        conn.close()
        return redirect(url_for('student_jobs'))

    try:
        db_execute(conn, "INSERT INTO applications (job_id, student_id) VALUES (%s,%s)", (job_id, profile['id']))
        conn.commit()
        flash('Application submitted!', 'success')
    except Exception:
        conn.rollback()
        flash('Already applied to this job.', 'info')
    finally:
        conn.close()
    return redirect(url_for('student_jobs'))

# ─── Company Routes ───────────────────────────────────────────────────────────
@app.route('/company/dashboard')
@login_required
@role_required('company')
def company_dashboard():
    conn = get_db()
    cp   = db_fetchone(conn, "SELECT * FROM company_profiles WHERE user_id=%s", (session['user_id'],))
    jobs = []
    if cp:
        jobs = db_fetchall(conn, """
            SELECT j.*,
                (SELECT COUNT(*) FROM applications WHERE job_id = j.id) AS applicant_count
            FROM jobs j
            WHERE j.company_id = %s
            ORDER BY j.created_at DESC
        """, (cp['id'],))
    stats = {
        'total_jobs':         len(jobs),
        'active_jobs':        sum(1 for j in jobs if j['is_active']),
        'total_applications': sum(j['applicant_count'] for j in jobs),
    }
    conn.close()
    return render_template('company/dashboard.html', profile=cp, jobs=jobs, stats=stats)

@app.route('/company/profile', methods=['GET', 'POST'])
@login_required
@role_required('company')
def company_profile():
    conn = get_db()
    if request.method == 'POST':
        fields = ['company_name', 'industry', 'website', 'description', 'hr_contact', 'hr_phone']
        vals   = {f: request.form.get(f, '') for f in fields}
        db_execute(conn, """
            UPDATE company_profiles
            SET company_name=%s, industry=%s, website=%s, description=%s, hr_contact=%s, hr_phone=%s
            WHERE user_id=%s
        """, (vals['company_name'], vals['industry'], vals['website'], vals['description'],
              vals['hr_contact'], vals['hr_phone'], session['user_id']))
        conn.commit()
        flash('Profile updated!', 'success')
        conn.close()
        return redirect(url_for('company_profile'))

    cp = db_fetchone(conn, """
        SELECT cp.*, u.name, u.email
        FROM company_profiles cp
        JOIN users u ON cp.user_id = u.id
        WHERE cp.user_id = %s
    """, (session['user_id'],))
    conn.close()
    return render_template('company/profile.html', profile=cp)

@app.route('/company/jobs/post', methods=['GET', 'POST'])
@login_required
@role_required('company')
def post_job():
    conn = get_db()
    cp   = db_fetchone(conn, "SELECT * FROM company_profiles WHERE user_id=%s", (session['user_id'],))
    if request.method == 'POST':
        db_execute(conn, """
            INSERT INTO jobs
                (company_id, title, description, requirements, job_type, location, salary, cgpa_cutoff, deadline)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (cp['id'],
              request.form['title'],
              request.form['description'],
              request.form.get('requirements', ''),
              request.form['job_type'],
              request.form.get('location', ''),
              request.form.get('salary', ''),
              request.form.get('cgpa_cutoff', 0),
              request.form.get('deadline', '')))
        conn.commit()
        flash('Job posted successfully!', 'success')
        conn.close()
        return redirect(url_for('company_dashboard'))
    conn.close()
    return render_template('company/post_job.html')

@app.route('/company/jobs/<int:job_id>/applicants')
@login_required
@role_required('company')
def job_applicants(job_id):
    conn = get_db()
    cp   = db_fetchone(conn, "SELECT * FROM company_profiles WHERE user_id=%s", (session['user_id'],))
    job  = db_fetchone(conn, "SELECT * FROM jobs WHERE id=%s AND company_id=%s", (job_id, cp['id']))
    if not job:
        flash('Job not found.', 'danger')
        conn.close()
        return redirect(url_for('company_dashboard'))

    applicants = db_fetchall(conn, """
        SELECT a.*, sp.cgpa, sp.branch, sp.year, sp.skills, sp.resume_path, sp.phone,
               u.name, u.email
        FROM applications a
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        WHERE a.job_id = %s
        ORDER BY a.applied_at DESC
    """, (job_id,))
    conn.close()
    return render_template('company/applicants.html', job=job, applicants=applicants)

@app.route('/company/applications/<int:app_id>/status', methods=['POST'])
@login_required
@role_required('company')
def update_application_status(app_id):
    status = request.form['status']
    notes  = request.form.get('notes', '')
    conn   = get_db()
    db_execute(conn, "UPDATE applications SET status=%s, notes=%s WHERE id=%s", (status, notes, app_id))
    if status in ('selected', 'offered'):
        app_row = db_fetchone(conn, "SELECT student_id FROM applications WHERE id=%s", (app_id,))
        if app_row:
            db_execute(conn, "UPDATE student_profiles SET is_placed=1 WHERE id=%s", (app_row['student_id'],))
    conn.commit()
    conn.close()
    flash('Application status updated.', 'success')
    return redirect(request.referrer or url_for('company_dashboard'))

@app.route('/company/jobs/<int:job_id>/toggle', methods=['POST'])
@login_required
@role_required('company')
def toggle_job(job_id):
    conn = get_db()
    db_execute(conn, "UPDATE jobs SET is_active = 1 - is_active WHERE id=%s", (job_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('company_dashboard'))

# ─── Admin Routes ─────────────────────────────────────────────────────────────
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_db()
    stats = {
        'total_students':     db_fetchval(conn, "SELECT COUNT(*) FROM users WHERE role='student'"),
        'total_companies':    db_fetchval(conn, "SELECT COUNT(*) FROM users WHERE role='company'"),
        'total_jobs':         db_fetchval(conn, "SELECT COUNT(*) FROM jobs"),
        'active_jobs':        db_fetchval(conn, "SELECT COUNT(*) FROM jobs WHERE is_active=1"),
        'total_applications': db_fetchval(conn, "SELECT COUNT(*) FROM applications"),
        'placed_students':    db_fetchval(conn, "SELECT COUNT(*) FROM student_profiles WHERE is_placed=1"),
    }
    recent_applications = db_fetchall(conn, """
        SELECT a.*, j.title, cp.company_name, u.name AS student_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN company_profiles cp ON j.company_id = cp.id
        JOIN student_profiles sp ON a.student_id = sp.id
        JOIN users u ON sp.user_id = u.id
        ORDER BY a.applied_at DESC
        LIMIT 10
    """)
    conn.close()
    return render_template('admin/dashboard.html', stats=stats, recent_applications=recent_applications)

@app.route('/admin/students')
@login_required
@role_required('admin')
def admin_students():
    conn = get_db()
    students = db_fetchall(conn, """
        SELECT u.*, sp.cgpa, sp.branch, sp.year, sp.is_placed,
               (SELECT COUNT(*) FROM applications WHERE student_id = sp.id) AS app_count
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        WHERE u.role = 'student'
        ORDER BY u.created_at DESC
    """)
    conn.close()
    return render_template('admin/students.html', students=students)

@app.route('/admin/companies')
@login_required
@role_required('admin')
def admin_companies():
    conn = get_db()
    companies = db_fetchall(conn, """
        SELECT u.*, cp.company_name, cp.industry,
               (SELECT COUNT(*) FROM jobs WHERE company_id = cp.id) AS job_count
        FROM users u
        LEFT JOIN company_profiles cp ON u.id = cp.user_id
        WHERE u.role = 'company'
        ORDER BY u.created_at DESC
    """)
    conn.close()
    return render_template('admin/companies.html', companies=companies)

@app.route('/admin/jobs')
@login_required
@role_required('admin')
def admin_jobs():
    conn = get_db()
    jobs = db_fetchall(conn, """
        SELECT j.*, cp.company_name,
               (SELECT COUNT(*) FROM applications WHERE job_id = j.id) AS applicant_count
        FROM jobs j
        JOIN company_profiles cp ON j.company_id = cp.id
        ORDER BY j.created_at DESC
    """)
    conn.close()
    return render_template('admin/jobs.html', jobs=jobs)

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    conn = get_db()
    db_execute(conn, "UPDATE users SET is_active = 1 - is_active WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/resume/<filename>')
@login_required
def serve_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)