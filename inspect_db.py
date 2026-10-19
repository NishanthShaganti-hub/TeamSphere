"""
Quick database inspection tool for TeamSphere.
Run with: python inspect_db.py
Displays formatted tables of all users, projects, and requests stored in SQLite.
"""

from app import create_app
from models import User, Project, TeamRequest, Skill

app = create_app()

def inspect():
    with app.app_context():
        print("\n" + "=" * 70)
        print(" TEAMSPHERE SQLITE DATABASE: instance/teamsphere.db")
        print("=" * 70)

        # 1. Users Table
        users = User.query.all()
        print(f"\n--- [USERS TABLE] ({len(users)} registered) ---")
        if not users:
            print("  (No users found)")
        for u in users:
            skills = ", ".join([s.name for s in u.skills]) or "None"
            print(f"  ID: {u.id} | Name: {u.display_name} | Role: {u.role}")
            print(f"       Email: {u.email} | Year: {u.year_of_study or 'N/A'}")
            print(f"       Dept:  {u.department or 'N/A'}")
            print(f"       Bio:   {u.bio or 'None'}")
            print(f"       Skills: {skills}")
            print("  " + "-" * 60)

        # 2. Projects Table
        projects = Project.query.all()
        print(f"\n--- [PROJECTS TABLE] ({len(projects)} posted) ---")
        if not projects:
            print("  (No projects found)")
        for p in projects:
            skills = ", ".join([s.name for s in p.skills]) or "None"
            print(f"  ID: {p.id} | Title: {p.title}")
            print(f"       Lead: {p.owner.display_name} ({p.owner.role})")
            print(f"       Status: {p.status} | Category: {p.category}")
            print(f"       Skills: {skills}")
            print("  " + "-" * 60)

        # 3. Requests Table
        requests = TeamRequest.query.all()
        print(f"\n--- [TEAM REQUESTS TABLE] ({len(requests)} total) ---")
        if not requests:
            print("  (No requests found)")
        for r in requests:
            target = f"Project: {r.project.title}" if r.project else "Direct Student Collab"
            print(f"  ID: {r.id} | From: {r.sender.display_name} -> To: {r.recipient.display_name}")
            print(f"       Target: {target} | Status: {r.status}")
            print("  " + "-" * 60)

        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    inspect()
