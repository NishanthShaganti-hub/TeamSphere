"""
TeamSphere Application Factory.
Initializes the Flask application, database extensions, and blueprints.
"""

import os
import click
from flask import Flask, render_template, request, jsonify
from config import config_by_name, DevelopmentConfig
from extensions import db, login_manager, csrf, limiter, migrate
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.profiles import profiles_bp
from blueprints.projects import projects_bp
from blueprints.requests import requests_bp


def skill_color(skill_name):
    """Return a stable color class for a skill tag."""
    return sum(ord(char) for char in skill_name) % 6


def register_error_handlers(app: Flask):
    """Register custom error handlers for HTTP status codes."""

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Forbidden", "message": "You do not have permission to perform this action."}), 403
        try:
            return render_template("errors/403.html"), 403
        except Exception:
            return "<h1>403 Forbidden</h1><p>You do not have permission to view this resource.</p>", 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Not Found", "message": "The requested resource was not found."}), 404
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            return "<h1>404 Not Found</h1><p>The requested page could not be found.</p>", 404

    @app.errorhandler(409)
    def conflict(error):
        msg = getattr(error, "description", "A conflict occurred with the current state of the resource.")
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Conflict", "message": msg}), 409
        return f"<h1>409 Conflict</h1><p>{msg}</p>", 409

    @app.errorhandler(429)
    def ratelimit_handler(error):
        msg = "Too many requests. Please slow down and try again shortly."
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Rate Limit Exceeded", "message": msg}), 429
        return f"<h1>429 Rate Limit Exceeded</h1><p>{msg}</p>", 429

    @app.errorhandler(500)
    def server_error(error):
        # Never leak raw stack traces to the client
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Server Error", "message": "An internal error occurred. Please try again later."}), 500
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return "<h1>500 Server Error</h1><p>An unexpected error occurred. Please try again later.</p>", 500


def create_app(config_object_or_name=None) -> Flask:
    """
    Application factory pattern.
    Configures and returns a new Flask application instance.
    """
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=os.path.join(os.path.dirname(__file__), "public", "static"),
        static_url_path="/static",
    )

    # Determine configuration class
    if config_object_or_name is None:
        env_name = (
            "production"
            if os.environ.get("VERCEL")
            else os.environ.get("FLASK_ENV", "development").lower()
        )
        config_class = config_by_name.get(env_name, DevelopmentConfig)
    elif isinstance(config_object_or_name, str):
        config_class = config_by_name.get(config_object_or_name, DevelopmentConfig)
    else:
        config_class = config_object_or_name

    if config_class is config_by_name["production"]:
        config_class.validate()

    app.config.from_object(config_class)
    app.add_template_filter(skill_color, "skill_color")

    # Ensure instance directory exists for SQLite database storage
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Context processor for navigation badges and safe endpoint resolution
    @app.context_processor
    def inject_global_template_vars():
        from flask_login import current_user
        from datetime import datetime, timezone
        from models import TeamRequest

        pending_count = 0
        if current_user.is_authenticated:
            try:
                pending_count = TeamRequest.query.filter_by(
                    recipient_id=current_user.id,
                    status="pending"
                ).count()
            except Exception:
                pending_count = 0

        endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
        return {
            "url_map_endpoints": endpoints,
            "now": datetime.now(timezone.utc),
            "pending_requests_count": pending_count,
        }

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(requests_bp)

    # CLI Command to initialize tables in SQLite database
    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables."""
        db.create_all()
        print(f"Database initialized successfully at: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # CLI Command to create verified Faculty accounts
    @app.cli.command("create-faculty")
    @click.option("--name", prompt="Faculty Full Name", help="Full name with title (e.g., Prof. Sarah Jenkins)")
    @click.option("--email", prompt="Faculty College Email", help="Official college email address")
    @click.option("--dept", default="Department of Information Technology", prompt="Department", help="Academic Department")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Account password (min 8 characters)")
    def create_faculty_command(name, email, dept, password):
        """Create a verified Faculty account for posting official hackathons and projects."""
        from models import User
        from utils.validators import normalize_email

        clean_name = name.strip()
        clean_email = normalize_email(email)

        if len(clean_name) < 2:
            click.echo("Error: Name must be at least 2 characters long.")
            return

        if not clean_email or "@" not in clean_email:
            click.echo("Error: Please provide a valid email address.")
            return

        if len(password) < 8:
            click.echo("Error: Password must be at least 8 characters long.")
            return

        existing = User.query.filter_by(email=clean_email).first()
        if existing:
            click.echo(f"Error: An account with email '{clean_email}' already exists.")
            return

        faculty_user = User(
            display_name=clean_name,
            email=clean_email,
            role="faculty",  # Verified faculty role
            department=dept.strip(),
            year_of_study=None,
            bio=f"Faculty member in the {dept.strip()}.",
        )
        faculty_user.set_password(password)

        db.session.add(faculty_user)
        db.session.commit()
        click.echo(f"Success! Faculty account '{clean_name}' ({clean_email}) created with role 'faculty'.")

    # Register error handlers
    register_error_handlers(app)

    return app


# Default application instance for dev servers and CLI tools
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n=======================================================")
    print(f" TeamSphere running on http://127.0.0.1:{port}")
    print(f" (Port 5001 used to prevent macOS AirPlay port 5000 conflicts)")
    print(f"=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=True)
