"""
Request Service: Handles team-up requests and atomic accept transactions.
Implements all rules from Section 9 of requirements.md.
"""

from typing import Tuple, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from extensions import db
from models import TeamRequest, Project, ProjectMember, User, utc_now


def send_team_request(
    sender_id: int,
    recipient_id: int,
    project_id: Optional[int] = None,
    message: str = "",
) -> Tuple[Optional[TeamRequest], Optional[str], int]:
    """
    Create a new team-up or project-join request.
    Returns: (request, error_message, http_status_code)
    """
    # Rule: Cannot send request to yourself
    if sender_id == recipient_id:
        return None, "You cannot send a team-up request to yourself.", 400

    # Rule: Check if recipient exists
    recipient = db.session.get(User, recipient_id)
    if not recipient:
        return None, "The recipient student does not exist.", 404

    # If project-specific join request
    if project_id:
        project = db.session.get(Project, project_id)
        if not project:
            return None, "The requested project does not exist.", 404

        # Rule: Cannot request to join your own project
        if project.owner_id == sender_id:
            return None, "You cannot send a request to join your own project.", 400

        # Rule: Cannot request to join if already a member
        if project.is_member(sender_id):
            return None, "You are already a member of this project.", 400

        # Rule: Project must be looking for teammates
        if project.status != "looking_for_teammates":
            return None, "This project is no longer looking for teammates.", 409

        # Verify recipient is indeed the project owner
        if project.owner_id != recipient_id:
            return None, "Join requests must be sent directly to the project lead.", 400

    # Truncate/sanitize message
    clean_msg = (message or "").strip()[:300] or None

    # Application-level duplicate pending request check
    existing_pending = TeamRequest.query.filter_by(
        sender_id=sender_id,
        recipient_id=recipient_id,
        project_id=project_id,
        status="pending",
    ).first()

    if existing_pending:
        return None, "You already have a pending request with this student/project.", 409

    try:
        new_request = TeamRequest(
            sender_id=sender_id,
            recipient_id=recipient_id,
            project_id=project_id,
            message=clean_msg,
            status="pending",
        )
        db.session.add(new_request)
        db.session.commit()
        return new_request, None, 201

    except IntegrityError:
        db.session.rollback()
        # Database partial unique index caught duplicate
        return None, "You already have a pending request with this student/project.", 409
    except Exception:
        db.session.rollback()
        return None, "An unexpected error occurred while sending your request.", 500


def accept_team_request(request_id: int, current_user_id: int) -> Tuple[bool, str, int]:
    """
    Accept a pending request atomically.
    If project join: adds sender to project_members within the exact same transaction.
    Re-checks that project is still 'looking_for_teammates'.
    Returns: (success, message, http_status_code)
    """
    try:
        # 1. Fetch fresh record from DB
        req = db.session.get(TeamRequest, request_id)
        if not req:
            return False, "Request not found.", 404

        # 2. Permission check: Only the recipient can accept
        if req.recipient_id != current_user_id:
            return False, "You do not have permission to accept this request.", 403

        # 3. Status check: Only pending requests can be accepted
        if req.status != "pending":
            return False, f"This request is already {req.status}.", 409

        # 4. If request is to join a project, validate project state
        if req.project_id:
            project = db.session.get(Project, req.project_id)
            if not project:
                return False, "The associated project no longer exists.", 404

            # Rule: Re-check that project is still looking for teammates
            if project.status != "looking_for_teammates":
                # Stale request: DO NOT accept. Return 409 and leave request pending so owner can reject it
                return False, "This project is no longer looking for teammates.", 409

            # Rule: Re-check sender is not already a member
            if project.is_member(req.sender_id):
                req.status = "accepted"
                db.session.commit()
                return True, "Request accepted. Student was already a member.", 200

            # Atomic transaction: insert member AND update request status
            pm = ProjectMember(project_id=project.id, user_id=req.sender_id)
            db.session.add(pm)

        # Update request status conditionally to prevent race conditions
        rows_updated = TeamRequest.query.filter_by(
            id=req.id,
            status="pending"
        ).update({"status": "accepted", "updated_at": utc_now()})

        if rows_updated == 0:
            db.session.rollback()
            return False, "This request was already handled.", 409

        db.session.commit()
        return True, "Request accepted successfully!", 200

    except IntegrityError:
        db.session.rollback()
        return False, "Database constraint violation occurred during acceptance.", 409
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to accept request: {str(e)}", 500


def reject_team_request(request_id: int, current_user_id: int) -> Tuple[bool, str, int]:
    """
    Reject a pending request. Only recipient can reject.
    """
    req = db.session.get(TeamRequest, request_id)
    if not req:
        return False, "Request not found.", 404

    if req.recipient_id != current_user_id:
        return False, "You do not have permission to reject this request.", 403

    if req.status != "pending":
        return False, f"This request is already {req.status}.", 409

    rows_updated = TeamRequest.query.filter_by(
        id=req.id,
        status="pending"
    ).update({"status": "rejected", "updated_at": utc_now()})

    if rows_updated == 0:
        return False, "This request was already handled.", 409

    db.session.commit()
    return True, "Request declined.", 200


def cancel_team_request(request_id: int, current_user_id: int) -> Tuple[bool, str, int]:
    """
    Cancel a pending request. Only sender can cancel.
    """
    req = db.session.get(TeamRequest, request_id)
    if not req:
        return False, "Request not found.", 404

    if req.sender_id != current_user_id:
        return False, "You do not have permission to cancel this request.", 403

    if req.status != "pending":
        return False, f"This request is already {req.status}.", 409

    rows_updated = TeamRequest.query.filter_by(
        id=req.id,
        status="pending"
    ).update({"status": "cancelled", "updated_at": utc_now()})

    if rows_updated == 0:
        return False, "This request was already handled.", 409

    db.session.commit()
    return True, "Request cancelled.", 200
