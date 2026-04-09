```python
import psycopg2
import psycopg2.extras
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Optional helper if you want dict cursor
def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ⚠️ RUN THIS ONLY MANUALLY (LOCAL SETUP)
def init_db():
    conn = get_db()
    c = get_cursor(conn)

    # ⚠️ WARNING: Drops all tables
    confirm = input("⚠️ This will DELETE all data. Type 'YES' to continue: ")
    if confirm != "YES":
        print("❌ Cancelled")
        return

    # Drop tables
    c.execute('DROP TABLE IF EXISTS interviews CASCADE')
    c.execute('DROP TABLE IF EXISTS applications CASCADE')
    c.execute('DROP TABLE IF EXISTS jobs CASCADE')
    c.execute('DROP TABLE IF EXISTS company_profiles CASCADE')
    c.execute('DROP TABLE IF EXISTS student_profiles CASCADE')
    c.execute('DROP TABLE IF EXISTS users CASCADE')

    # Users
    c.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('student','company','admin')),
            created_at TIMESTAMP DEFAULT NOW(),
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Student profiles
    c.execute('''
        CREATE TABLE student_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
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
            is_placed INTEGER DEFAULT 0
        )
    ''')

    # Company profiles
    c.execute('''
        CREATE TABLE company_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            company_name TEXT NOT NULL,
            industry TEXT,
            website TEXT,
            description TEXT,
            hr_contact TEXT,
            hr_phone TEXT
        )
    ''')

    # Jobs
    c.execute('''
        CREATE TABLE jobs (
            id SERIAL PRIMARY KEY,
            company_id INTEGER REFERENCES company_profiles(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            job_type TEXT CHECK(job_type IN ('fulltime','internship')),
            location TEXT,
            salary TEXT,
            cgpa_cutoff REAL DEFAULT 0,
            deadline TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Applications
    c.execute('''
        CREATE TABLE applications (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            student_id INTEGER REFERENCES student_profiles(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'applied',
            applied_at TIMESTAMP DEFAULT NOW(),
            notes TEXT,
            UNIQUE(job_id, student_id)
        )
    ''')

    # Interviews
    c.execute('''
        CREATE TABLE interviews (
            id SERIAL PRIMARY KEY,
            application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
            scheduled_at TEXT,
            venue TEXT,
            mode TEXT CHECK(mode IN ('online','offline')),
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized safely!")


if __name__ == "__main__":
    init_db()
```
