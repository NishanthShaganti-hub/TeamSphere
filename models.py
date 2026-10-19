"""
Database Models for TeamSphere (Student Project & Team Finder).
Follows specifications from requirements.md (v3).
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, func, text
from extensions import db


def utc_now():
    """Return current timestamp in UTC timezone."""
    return datetime.now(timezone.utc)


# Association Table: User <-> Skills
user_skills = db.Table(
    "user_skills",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# Association Table: User <-> Interests
user_interests = db.Table(
    "user_interests",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("interest_id", db.Integer, db.ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)

# Association Table: Project <-> Skills
project_skills = db.Table(
    "project_skills",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class ProjectMember(db.Model):
    """
    Project Members association with joined_at timestamp.
    Composite primary key: (project_id, user_id).
    """
    __tablename__ = "project_members"

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship("User", backref=db.backref("project_memberships", cascade="all, delete-orphan", passive_deletes=True))
    project = db.relationship("Project", backref=db.backref("project_memberships", cascade="all, delete-orphan", passive_deletes=True))


class Skill(db.Model):
    """
    Normalized skill names (stored lowercase and trimmed).
    """
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Skill {self.name}>"


class Interest(db.Model):
    """
    Normalized student interests (stored lowercase and trimmed).
    """
    __tablename__ = "interests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Interest {self.name}>"


class User(UserMixin, db.Model):
    """
    User account model.
    In v1, only the 'student' role is used. Public registration always creates 'student'.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    department = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.String(300), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    skills = db.relationship(
        "Skill",
        secondary=user_skills,
        backref=db.backref("users", lazy="dynamic"),
        lazy="joined",
    )
    interests = db.relationship(
        "Interest",
        secondary=user_interests,
        backref=db.backref("users", lazy="dynamic"),
        lazy="joined",
    )
    owned_projects = db.relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
    )
    member_projects = db.relationship(
        "Project",
        secondary="project_members",
        back_populates="members",
        lazy="dynamic",
        overlaps="project_memberships,project,user",
    )
    sent_requests = db.relationship(
        "TeamRequest",
        foreign_keys="TeamRequest.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
    )
    received_requests = db.relationship(
        "TeamRequest",
        foreign_keys="TeamRequest.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
    )

    def set_password(self, password: str):
        """Hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify given password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self) -> str:
        """Return 1-2 uppercase letters for the avatar fallback."""
        parts = self.display_name.strip().split()
        if not parts:
            return "U"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def to_public_dict(self) -> dict:
        """
        Public collaboration profile dictionary.
        Strictly excludes password_hash and email for student privacy.
        """
        return {
            "id": self.id,
            "display_name": self.display_name,
            "department": self.department or "",
            "year_of_study": self.year_of_study,
            "bio": self.bio or "",
            "profile_image_url": self.profile_image_url or "",
            "initials": self.initials,
            "skills": [s.name for s in self.skills],
            "interests": [i.name for i in self.interests],
        }

    def __repr__(self):
        return f"<User {self.id}: {self.display_name}>"


class Project(db.Model):
    """
    Project entity.
    Categories: hackathon, academic, personal, research
    Statuses: looking_for_teammates, in_progress, completed
    """
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    short_description = db.Column(db.String(140), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, default="looking_for_teammates", index=True)
    repo_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    owner = db.relationship("User", back_populates="owned_projects")
    skills = db.relationship(
        "Skill",
        secondary=project_skills,
        backref=db.backref("projects", lazy="dynamic"),
        lazy="joined",
    )
    members = db.relationship(
        "User",
        secondary="project_members",
        back_populates="member_projects",
        lazy="selectin",
        overlaps="project_memberships,project,user",
    )
    requests = db.relationship(
        "TeamRequest",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
    )

    def is_member(self, user_id: int) -> bool:
        """Check if user_id is the owner or a listed member."""
        if self.owner_id == user_id:
            return True
        return any(m.id == user_id for m in self.members)

    def __repr__(self):
        return f"<Project {self.id}: {self.title}>"


class TeamRequest(db.Model):
    """
    Team-up request to collaborate with a student or join a project.
    Statuses: pending, accepted, rejected, cancelled
    """
    __tablename__ = "team_requests"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    message = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_requests")
    recipient = db.relationship("User", foreign_keys=[recipient_id], back_populates="received_requests")
    project = db.relationship("Project", back_populates="requests")

    __table_args__ = (
        # Partial unique index: prevents duplicate pending requests between sender, recipient, and project
        # COALESCE(project_id, 0) handles NULL project_id for student-to-student requests in SQLite
        Index(
            "idx_team_requests_pending_unique",
            "sender_id",
            "recipient_id",
            func.coalesce(project_id, 0),
            unique=True,
            sqlite_where=text("status = 'pending'"),
            postgresql_where=text("status = 'pending'"),
        ),
    )

    def __repr__(self):
        return f"<TeamRequest {self.id}: sender={self.sender_id} recipient={self.recipient_id} status={self.status}>"
