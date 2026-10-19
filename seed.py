"""
Seed script for TeamSphere.
Populates fake student profiles, demo projects, and sample requests.
Never uses real student data or real production secrets.
Run with: python seed.py
"""

from app import create_app
from extensions import db
from models import User, Skill, Interest, Project, ProjectMember, TeamRequest

app = create_app()

def seed_database():
    """Insert fake demo students, projects, and requests."""
    with app.app_context():
        # Clean existing data
        db.drop_all()
        db.create_all()
        print("Cleared database schema and re-created tables.")

        # 1. Create Skills
        skill_names = [
            "python", "javascript", "flask", "react", "sql", "machine-learning",
            "docker", "data-analysis", "cybersecurity", "linux", "html", "css"
        ]
        skills_map = {}
        for name in skill_names:
            sk = Skill(name=name)
            db.session.add(sk)
            skills_map[name] = sk

        # 2. Create Interests
        interest_names = [
            "ai ethics", "open-source", "ui/ux", "cloud computing", "hackathons",
            "data science", "infosec", "robotics"
        ]
        interests_map = {}
        for name in interest_names:
            it = Interest(name=name)
            db.session.add(it)
            interests_map[name] = it

        db.session.commit()

        # 3. Create Students (Password for all demo accounts: Password123!)
        demo_students_data = [
            {
                "display_name": "Maya Patel",
                "email": "maya.patel@college.edu",
                "department": "Department of Information Technology",
                "year_of_study": 3,
                "bio": "Junior passionate about Python backends and machine learning. Looking for teammates for the upcoming Spring Hackathon!",
                "skills": ["python", "machine-learning", "flask", "sql"],
                "interests": ["ai ethics", "hackathons"],
            },
            {
                "display_name": "Liam Chen",
                "email": "liam.chen@college.edu",
                "department": "Department of Information Technology",
                "year_of_study": 2,
                "bio": "Frontend enthusiast building fast, accessible web experiences. Excited to collaborate on product design.",
                "skills": ["javascript", "html", "css", "react"],
                "interests": ["ui/ux", "open-source"],
            },
            {
                "display_name": "Aria Rodriguez",
                "email": "aria.rodriguez@college.edu",
                "department": "Department of Information Technology",
                "year_of_study": 4,
                "bio": "Senior focusing on cloud architectures and DevOps pipelines. Mentoring junior students in containerization.",
                "skills": ["docker", "linux", "python", "sql"],
                "interests": ["cloud computing", "open-source"],
            },
            {
                "display_name": "David Kim",
                "email": "david.kim@college.edu",
                "department": "Department of Information Technology",
                "year_of_study": 1,
                "bio": "Freshman enthusiastic about data analysis and competitive programming. Looking to learn from upperclassmen.",
                "skills": ["python", "data-analysis"],
                "interests": ["data science", "hackathons"],
            },
            {
                "display_name": "Zoe Washington",
                "email": "zoe.washington@college.edu",
                "department": "Department of Information Technology",
                "year_of_study": 3,
                "bio": "Cybersecurity researcher and CTF player. Always looking for backend developers to build secure audit tools.",
                "skills": ["cybersecurity", "linux", "python"],
                "interests": ["infosec", "robotics"],
            },
        ]

        users = []
        for s_data in demo_students_data:
            user = User(
                display_name=s_data["display_name"],
                email=s_data["email"],
                role="student",
                department=s_data["department"],
                year_of_study=s_data["year_of_study"],
                bio=s_data["bio"],
            )
            user.set_password("Password123!")
            for sk in s_data["skills"]:
                user.skills.append(skills_map[sk])
            for it in s_data["interests"]:
                user.interests.append(interests_map[it])

            db.session.add(user)
            users.append(user)

        db.session.commit()
        print(f"Seeded {len(users)} fake students (Password: 'Password123!').")

        # 4. Create Projects
        projects_data = [
            {
                "owner": users[0],  # Maya
                "title": "Campus Pantry Tracker",
                "short_description": "Real-time web app tracking inventory and surplus donations for campus food pantries.",
                "full_description": "We are building a responsive web portal to connect student volunteers with campus food pantries. It tracks current stock levels, provides surplus alerts, and schedules donation drop-offs. Looking for a frontend developer familiar with vanilla JS/CSS to build intuitive volunteer forms.",
                "category": "hackathon",
                "status": "looking_for_teammates",
                "repo_url": "https://github.com/example/campus-pantry-tracker",
                "skills": ["python", "flask", "javascript", "html"],
            },
            {
                "owner": users[1],  # Liam
                "title": "Smart Course Schedule Visualizer",
                "short_description": "Interactive schedule builder that highlights conflicting exams and optimal study blocks.",
                "full_description": "An intuitive calendar tool specifically tailored for Information Technology undergrads. Import course codes and automatically generate color-coded weekly study timetables with zero overlapping sessions. Seeking a backend developer to assist with course catalog scraping.",
                "category": "academic",
                "status": "looking_for_teammates",
                "repo_url": "https://github.com/example/it-schedule-visualizer",
                "skills": ["javascript", "css", "html", "python"],
            },
            {
                "owner": users[2],  # Aria
                "title": "Cloud Lab Microservices Benchmarker",
                "short_description": "Automated performance testing framework measuring container latency in university clusters.",
                "full_description": "Senior research project measuring tail latency across lightweight Docker containers deployed on departmental server nodes. Developing automated Prometheus exporters and stress testing suites.",
                "category": "research",
                "status": "in_progress",
                "repo_url": "https://github.com/example/cloud-lab-benchmarker",
                "skills": ["docker", "linux", "python"],
            },
            {
                "owner": users[4],  # Zoe
                "title": "Peer-to-Peer Tutoring Exchange",
                "short_description": "Department portal pairing lowerclassmen with upperclass peer tutors for core IT labs.",
                "full_description": "Completed capstone project designed to facilitate peer-led tutoring in Object-Oriented Programming and Networking. Now permanently archived for departmental reference.",
                "category": "personal",
                "status": "completed",
                "repo_url": "https://github.com/example/it-tutoring-exchange",
                "skills": ["python", "sql", "html"],
            },
        ]

        projects = []
        for p_data in projects_data:
            proj = Project(
                owner_id=p_data["owner"].id,
                title=p_data["title"],
                short_description=p_data["short_description"],
                full_description=p_data["full_description"],
                category=p_data["category"],
                status=p_data["status"],
                repo_url=p_data["repo_url"],
            )
            for sk in p_data["skills"]:
                proj.skills.append(skills_map[sk])

            db.session.add(proj)
            projects.append(proj)

        db.session.commit()
        print(f"Seeded {len(projects)} demo projects across categories.")

        # 5. Add a project teammate
        pm = ProjectMember(project_id=projects[2].id, user_id=users[0].id)
        db.session.add(pm)

        # 6. Seed sample team-up requests
        # David Kim requests to join Maya's Campus Pantry Tracker
        req1 = TeamRequest(
            sender_id=users[3].id,  # David
            recipient_id=users[0].id,  # Maya
            project_id=projects[0].id,
            message="Hi Maya! I'm a freshman eager to help with data modeling and testing for the food pantry app.",
            status="pending",
        )

        # Zoe requests direct collaboration with Liam
        req2 = TeamRequest(
            sender_id=users[4].id,  # Zoe
            recipient_id=users[1].id,  # Liam
            project_id=None,
            message="Hey Liam! Loved your UI work. Want to team up for next month's hackathon?",
            status="pending",
        )

        db.session.add_all([req1, req2])
        db.session.commit()
        print("Seeded sample pending requests.")
        print("\nSeed complete! You can now log into any account with email and password 'Password123!'.")


if __name__ == "__main__":
    seed_database()
