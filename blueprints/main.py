"""
Main Blueprint: Landing page, dashboard, and health routes.
"""

from flask import Blueprint, render_template, jsonify
from models import Project

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Render the portal landing page with recent active projects."""
    try:
        recent_projects = (
            Project.query.filter(Project.status != "completed")
            .order_by(Project.created_at.desc())
            .limit(3)
            .all()
        )
    except Exception:
        # In case tables have not been created yet in local dev run
        recent_projects = []

    return render_template("index.html", recent_projects=recent_projects)


@main_bp.route("/dashboard")
def dashboard():
    """Student dashboard showing personal projects and request summaries."""
    from flask_login import login_required, current_user
    from models import Project, TeamRequest

    if not current_user.is_authenticated:
        from flask import redirect, url_for
        return redirect(url_for("auth.login", next="/dashboard"))

    # Fetch personal projects
    my_projects = (
        Project.query.filter_by(owner_id=current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    # Fetch pending received requests (awaiting current user's review)
    requests_to_review = (
        TeamRequest.query.filter_by(recipient_id=current_user.id, status="pending")
        .order_by(TeamRequest.created_at.desc())
        .all()
    )

    # Fetch pending sent requests (awaiting reply from others)
    requests_awaiting = (
        TeamRequest.query.filter_by(sender_id=current_user.id, status="pending")
        .order_by(TeamRequest.created_at.desc())
        .all()
    )

    return render_template(
        "dashboard.html",
        my_projects=my_projects,
        requests_to_review=requests_to_review,
        requests_awaiting=requests_awaiting,
    )


@main_bp.route("/health")
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "service": "TeamSphere"})
