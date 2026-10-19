# TeamSphere — Student Project & Team Finder

A clean, accessible web portal built for the **Department of Information Technology** where students can create collaboration profiles, showcase projects, discover teammates with complementary technical skills, and send verified team-up requests. The portal also features **Faculty-Verified Hackathons & Capstone Challenges**, as well as a permanent searchable **Department Project Archive**.

---

## Technology Stack

* **Backend**: Python 3.10+ with Flask (Application Factory pattern & Blueprints).
* **Database**: SQLite (stored locally under `instance/teamsphere.db`).
* **ORM**: Flask-SQLAlchemy with SQLAlchemy connection listener enforcing `PRAGMA foreign_keys = ON`.
* **Authentication**: Flask-Login with Werkzeug password hashing and pre-login session clearing.
* **Security & Forms**: Flask-WTF (CSRF protection on all POST requests), Flask-Limiter (rate limiting), and safe local redirect handling.
* **Frontend**: Server-rendered Jinja templates, custom responsive Vanilla CSS (custom design system), and accessible Vanilla JavaScript (modals, toast alerts, skill chips).
* **Testing**: Pytest with test isolation guard against in-memory SQLite (`sqlite:///:memory:`).

---

## Core Features

1. **Department Portal & Navigation**:
   * Responsive navigation bar with mobile hamburger drawer.
   * Dynamic navigation links based on authentication state (Guest vs Student vs Faculty).
2. **Student Authentication & Privacy**:
   * Student registration strictly enforcing the `student` role.
   * Secure login with rate-limiting and generic failure messages.
   * Strict privacy: student email addresses and password hashes are never exposed.
3. **Student Collaboration Profiles**:
   * Profile creation and editing: department, year of study (1–6), bio (max 300 characters), skills chips, interests chips, and validated profile picture URL.
   * Public directory search via **Team Finder** (`/team-finder`).
4. **Project Management & Department Archive**:
   * Project publishing, editing, and deletion with strict owner permission checks (HTTP 403 enforcement).
   * Filter projects by Category (Hackathon, Academic, Personal, Research) and Status.
   * Permanent searchable **Archive** of completed projects.
5. **Verified Faculty Hackathons & Challenges**:
   * Dedicated CLI workflow (`flask create-faculty`) to provision verified professors and department mentors.
   * Official `★ Faculty Verified` badge on hackathons and capstone listings.
6. **Team-Up Requests & Atomic Acceptance**:
   * Students can send requests to join a project (recipient = project owner) or collaborate directly with another student.
   * Join requests can only be sent while a project status is `looking_for_teammates`.
   * Atomic accept transaction: adds the member to `project_members` and changes status to `accepted` in a single transaction with rollback safety.
   * Partial unique index preventing duplicate pending requests (`COALESCE(project_id, 0)`).

---

## Project Structure

```text
TeamSphere/
├── app.py                 # Application factory (create_app), CLI commands & server entry
├── config.py              # Environment configuration (Development, Testing, Production)
├── extensions.py          # SQLAlchemy, LoginManager, CSRFProtect, Limiter & SQLite listener
├── models.py              # Database schema (User, Project, Skill, Interest, TeamRequest, etc.)
├── forms.py               # WTForms definitions with validation rules
├── inspect_db.py          # CLI tool to inspect SQLite database tables
├── seed.py                # Database seed script for development/demo
├── requirements.txt       # Pinned dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore rules (excludes .env, *.db, venv/)
├── README.md              # Documentation
├── blueprints/
│   ├── main.py            # Landing page, dashboard, health check
│   ├── auth.py            # Register, login, logout
│   ├── profiles.py        # Profile view and edit
│   ├── projects.py        # Project browsing, detail, creation, editing, deletion
│   └── requests.py        # Team finder and request actions (accept/reject/cancel)
├── services/
│   ├── auth_service.py    # Authentication and registration business rules
│   └── request_service.py # Atomic request acceptance and status transition rules
├── utils/
│   └── validators.py      # Normalization helpers and open redirect validators
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Shared master layout with navbar and footer
│   ├── index.html         # Landing page with hero and recent projects
│   ├── register.html      # Student registration
│   ├── login.html         # Student/Faculty login
│   ├── dashboard.html     # Student personal dashboard
│   ├── profile.html       # Public profile view
│   ├── edit_profile.html  # Profile editing with chips
│   ├── projects.html      # Browse, search, filter projects and archive
│   ├── project_detail.html# Project view, team list, and join request modal
│   ├── create_project.html# Post and edit project form
│   ├── team_finder.html   # Student directory search
│   ├── requests.html      # Sent and received collaboration requests
│   └── errors/            # Custom 403, 404, 500 error templates
├── static/
│   ├── css/style.css      # Custom design system with CSS tokens and responsive rules
│   └── js/main.js         # Mobile nav, toasts, modals, character counter, chips
├── instance/              # SQLite database storage (teamsphere.db)
└── tests/
    ├── conftest.py        # Pytest fixtures and test database isolation guard
    ├── test_stage1_foundations.py
    ├── test_stage2_ui.py
    ├── test_stage3_auth.py
    └── test_stage4_faculty.py & test_stage4_profiles.py
```

---

## Local Development Setup

### 1. Clone the repository and enter the directory
```bash
git clone https://github.com/YOUR_USERNAME/TeamSphere.git
cd TeamSphere
```

### 2. Set up a Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
*(Optionally adjust `SECRET_KEY` or `ALLOWED_EMAIL_DOMAIN` if you wish to restrict registration to your university domain).*

### 5. Initialize the SQLite Database
```bash
flask --app app init-db
```

### 6. Create a Verified Faculty Account (Optional)
```bash
flask --app app create-faculty --name "Prof. Name" --email "faculty@college.edu" --dept "Department of Information Technology" --password "YourPassword123!"
```

### 7. Run the Application
```bash
python app.py
```
Open your browser to:
👉 **[http://127.0.0.1:5001/](http://127.0.0.1:5001/)**

*(Note: Port 5001 is used by default to prevent conflicts with macOS Monterey/Ventura/Sonoma/Sequoia AirPlay Receiver which uses port 5000).*

---

## Inspecting the SQLite Database

### Option A: Using the built-in terminal inspector
Run:
```bash
python inspect_db.py
```

### Option B: Using SQLite Command Line
```bash
sqlite3 -table instance/teamsphere.db "SELECT id, display_name, email, role, department FROM users;"
sqlite3 -table instance/teamsphere.db "SELECT id, title, category, status FROM projects;"
```

### Option C: Using "DB Browser for SQLite" (GUI)
1. Download and open [DB Browser for SQLite](https://sqlitebrowser.org/).
2. Click **Open Database** and select `instance/teamsphere.db`.
3. Click **Browse Data** to view and query any table.

---

## Running the Automated Test Suite

The test suite runs against an isolated, in-memory SQLite database (`sqlite:///:memory:`) and will fail immediately if pointed at development data.

Run all 28 tests with pytest:
```bash
pytest -v
```

---

## Future Deployment & PostgreSQL Considerations

TeamSphere uses SQLAlchemy ORM models, making a future transition to PostgreSQL straightforward. However, moving to PostgreSQL requires:
1. Configuring a managed PostgreSQL instance with persistent storage (local SQLite files are reset on ephemeral hosts like Render or Heroku).
2. Updating the database connection string in `.env` (`DATABASE_URL=postgresql://user:pass@host/dbname`).
3. Ensuring the SQLite `PRAGMA foreign_keys = ON` listener only runs when dialect is `sqlite3` (already implemented).
4. Ensuring partial unique index expressions (`postgresql_where`) are verified against your PostgreSQL version.
5. Case-insensitive search: TeamSphere uses `.ilike()` for PostgreSQL compatibility.

---

## License

Developed for the **Department of Information Technology**. Open-source under the MIT License.
