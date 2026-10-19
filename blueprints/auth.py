"""
Authentication Blueprint: Registration, Login, and Logout.
Follows security rules for rate limiting, safe redirects, and session clearing.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import limiter
from forms import RegistrationForm, LoginForm
from services.auth_service import register_student, authenticate_user
from utils.validators import is_safe_url

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    """Register a new student account."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    allowed_domain = current_app.config.get("ALLOWED_EMAIL_DOMAIN", "")

    if form.validate_on_submit():
        user, error = register_student(
            display_name=form.display_name.data,
            email=form.email.data,
            password=form.password.data,
            allowed_domain=allowed_domain,
        )

        if error:
            flash(error, "danger")
            return render_template("register.html", form=form, allowed_domain=allowed_domain), 400

        # Session security: clear pre-login session data before authenticating
        session.clear()
        login_user(user)
        flash(f"Welcome to TeamSphere, {user.display_name}! Your student account is ready.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html", form=form, allowed_domain=allowed_domain)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    """Authenticate student with email and password."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        user = authenticate_user(
            email=form.email.data,
            password=form.password.data,
        )

        if not user:
            # Generic error message: never reveal whether the email exists or password failed
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form), 401

        # Session security: clear pre-login session data before establishing user session
        session.clear()
        login_user(user)

        # Validate post-login redirect target to prevent open redirect vulnerabilities
        next_page = request.args.get("next")
        if next_page and is_safe_url(next_page):
            return redirect(next_page)

        flash(f"Welcome back, {user.display_name}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out current user and clear session state."""
    logout_user()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))
