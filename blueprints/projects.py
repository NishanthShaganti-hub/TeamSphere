"""
Projects Blueprint: Browse, create, detail, edit, delete, and archive.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Project, Skill, User, ProjectMember

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/projects")
def browse_projects():
    """Browse and filter projects (including completed project archive)."""
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip().lower()
    category_filter = request.args.get("category", "all").strip().lower()
    skill_filter = request.args.get("skill", "").strip().lower()
    faculty_only = request.args.get("faculty", "").lower() in ("true", "1", "yes")
    page = request.args.get("page", 1, type=int)

    query = Project.query

    # Faculty-only filter for official department hackathons and research
    if faculty_only:
        query = query.join(User, Project.owner_id == User.id).filter(User.role == "faculty")

    # Status filter
    if status_filter == "open":
        query = query.filter_by(status="looking_for_teammates")
    elif status_filter == "in_progress":
        query = query.filter_by(status="in_progress")
    elif status_filter == "completed" or status_filter == "archive":
        query = query.filter_by(status="completed")
    elif status_filter != "all" and status_filter in ("looking_for_teammates", "in_progress", "completed"):
        query = query.filter_by(status=status_filter)

    # Category filter
    if category_filter and category_filter != "all":
        query = query.filter_by(category=category_filter)

    # Skill filter
    if skill_filter:
        query = query.filter(Project.skills.any(Skill.name == skill_filter))

    # Keyword search across title, short description, and full description
    if search_query:
        search_like = f"%{search_query}%"
        query = query.filter(
            (Project.title.ilike(search_like))
            | (Project.short_description.ilike(search_like))
            | (Project.full_description.ilike(search_like))
        )

    # Order newest first
    query = query.order_by(Project.created_at.desc())

    # Paginate (12 per page)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    projects = pagination.items

    # Fetch all skills for filter chips
    available_skills = Skill.query.order_by(Skill.name).all()

    return render_template(
        "projects.html",
        projects=projects,
        pagination=pagination,
        search_query=search_query,
        status_filter=status_filter,
        category_filter=category_filter,
        skill_filter=skill_filter,
        faculty_only=faculty_only,
        available_skills=available_skills,
    )


@projects_bp.route("/projects/<int:project_id>")
def project_detail(project_id: int):
    """View details of a project and actions for teammates."""
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)

    is_owner = current_user.is_authenticated and project.owner_id == current_user.id
    is_member = current_user.is_authenticated and project.is_member(current_user.id)

    # Check if current user has a pending request
    has_pending_request = False
    if current_user.is_authenticated and not is_owner and not is_member:
        from models import TeamRequest
        has_pending_request = TeamRequest.query.filter_by(
            sender_id=current_user.id,
            project_id=project.id,
            status="pending",
        ).first() is not None

    return render_template(
        "project_detail.html",
        project=project,
        is_owner=is_owner,
        is_member=is_member,
        has_pending_request=has_pending_request,
    )


@projects_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def create_project():
    """Create a new project."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        short_description = request.form.get("short_description", "").strip()
        full_description = request.form.get("full_description", "").strip()
        category = request.form.get("category", "hackathon").strip().lower()
        status = request.form.get("status", "looking_for_teammates").strip().lower()
        repo_url = request.form.get("repo_url", "").strip()
        raw_skills = request.form.get("skills", "").strip()

        # Server-side validation
        errors = []
        if not title or len(title) > 150:
            errors.append("Title is required and must be under 150 characters.")
        if not short_description or len(short_description) > 140:
            errors.append("Short description is required and must be under 140 characters.")
        if not full_description:
            errors.append("Full description is required.")
        if category not in ("hackathon", "academic", "personal", "research"):
            errors.append("Invalid project category.")
        if status not in ("looking_for_teammates", "in_progress", "completed"):
            errors.append("Invalid project status.")
        if repo_url and not (repo_url.startswith("http://") or repo_url.startswith("https://")):
            errors.append("Repository URL must start with http:// or https://")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("create_project.html", is_edit=False, form_data=request.form), 400

        project = Project(
            owner_id=current_user.id,
            title=title,
            short_description=short_description,
            full_description=full_description,
            category=category,
            status=status,
            repo_url=repo_url or None,
        )

        # Normalize and attach skills
        if raw_skills:
            for s_name in raw_skills.split(","):
                clean_name = s_name.strip().lower().replace("  ", " ")
                if clean_name and len(clean_name) <= 30:
                    skill = Skill.query.filter_by(name=clean_name).first()
                    if not skill:
                        skill = Skill(name=clean_name)
                        db.session.add(skill)
                    if skill not in project.skills:
                        project.skills.append(skill)

        db.session.add(project)
        db.session.commit()
        flash("Your project has been successfully published!", "success")
        return redirect(url_for("projects.project_detail", project_id=project.id))

    return render_template("create_project.html", is_edit=False, form_data={})


@projects_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id: int):
    """Edit project details. Strictly restricted to owner."""
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)

    # Permission check: Return 403 if viewer is not the owner
    if project.owner_id != current_user.id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        short_description = request.form.get("short_description", "").strip()
        full_description = request.form.get("full_description", "").strip()
        category = request.form.get("category", "hackathon").strip().lower()
        status = request.form.get("status", "looking_for_teammates").strip().lower()
        repo_url = request.form.get("repo_url", "").strip()
        raw_skills = request.form.get("skills", "").strip()

        errors = []
        if not title or len(title) > 150:
            errors.append("Title is required and must be under 150 characters.")
        if not short_description or len(short_description) > 140:
            errors.append("Short description is required and must be under 140 characters.")
        if not full_description:
            errors.append("Full description is required.")
        if category not in ("hackathon", "academic", "personal", "research"):
            errors.append("Invalid project category.")
        if status not in ("looking_for_teammates", "in_progress", "completed"):
            errors.append("Invalid project status.")
        if repo_url and not (repo_url.startswith("http://") or repo_url.startswith("https://")):
            errors.append("Repository URL must start with http:// or https://")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("create_project.html", is_edit=True, project=project, form_data=request.form), 400

        project.title = title
        project.short_description = short_description
        project.full_description = full_description
        project.category = category
        project.status = status
        project.repo_url = repo_url or None

        # Update skills
        project.skills.clear()
        if raw_skills:
            for s_name in raw_skills.split(","):
                clean_name = s_name.strip().lower().replace("  ", " ")
                if clean_name and len(clean_name) <= 30:
                    skill = Skill.query.filter_by(name=clean_name).first()
                    if not skill:
                        skill = Skill(name=clean_name)
                        db.session.add(skill)
                    if skill not in project.skills:
                        project.skills.append(skill)

        db.session.commit()
        flash("Project details updated successfully.", "success")
        return redirect(url_for("projects.project_detail", project_id=project.id))

    skills_csv = ",".join(s.name for s in project.skills)
    return render_template("create_project.html", is_edit=True, project=project, form_data=project, skills_csv=skills_csv)


@projects_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id: int):
    """Delete a project. Strictly restricted to owner."""
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)

    if project.owner_id != current_user.id:
        abort(403)

    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully.", "info")
    return redirect(url_for("projects.browse_projects"))
