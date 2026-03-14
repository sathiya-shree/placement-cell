# PlaceIT — Placement Cell Management System

A full-stack web application built for college placement cells to manage students, companies, job postings, and applications — all in one place.

🌐 **Live Demo:** [placement-cell-6b63.onrender.com](https://placement-cell-6b63.onrender.com)

---

## About

PlaceIT streamlines the entire campus placement process. Students can build profiles and apply for jobs, companies can post openings and manage applicants, and placement coordinators get a complete overview through the admin dashboard.

---

## Features

### 🎓 Students
- Register and build a detailed profile (CGPA, branch, skills, bio)
- Upload resume (PDF/DOC)
- Browse full-time jobs and internships
- Apply with one click
- Track application status in real-time (Applied → Shortlisted → Selected → Offered)

### 🏢 Companies
- Register and manage company profile
- Post job/internship listings with CGPA cutoff, salary, and deadline
- View and manage all applicants per job
- Update applicant status and add notes
- Open/close job listings

### 🛡️ Admin
- Overview dashboard with placement statistics
- Monitor placement rate, active jobs, total applications
- View and manage all students and companies
- Enable/disable user accounts

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | PostgreSQL (Supabase) |
| Frontend | Jinja2, HTML, CSS, JavaScript |
| Hosting | Render |
| Auth | Session-based with SHA-256 hashing |
| File Upload | Werkzeug |

---

## Project Structure

```
placement_cell/
├── app.py                  # Main Flask application & all routes
├── database.py             # DB connection & schema initialization
├── requirements.txt        # Python dependencies
├── Procfile                # Render start command
├── static/
│   └── uploads/
│       └── resumes/        # Uploaded student resumes
└── templates/
    ├── base.html           # Base layout with nav & styles
    ├── index.html          # Landing page
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── student/
    │   ├── dashboard.html
    │   ├── profile.html
    │   └── jobs.html
    ├── company/
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── post_job.html
    │   └── applicants.html
    └── admin/
        ├── dashboard.html
        ├── students.html
        ├── companies.html
        └── jobs.html
```

---

## Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/sathiya-shree/placement-cell.git
cd placement-cell
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variable
Create a `.env` file:
```
DATABASE_URL=postgresql://your_connection_string_here
```

### 4. Run the app
```bash
python app.py
```

Open `http://localhost:5000`

---

## Deployment

Hosted on **Render** with **Supabase PostgreSQL** as the database.

- Render auto-deploys on every push to `main`
- Database tables are created automatically on first startup via `init_db()`
- Environment variable `DATABASE_URL` is set in Render's dashboard

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@placement.edu | admin123 |

Register new student and company accounts via the `/register` page.

---

## Screenshots

> Landing page, student dashboard, job listings, company applicant management, admin overview

---

## License

MIT License — free to use and modify for educational purposes.
