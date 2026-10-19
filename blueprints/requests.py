"""
Requests Blueprint: Team Finder student directory and team-up request workflows.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models import User, Skill, Interest, TeamRequest, Project
from services.request_service import (
    send_team_request,
    accept_team_request,
    reject_team_request,
    cancel_team_request,
)

requests_bp = Blueprint("requests", __name__)


@requests_bp.route("/team-finder")
def team_finder():
    """Discover student collaborators filtered by skills, interests, and department."""
    search_query = request.args.get("q", "").strip()
    skill_filter = request.args.get("skill", "").strip().lower()
    interest_filter = request.args.get("interest", "").strip().lower()
    page = request.args.get("page", 1, type=int)

    query = User.query

    # Rule: Do not show current user in the team finder directory
    if current_user.is_authenticated:
        query = query.filter(User.id != current_user.id)

    # Search filter (name, department, bio)
    if search_query:
        like_term = f"%{search_query}%"
        query = query.filter(
            (User.display_name.ilike(like_term))
            | (User.department.ilike(like_term))
            | (User.bio.ilike(like_term))
        )

    # Skill filter
    if skill_filter:
        query = query.filter(User.skills.any(Skill.name == skill_filter))

    # Interest filter
    if interest_filter:
        query = query.filter(User.interests.any(Interest.name == interest_filter))

    query = query.order_by(User.display_name.asc())

    # Paginate (12 per page)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    students = pagination.items

    available_skills = Skill.query.order_by(Skill.name).all()
    available_interests = Interest.query.order_by(Interest.name).all()

    # Determine pending collaboration requests if logged in
    pending_recipient_ids = set()
    if current_user.is_authenticated:
        pending_requests = TeamRequest.query.filter_by(
            sender_id=current_user.id,
            project_id=None,
            status="pending",
        ).all()
        pending_recipient_ids = {r.recipient_id for r in pending_requests}

    return render_template(
        "team_finder.html",
        students=students,
        pagination=pagination,
        search_query=search_query,
        skill_filter=skill_filter,
        interest_filter=interest_filter,
        available_skills=available_skills,
        available_interests=available_interests,
        pending_recipient_ids=pending_recipient_ids,
    )


@requests_bp.route("/requests")
@login_required
def view_requests():
    """View all received and sent collaboration requests."""
    received = (
        TeamRequest.query.filter_by(recipient_id=current_user.id)
        .order_by(TeamRequest.created_at.desc())
        .all()
    )
    sent = (
        TeamRequest.query.filter_by(sender_id=current_user.id)
        .order_by(TeamRequest.created_at.desc())
        .all()
    )

    return render_template("requests.html", received=received, sent=sent)


@requests_bp.route("/requests/send", methods=["POST"])
@login_required
def send_request():
    """Send a request to collaborate or join a project."""
    recipient_id = request.form.get("recipient_id", type=int)
    project_id = request.form.get("project_id", type=int)
    message = request.form.get("message", "").strip()

    if not recipient_id:
        flash("Invalid recipient student.", "danger")
        return redirect(request.referrer or url_for("requests.team_finder"))

    req, error, status_code = send_team_request(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        project_id=project_id,
        message=message,
    )

    if error:
        flash(error, "danger" if status_code != 409 else "warning")
    else:
        flash("Team-up request sent successfully!", "success")

    return redirect(request.referrer or url_for("requests.view_requests"))


@requests_bp.route("/requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id: int):
    """Accept a pending request atomically."""
    success, message, status_code = accept_team_request(request_id, current_user.id)

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": success, "message": message}), status_code

    flash(message, "success" if success else "danger")
    return redirect(request.referrer or url_for("requests.view_requests"))


@requests_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id: int):
    """Reject a pending request."""
    success, message, status_code = reject_team_request(request_id, current_user.id)

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": success, "message": message}), status_code

    flash(message, "info" if success else "danger")
    return redirect(request.referrer or url_for("requests.view_requests"))


@requests_bp.route("/requests/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel_request(request_id: int):
    """Cancel a pending request."""
    success, message, status_code = cancel_team_request(request_id, current_user.id)

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": success, "message": message}), status_code

    flash(message, "info" if success else "danger")
    return redirect(request.referrer or url_for("requests.view_requests"))
