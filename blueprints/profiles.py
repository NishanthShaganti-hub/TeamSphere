"""
Profiles Blueprint: View student profile and edit personal profile.
Enforces privacy rules (emails and passwords hidden).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import User, Skill, Interest, TeamRequest, Project

profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.route("/profile/<int:user_id>")
def view_profile(user_id: int):
    """View public student profile and their active projects."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    is_self = current_user.is_authenticated and current_user.id == user.id

    # Fetch user's public projects
    projects = (
        Project.query.filter_by(owner_id=user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    # Check if a pending collaboration request already exists between current_user and this student
    has_pending_collab = False
    if current_user.is_authenticated and not is_self:
        has_pending_collab = TeamRequest.query.filter_by(
            sender_id=current_user.id,
            recipient_id=user.id,
            project_id=None,
            status="pending",
        ).first() is not None

    return render_template(
        "profile.html",
        profile_user=user,
        is_self=is_self,
        projects=projects,
        has_pending_collab=has_pending_collab,
    )


@profiles_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit student profile details (department, year, bio, and skills)."""
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        department = request.form.get("department", "").strip()
        year_str = request.form.get("year_of_study", "").strip()
        bio = request.form.get("bio", "").strip()
        raw_skills = request.form.get("skills", "").strip()
        raw_interests = request.form.get("interests", "").strip()

        errors = []
        if not display_name or len(display_name) < 2 or len(display_name) > 100:
            errors.append("Display name must be between 2 and 100 characters.")

        year = None
        if year_str:
            try:
                year = int(year_str)
                if year < 1 or year > 4:
                    errors.append("Year of study must be between 1 and 4.")
            except ValueError:
                errors.append("Year of study must be a valid integer.")

        if bio and len(bio) > 300:
            errors.append("Bio cannot exceed 300 characters.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("edit_profile.html", form_data=request.form), 400

        # Save profile fields
        current_user.display_name = display_name
        current_user.department = department or "Department of Information Technology"
        current_user.year_of_study = year
        current_user.bio = bio or None

        # Update normalized skills (max 10 items, max 30 chars each)
        current_user.skills.clear()
        if raw_skills:
            for s_name in raw_skills.split(",")[:10]:
                clean_skill = s_name.strip().lower().replace("  ", " ")
                if clean_skill and len(clean_skill) <= 30:
                    skill_obj = Skill.query.filter_by(name=clean_skill).first()
                    if not skill_obj:
                        skill_obj = Skill(name=clean_skill)
                        db.session.add(skill_obj)
                    if skill_obj not in current_user.skills:
                        current_user.skills.append(skill_obj)

        # Update normalized interests (max 10 items, max 30 chars each)
        current_user.interests.clear()
        if raw_interests:
            for i_name in raw_interests.split(",")[:10]:
                clean_interest = i_name.strip().lower().replace("  ", " ")
                if clean_interest and len(clean_interest) <= 30:
                    interest_obj = Interest.query.filter_by(name=clean_interest).first()
                    if not interest_obj:
                        interest_obj = Interest(name=clean_interest)
                        db.session.add(interest_obj)
                    if interest_obj not in current_user.interests:
                        current_user.interests.append(interest_obj)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profiles.view_profile", user_id=current_user.id))

    skills_csv = ",".join(s.name for s in current_user.skills)
    interests_csv = ",".join(i.name for i in current_user.interests)
    return render_template("edit_profile.html", form_data=current_user, skills_csv=skills_csv, interests_csv=interests_csv)
