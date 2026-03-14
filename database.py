import psycopg2
import psycopg2.extras
import os
import hashlib

DATABASE_URL = os.environ.get("postgresql://postgres:Shree@030204@db.kxppkbfyatidwysixeox.supabase.co:5432/postgres")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN (\'student\',\'company\',\'admin\')),
            created_at TIMESTAMP DEFAULT NOW(),
            is_active INTEGER DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            roll_number TEXT UNIQUE,
            branch TEXT,
            year INTEGER,
            cgpa REAL,
            skills TEXT,
            phone TEXT,
            resume_path TEXT,
            linkedin TEXT,
            github TEXT,
            bio TEXT,
            is_placed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS company_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            industry TEXT,
            website TEXT,
            description TEXT,
            hr_contact TEXT,
            hr_phone TEXT,
            logo_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            company_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            job_type TEXT DEFAULT \'fulltime\' CHECK(job_type IN (\'fulltime\',\'internship\')),
            location TEXT,
            salary TEXT,
            cgpa_cutoff REAL DEFAULT 0.0,
            deadline TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY(company_id) REFERENCES company_profiles(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            job_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT \'applied\' CHECK(status IN (\'applied\',\'shortlisted\',\'rejected\',\'selected\',\'offered\')),
            applied_at TIMESTAMP DEFAULT NOW(),
            notes TEXT,
            UNIQUE(job_id, student_id),
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES student_profiles(id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            application_id INTEGER NOT NULL,
            scheduled_at TEXT,
            venue TEXT,
            mode TEXT DEFAULT \'offline\' CHECK(mode IN (\'online\',\'offline\')),
            notes TEXT,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        )
    ''')

    # Seed admin user
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    """, ("Admin", "admin@placement.edu", admin_pass, "admin"))

    conn.commit()
    c.close()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()