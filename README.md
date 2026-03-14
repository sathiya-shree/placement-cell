# PlaceIT — Placement Cell Management System

A full-featured placement cell web application built with **Flask + SQLite**.

## Features

### 👩‍🎓 Students
- Register and login
- Complete profile (CGPA, branch, year, skills, bio, LinkedIn, GitHub)
- Upload resume (PDF/DOC)
- Browse and apply for jobs/internships
- Track application status in real-time
- Dashboard with placement stats

### 🏢 Companies
- Register and manage company profile
- Post full-time jobs & internships (with CGPA cutoff, deadline, salary)
- View all applicants per job
- Update applicant status (Applied → Shortlisted → Selected → Offered)
- Open/close job listings

### 🛡️ Admin
- Full placement statistics dashboard
- View all students, companies, and jobs
- Monitor placement rate
- Enable/disable users

## Tech Stack
- **Backend**: Flask (Python 3)
- **Database**: SQLite (via sqlite3)
- **Frontend**: Jinja2 templates, custom CSS (Syne + DM Sans fonts)
- **Auth**: Session-based with SHA-256 password hashing

## Setup & Run

### 1. Install dependencies
```bash
pip install flask
```

### 2. Run the application
```bash
cd placement_cell
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## Demo Credentials

| Role    | Email                    | Password  |
|---------|--------------------------|-----------|
| Admin   | admin@placement.edu      | admin123  |

Register new students and companies via the registration page.

## Project Structure
```
placement_cell/
├── app.py              # Main Flask application
├── database.py         # DB schema & initialization
├── placement.db        # SQLite database (auto-created)
├── static/
│   └── uploads/
│       └── resumes/    # Uploaded resume files
└── templates/
    ├── base.html       # Base layout
    ├── index.html      # Landing page
    ├── auth/           # Login, Register
    ├── student/        # Dashboard, Profile, Jobs
    ├── company/        # Dashboard, Post Job, Applicants
    └── admin/          # Dashboard, Students, Companies, Jobs
```

## Database Schema
- `users` — all users (student/company/admin)
- `student_profiles` — extended student info
- `company_profiles` — company details
- `jobs` — job/internship postings
- `applications` — student applications
- `interviews` — scheduled interviews
