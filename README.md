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
   * Profile creation and editing: department, year of study (1–4), bio (max 300 characters), skills chips, and interests chips. Profiles use initials avatars and do not support profile pictures.
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
├── public/static/
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

### Prerequisites

Install Python 3.10 or newer and Git. The project uses SQLite by default. The `sqlite3` command-line program is optional and is only needed for direct terminal database commands.

### 1. Clone the repository and enter the directory
```bash
git clone https://github.com/NishanthShaganti-hub/TeamSphere.git
cd TeamSphere
```

### 2. Create and activate a virtual environment

**macOS / Linux (bash or zsh):**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again. Alternatively, use Command Prompt:

```bat
py -3 -m venv venv
venv\Scripts\activate.bat
```

When activated, your prompt normally shows `(venv)`. Run `deactivate` to leave the environment.

### 3. Install dependencies

With the virtual environment active:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

**macOS / Linux:**

```bash
cp .env.example .env
```

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

Edit `.env` to set a private `SECRET_KEY`. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Optionally set `ALLOWED_EMAIL_DOMAIN` to restrict student registration to a university email domain. Leave `DATABASE_URL` unset to use `instance/teamsphere.db`.

### 5. Initialize the SQLite Database
```bash
python -m flask --app app init-db
```
This creates missing tables. It does not erase data or change existing tables when the model schema changes. The database starts without demo listings; users add listings themselves using **Post a project**.

### 6. Create a Verified Faculty Account (Optional)
```bash
python -m flask --app app create-faculty \
  --name "Prof. Name" \
  --email "faculty@college.edu" \
  --dept "Department of Information Technology"
```
The command prompts for a password. You can also pass `--password "YourPassword123!"`, but the prompt avoids storing it in shell history.

### 7. Run the Application
```bash
python app.py
```
Open **[http://127.0.0.1:5001/](http://127.0.0.1:5001/)** in your browser. Stop the server with `Ctrl+C`. Port 5001 avoids the common macOS AirPlay Receiver conflict on port 5000.

Alternatively, run Flask's development server:

```bash
python -m flask --app app run --host 127.0.0.1 --port 5001 --debug
```

---

## Deploy to Vercel

Vercel runs the Flask app from the root `app.py` entrypoint. Static assets are in `public/static/`, which Vercel serves directly; Flask serves the same files locally at `/static/`.

1. Import `NishanthShaganti-hub/TeamSphere` into Vercel and select the repository root as the project root. Vercel detects the Flask app and Python dependencies from `app.py` and `requirements.txt`.
2. Configure these environment variables in the Vercel project for Production and Preview:
   * `SECRET_KEY`: a long, random value; do not use the example or development key.
   * `DATABASE_URL`: the connection URL for your hosted PostgreSQL database. Use the provider's pooled URL if required by its Vercel/serverless guidance. Both `postgres://` and `postgresql://` URLs are normalized to use psycopg 3.
   * `FLASK_ENV`: `production`.
   * Optionally set `ALLOWED_EMAIL_DOMAIN` to limit registration to your institution.
3. Initialize the hosted database schema once from a trusted machine with the same `SECRET_KEY` and `DATABASE_URL` configured in its environment:

   ```bash
   FLASK_ENV=production python -m flask --app app init-db
   ```

   This creates missing tables only; it does not migrate existing tables. For later schema changes, create and apply Flask-Migrate migrations instead.
4. Deploy from Vercel, or push a commit to the connected GitHub branch to trigger a deployment. Vercel sets secure session cookies and uses production configuration automatically.

SQLite is intended for local development only on Vercel: serverless filesystems are ephemeral, so use hosted PostgreSQL to retain accounts and project data.

---

## Database Commands (SQLite)

Commands below assume you are in the repository root and using the default database, `instance/teamsphere.db`. If `DATABASE_URL` is set in `.env`, use the path from that setting for SQLite commands. The app's custom Flask commands are `init-db` and `create-faculty`.

### Initialize database tables

```bash
python -m flask --app app init-db
```

This is safe to rerun: it creates missing tables but does not migrate existing tables or delete records.

### Apply model/schema changes

For changes to database models, use Flask-Migrate rather than relying on `init-db` to alter existing tables. Initialize the migration repository once:

```bash
python -m flask --app app db init
```

For each model change, generate and apply a migration:

```bash
python -m flask --app app db migrate -m "Describe the schema change"
python -m flask --app app db upgrade
```

Review generated files in `migrations/` before applying them, and commit those migration files with the model change. `db init` is only needed once per repository.

### Inspect database contents

Use the built-in inspector:

```bash
python inspect_db.py
```

Or query SQLite directly (install the `sqlite3` command-line tool separately if it is unavailable):

```bash
sqlite3 -header -column instance/teamsphere.db "SELECT id, display_name, email, role, department, year_of_study FROM users;"
sqlite3 -header -column instance/teamsphere.db "SELECT id, title, category, status, owner_id FROM projects;"
sqlite3 -header -column instance/teamsphere.db "SELECT id, sender_id, recipient_id, project_id, status FROM team_requests;"
```

### Interactive SQLite commands

Open a prompt:

```bash
sqlite3 instance/teamsphere.db
```

At `sqlite>`:

```sql
.tables
.schema users
.schema projects
.headers on
.mode column
PRAGMA foreign_keys;
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;
SELECT * FROM users;
SELECT * FROM projects;
.quit
```

Run a single statement without the interactive prompt:

```bash
sqlite3 instance/teamsphere.db "SELECT COUNT(*) FROM users;"
```

SQLite supports standard `SELECT`, `INSERT`, `UPDATE`, and `DELETE` statements. Use the web app for routine user and project management; direct SQL bypasses application validation and authorization. Back up before editing or deleting data. Examples (replace `123` with the intended project ID):

```sql
-- Find a user by email
SELECT id, display_name, email, role FROM users WHERE email = 'student@college.edu';

-- List projects, newest first
SELECT id, title, category, status FROM projects ORDER BY id DESC;

-- Update a project's status
UPDATE projects SET status = 'completed' WHERE id = 123;

--- Delete a project
DELETE FROM projects WHERE id = 123;
```

For a group of related SQL changes, use a transaction so you can undo them before committing:

```sql
BEGIN;
-- Run the intended UPDATE or DELETE statements here.
ROLLBACK; -- use COMMIT instead when you want to keep the changes
```

### Back up or reset the local database

Back up before maintenance:

```bash
cp instance/teamsphere.db instance/teamsphere.backup.db
```

PowerShell equivalent:

```powershell
Copy-Item instance/teamsphere.db instance/teamsphere.backup.db
```

Restore from that backup with the app stopped:

```bash
cp instance/teamsphere.backup.db instance/teamsphere.db
```

```powershell
Copy-Item instance/teamsphere.backup.db instance/teamsphere.db
```

To intentionally reset local development data, stop the app and back up first, then remove the database and initialize a fresh one.

**macOS / Linux:**

```bash
rm instance/teamsphere.db
python -m flask --app app init-db
```

**Windows PowerShell:**

```powershell
Remove-Item instance\teamsphere.db
python -m flask --app app init-db
```

Resetting removes all local users, projects, skills, interests, and requests in that database.

### Optional SQLite GUI

1. Download [DB Browser for SQLite](https://sqlitebrowser.org/).
2. Open `instance/teamsphere.db`.
3. Use **Browse Data** to inspect tables or **Execute SQL** to run queries.

---

## Running the Automated Test Suite

The test suite runs against an isolated, in-memory SQLite database (`sqlite:///:memory:`), not the development database. Activate the virtual environment first.

Run all tests:

```bash
python -m pytest -v
```

Run one test file:

```bash
python -m pytest -v tests/test_stage2_ui.py
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
