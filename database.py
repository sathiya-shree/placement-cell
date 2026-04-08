import psycopg2
import psycopg2.extras
import os
import hashlib
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Drop existing tables to recreate with proper types
    c.execute('DROP TABLE IF EXISTS interviews CASCADE')
    c.execute('DROP TABLE IF EXISTS applications CASCADE')
    c.execute('DROP TABLE IF EXISTS jobs CASCADE')
    c.execute('DROP TABLE IF EXISTS company_profiles CASCADE')
    c.execute('DROP TABLE IF EXISTS student_profiles CASCADE')
    c.execute('DROP TABLE IF EXISTS users CASCADE')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','company','admin')),
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
            job_type TEXT DEFAULT 'fulltime' CHECK(job_type IN ('fulltime','internship')),
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
            status TEXT DEFAULT 'applied' CHECK(status IN ('applied','shortlisted','rejected','selected','offered')),
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
            mode TEXT DEFAULT 'offline' CHECK(mode IN ('online','offline')),
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

    # Seed sample companies
    companies_data = [
        ("Google", "google@hiring.com", "Technology", "https://careers.google.com", "Leading technology company specializing in Internet-related services and products.", "Sarah Johnson", "+1-650-253-0000"),
        ("Microsoft", "microsoft@hiring.com", "Technology", "https://careers.microsoft.com", "Multinational technology corporation producing computer software, consumer electronics, and personal computers.", "Michael Chen", "+1-425-882-8080"),
        ("Amazon", "amazon@hiring.com", "E-commerce", "https://amazon.jobs", "American multinational technology company focusing on e-commerce, cloud computing, and artificial intelligence.", "Emily Rodriguez", "+1-206-266-1000"),
        ("Infosys", "infosys@hiring.com", "Consulting", "https://www.infosys.com/careers", "Global leader in next-generation digital services and consulting.", "Rajesh Kumar", "+91-80-2852-0261"),
        ("TCS", "tcs@hiring.com", "Consulting", "https://www.tcs.com/careers", "IT services, consulting and business solutions organization.", "Priya Sharma", "+91-22-6778-9595"),
        ("Wipro", "wipro@hiring.com", "Technology", "https://careers.wipro.com", "Leading global information technology, consulting and business process services company.", "Amit Patel", "+91-80-2844-0011"),
        ("Deloitte", "deloitte@hiring.com", "Consulting", "https://www2.deloitte.com/careers", "Multinational professional services network providing audit, consulting, and advisory services.", "Jennifer Williams", "+1-212-492-4000"),
        ("Accenture", "accenture@hiring.com", "Consulting", "https://www.accenture.com/careers", "Global professional services company providing strategy, consulting, and technology services.", "David Brown", "+1-877-889-9009"),
        ("Flipkart", "flipkart@hiring.com", "E-commerce", "https://www.flipkartcareers.com", "Leading Indian e-commerce company offering a wide range of products.", "Sneha Reddy", "+91-80-4719-8000"),
        ("Adobe", "adobe@hiring.com", "Technology", "https://www.adobe.com/careers", "American multinational computer software company creating creative and marketing software.", "Lisa Anderson", "+1-408-536-6000"),
    ]

    company_ids = {}
    for company_name, email, industry, website, description, hr_contact, hr_phone in companies_data:
        password = hashlib.sha256("password123".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (company_name, email, password, "company"))
        
        result = c.fetchone()
        if result:
            user_id = result['id']
            c.execute("""
                INSERT INTO company_profiles (user_id, company_name, industry, website, description, hr_contact, hr_phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, company_name, industry, website, description, hr_contact, hr_phone))
            company_ids[company_name] = c.fetchone()['id']

    # Seed sample students
    students_data = [
        ("Rahul Verma", "rahul.verma@college.edu", "21CS001", "Computer Science", 4, 8.7, "Python, Java, React, Node.js, SQL, Machine Learning", "+91-98765-43210", "https://linkedin.com/in/rahulverma", "https://github.com/rahulverma", "Passionate software developer with expertise in full-stack development and ML."),
        ("Priya Singh", "priya.singh@college.edu", "21CS002", "Computer Science", 4, 9.2, "Python, Django, PostgreSQL, AWS, Docker, Kubernetes", "+91-98765-43211", "https://linkedin.com/in/priyasingh", "https://github.com/priyasingh", "Cloud enthusiast and backend developer with strong problem-solving skills."),
        ("Arjun Patel", "arjun.patel@college.edu", "21IT001", "Information Technology", 4, 8.5, "React, Angular, TypeScript, CSS, UI/UX Design", "+91-98765-43212", "https://linkedin.com/in/arjunpatel", "https://github.com/arjunpatel", "Frontend developer with a keen eye for design and user experience."),
        ("Sneha Reddy", "sneha.reddy@college.edu", "21CS003", "Computer Science", 4, 8.9, "Data Science, Python, R, TensorFlow, Tableau, Power BI", "+91-98765-43213", "https://linkedin.com/in/snehareddy", "https://github.com/snehareddy", "Data science enthusiast with strong analytical and visualization skills."),
        ("Vikram Kumar", "vikram.kumar@college.edu", "21EC001", "Electronics", 4, 8.3, "C++, Embedded Systems, IoT, Arduino, MATLAB", "+91-98765-43214", "https://linkedin.com/in/vikramkumar", "https://github.com/vikramkumar", "Electronics engineer interested in IoT and embedded systems development."),
        ("Ananya Desai", "ananya.desai@college.edu", "21CS004", "Computer Science", 3, 8.6, "Java, Spring Boot, Microservices, MongoDB, Redis", "+91-98765-43215", "https://linkedin.com/in/ananya", "https://github.com/ananya", "Backend developer focused on building scalable microservices architecture."),
        ("Rohan Sharma", "rohan.sharma@college.edu", "21IT002", "Information Technology", 3, 7.8, "JavaScript, Vue.js, Firebase, Git, Agile", "+91-98765-43216", "https://linkedin.com/in/rohan", "https://github.com/rohan", "Web developer passionate about creating interactive user interfaces."),
        ("Kavya Nair", "kavya.nair@college.edu", "21CS005", "Computer Science", 4, 9.1, "Python, Machine Learning, Deep Learning, NLP, OpenCV", "+91-98765-43217", "https://linkedin.com/in/kavya", "https://github.com/kavya", "AI/ML researcher with focus on natural language processing and computer vision."),
        ("Aditya Joshi", "aditya.joshi@college.edu", "21ME001", "Mechanical", 4, 7.9, "AutoCAD, SolidWorks, ANSYS, Python, Data Analysis", "+91-98765-43218", "https://linkedin.com/in/aditya", "https://github.com/adityaj", "Mechanical engineer with interest in CAD design and engineering analytics."),
        ("Divya Iyer", "divya.iyer@college.edu", "21CS006", "Computer Science", 3, 8.4, "React Native, Flutter, Android, iOS, Mobile Development", "+91-98765-43219", "https://linkedin.com/in/divya", "https://github.com/divya", "Mobile app developer with experience in cross-platform development."),
    ]

    student_ids = {}
    for name, email, roll, branch, year, cgpa, skills, phone, linkedin, github, bio in students_data:
        password = hashlib.sha256("password123".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (name, email, password, "student"))
        
        result = c.fetchone()
        if result:
            user_id = result['id']
            c.execute("""
                INSERT INTO student_profiles (user_id, roll_number, branch, year, cgpa, skills, phone, linkedin, github, bio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, roll, branch, year, cgpa, skills, phone, linkedin, github, bio))
            student_ids[name] = c.fetchone()['id']

    # Seed sample jobs
    jobs_data = [
        ("Google", "Software Engineer", "Join our team to build the next generation of Google products. Work on large-scale distributed systems.", "BS in Computer Science or related field, Strong coding skills in Python/Java/C++, Experience with data structures and algorithms", "fulltime", "Bangalore, India", "₹18-25 LPA", 7.5, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")),
        ("Google", "Product Management Intern", "Learn product management from industry experts. Work on real products used by millions.", "Currently pursuing Bachelor's/Master's, Strong analytical skills, Passion for technology products", "internship", "Remote", "₹50,000/month", 7.0, (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")),
        ("Microsoft", "Cloud Solutions Engineer", "Help customers build innovative solutions on Azure. Work with cutting-edge cloud technologies.", "Knowledge of cloud platforms, Programming in C#/Python, Understanding of DevOps practices", "fulltime", "Hyderabad, India", "₹15-22 LPA", 7.5, (datetime.now() + timedelta(days=28)).strftime("%Y-%m-%d")),
        ("Microsoft", "Software Engineering Intern", "Contribute to Microsoft products used globally. Collaborate with talented engineers.", "Currently pursuing CS/IT degree, Strong programming fundamentals, Problem-solving skills", "internship", "Bangalore, India", "₹60,000/month", 7.0, (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")),
        ("Amazon", "SDE - Frontend", "Build customer-facing features for Amazon's e-commerce platform. Impact millions of users daily.", "Expertise in React/Angular, HTML/CSS/JavaScript, RESTful API integration", "fulltime", "Bangalore, India", "₹16-24 LPA", 7.0, (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")),
        ("Amazon", "Data Analyst", "Analyze data to drive business decisions. Work with large datasets and create insights.", "SQL expertise, Python/R for data analysis, Data visualization tools (Tableau/PowerBI)", "fulltime", "Hyderabad, India", "₹12-18 LPA", 7.5, (datetime.now() + timedelta(days=22)).strftime("%Y-%m-%d")),
        ("Infosys", "Systems Engineer", "Join our digital transformation team. Work on enterprise solutions for global clients.", "Any Engineering degree, Good communication skills, Willingness to learn new technologies", "fulltime", "Pune, India", "₹4-6 LPA", 6.5, (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d")),
        ("TCS", "Digital Associate", "Be part of TCS Digital transforming businesses worldwide with emerging technologies.", "Engineering/MCA degree, Programming knowledge, Team player", "fulltime", "Chennai, India", "₹3.5-5.5 LPA", 6.0, (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")),
        ("Wipro", "Project Engineer", "Work on innovative projects using AI, ML, and Cloud technologies.", "CS/IT/ECE degree, Programming skills in Java/Python, Analytical thinking", "fulltime", "Bangalore, India", "₹4-6.5 LPA", 6.5, (datetime.now() + timedelta(days=38)).strftime("%Y-%m-%d")),
        ("Deloitte", "Business Technology Analyst", "Solve complex business problems using technology. Work with Fortune 500 clients.", "Strong analytical skills, Technology interest, Consulting mindset", "fulltime", "Mumbai, India", "₹7-10 LPA", 7.0, (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")),
        ("Accenture", "Application Development Associate", "Develop applications for leading enterprises across industries.", "Engineering degree, Programming fundamentals, Problem-solving ability", "fulltime", "Bangalore, India", "₹4.5-6.5 LPA", 6.5, (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")),
        ("Flipkart", "SDE Intern", "Build features for India's leading e-commerce platform. Learn from experienced engineers.", "Pursuing CS/IT degree, Strong DSA knowledge, Object-oriented programming", "internship", "Bangalore, India", "₹45,000/month", 7.5, (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d")),
        ("Adobe", "Software Development Engineer", "Create amazing experiences with Adobe's creative tools used by millions worldwide.", "BS in CS or equivalent, C++/Java expertise, Graphics/UI programming knowledge", "fulltime", "Noida, India", "₹20-28 LPA", 8.0, (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")),
        ("Flipkart", "Product Analyst", "Drive product decisions with data. Work on improving user experience for millions.", "Data analysis skills, SQL proficiency, Product thinking", "fulltime", "Bangalore, India", "₹10-15 LPA", 7.0, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")),
        ("Wipro", "AI/ML Intern", "Work on machine learning projects. Gain hands-on experience with real-world data.", "Pursuing final year, Python/ML libraries, Mathematics foundation", "internship", "Hyderabad, India", "₹35,000/month", 7.0, (datetime.now() + timedelta(days=27)).strftime("%Y-%m-%d")),
    ]

    job_ids = []
    for company_name, title, desc, req, jtype, loc, sal, cgpa, deadline in jobs_data:
        if company_name in company_ids:
            c.execute("""
                INSERT INTO jobs (company_id, title, description, requirements, job_type, location, salary, cgpa_cutoff, deadline, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (company_ids[company_name], title, desc, req, jtype, loc, sal, cgpa, deadline, 1))
            job_ids.append(c.fetchone()['id'])

    # Seed sample applications with various statuses
    applications_data = [
        (0, "Rahul Verma", "applied"),
        (0, "Priya Singh", "shortlisted"),
        (1, "Rahul Verma", "applied"),
        (2, "Arjun Patel", "shortlisted"),
        (3, "Sneha Reddy", "applied"),
        (4, "Priya Singh", "selected"),
        (5, "Kavya Nair", "shortlisted"),
        (6, "Vikram Kumar", "applied"),
        (7, "Ananya Desai", "applied"),
        (8, "Rohan Sharma", "rejected"),
        (9, "Rahul Verma", "shortlisted"),
        (10, "Divya Iyer", "applied"),
        (11, "Sneha Reddy", "applied"),
        (12, "Priya Singh", "applied"),
        (13, "Kavya Nair", "offered"),
        (14, "Aditya Joshi", "applied"),
        (0, "Kavya Nair", "applied"),
        (2, "Rahul Verma", "applied"),
        (4, "Arjun Patel", "applied"),
        (5, "Divya Iyer", "shortlisted"),
        (6, "Sneha Reddy", "applied"),
        (8, "Ananya Desai", "shortlisted"),
        (10, "Rohan Sharma", "applied"),
        (12, "Aditya Joshi", "applied"),
    ]

    for job_idx, student_name, status in applications_data:
        if job_idx < len(job_ids) and student_name in student_ids:
            try:
                c.execute("""
                    INSERT INTO applications (job_id, student_id, status)
                    VALUES (%s, %s, %s)
                """, (job_ids[job_idx], student_ids[student_name], status))
            except:
                pass  # Skip if duplicate

    # Mark some students as placed
    c.execute("UPDATE student_profiles SET is_placed = 1 WHERE id IN (%s, %s)", 
              (student_ids.get("Priya Singh", 0), student_ids.get("Kavya Nair", 0)))

    conn.commit()
    c.close()
    conn.close()
    print("✅ Database initialized with sample data!")

if __name__ == "__main__":
    init_db()
