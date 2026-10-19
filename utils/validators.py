"""
Reusable validation and normalization utilities.
"""

from urllib.parse import urlparse


def is_safe_url(target: str) -> bool:
    """
    Validate that a redirect target is a safe local relative path.
    Rejects external URLs, scheme-relative URLs (//), and backslash tricks.
    """
    if not target or not isinstance(target, str):
        return False

    target = target.strip()

    # Must start with a single forward slash
    if not target.startswith("/") or target.startswith("//"):
        return False

    # Prevent backslash directory traversal or parser confusion
    if "\\" in target:
        return False

    # Parse and ensure no host or scheme is specified
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return False

    return True


def normalize_email(email: str) -> str:
    """Trim whitespace and convert email address to lowercase."""
    if not email:
        return ""
    return email.strip().lower()


def validate_college_email(email: str, allowed_domain: str = "") -> bool:
    """
    Check if the email belongs to the permitted college domain.
    If allowed_domain is empty, any syntactically valid email domain is accepted.
    """
    if not email or "@" not in email:
        return False

    if not allowed_domain:
        return True

    domain = email.split("@")[-1].strip().lower()
    allowed_domain = allowed_domain.strip().lower().lstrip("@")
    return domain == allowed_domain or domain.endswith("." + allowed_domain)
