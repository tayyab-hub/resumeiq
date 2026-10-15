"""Every user-visible error code, with the three-part message it carries.

Each message answers: what happened, why it may have happened, what to do next.
Nothing here may reference a file path, a library name, or an exception class.
"""

from __future__ import annotations

from typing import NamedTuple


class ErrorSpec(NamedTuple):
    code: str
    http_status: int
    what: str
    why: str
    next_step: str


def _spec(code: str, status: int, what: str, why: str, next_step: str) -> ErrorSpec:
    return ErrorSpec(code, status, what, why, next_step)


# --- Authentication --------------------------------------------------------

INVALID_CREDENTIALS = _spec(
    "INVALID_CREDENTIALS",
    401,
    "We could not sign you in.",
    "The email address or password did not match an active account.",
    "Check both fields and try again. Passwords are case-sensitive.",
)
EMAIL_UNAVAILABLE = _spec(
    "EMAIL_UNAVAILABLE",
    409,
    "This email address cannot be registered.",
    "It may already be associated with an account.",
    "Try signing in instead, or register with a different email address.",
)
TOKEN_MISSING = _spec(
    "TOKEN_MISSING",
    401,
    "You are not signed in.",
    "This page needs an active session and none was found.",
    "Sign in and try again.",
)
TOKEN_EXPIRED = _spec(
    "TOKEN_EXPIRED",
    401,
    "Your session has expired.",
    "Sessions last 30 minutes for security.",
    "Sign in again to continue. Your saved analyses are unaffected.",
)
TOKEN_INVALID = _spec(
    "TOKEN_INVALID",
    401,
    "Your session is not valid.",
    "The session token was malformed, or the account is no longer active.",
    "Sign in again to start a new session.",
)
REFRESH_INVALID = _spec(
    "REFRESH_INVALID",
    401,
    "We could not renew your session.",
    "The renewal token is missing, expired, or was revoked by signing out.",
    "Sign in again to continue.",
)
PASSWORD_INCORRECT = _spec(
    "PASSWORD_INCORRECT",
    401,
    "That password is not correct.",
    "This action requires your current password as confirmation.",
    "Re-enter your current password and try again.",
)

# --- Rate limiting ---------------------------------------------------------

TOO_MANY_ATTEMPTS = _spec(
    "TOO_MANY_ATTEMPTS",
    429,
    "Too many sign-in attempts.",
    "Repeated failed attempts are temporarily blocked to protect your account.",
    "Wait for the period shown in the Retry-After header, then try again.",
)
RATE_LIMITED = _spec(
    "RATE_LIMITED",
    429,
    "You have reached a usage limit.",
    "This endpoint limits how often it can be called by one account.",
    "Wait for the period shown in the Retry-After header, then try again.",
)
AI_QUOTA_EXCEEDED = _spec(
    "AI_QUOTA_EXCEEDED",
    429,
    "You have used today's AI suggestion allowance.",
    "AI suggestions are limited per day to keep the service available to everyone.",
    "Your rule-based analysis is unaffected. AI suggestions reset tomorrow.",
)

# --- Upload and extraction -------------------------------------------------

RESUME_MISSING = _spec(
    "RESUME_MISSING",
    422,
    "No resume file was received.",
    "The upload may have been interrupted, or no file was selected.",
    "Select your PDF resume and submit again.",
)
RESUME_INVALID_TYPE = _spec(
    "RESUME_INVALID_TYPE",
    415,
    "That file is not a PDF.",
    "Only PDF resumes can be read. Renaming a file does not change its format.",
    "Export your resume as a PDF from Word, Google Docs, or Pages, then upload it.",
)
RESUME_TOO_LARGE = _spec(
    "RESUME_TOO_LARGE",
    413,
    "That file is too large.",
    "Resumes are limited to 5 MB. Large files usually contain high-resolution images.",
    "Re-export the PDF with compressed images, or remove large graphics, then retry.",
)
RESUME_EMPTY = _spec(
    "RESUME_EMPTY",
    422,
    "That file is empty.",
    "The file contains no data, which usually means the export or upload failed.",
    "Open the file to confirm it is readable, then export and upload it again.",
)
RESUME_CORRUPT = _spec(
    "RESUME_CORRUPT",
    422,
    "We could not open this PDF.",
    "The file appears to be damaged or was only partially uploaded.",
    "Open it locally to confirm it works, then re-export and upload it again.",
)
RESUME_ENCRYPTED = _spec(
    "RESUME_ENCRYPTED",
    422,
    "This PDF is password-protected.",
    "Protected files cannot be opened for analysis.",
    "Save an unprotected copy of your resume and upload that instead.",
)
RESUME_NO_TEXT_LAYER = _spec(
    "RESUME_NO_TEXT_LAYER",
    422,
    "We could not read any text from this PDF.",
    "It looks like a scan or an image export, so it contains pictures of words rather than words.",
    "Export a text-based PDF from Word or Google Docs and upload that. "
    "You can check by trying to select text in the file.",
)

# --- Job description -------------------------------------------------------

JOB_DESCRIPTION_TOO_SHORT = _spec(
    "JOB_DESCRIPTION_TOO_SHORT",
    422,
    "The job description is too short to analyse.",
    "At least 200 characters are needed to identify requirements reliably.",
    "Paste the full job description, including the requirements section.",
)
JOB_DESCRIPTION_TOO_LONG = _spec(
    "JOB_DESCRIPTION_TOO_LONG",
    422,
    "The job description is too long.",
    "The limit is 8,000 characters, which is longer than almost any real posting.",
    "Paste the role, responsibilities, and requirements, and omit company boilerplate.",
)

# --- Resources and generic -------------------------------------------------

ANALYSIS_NOT_FOUND = _spec(
    "ANALYSIS_NOT_FOUND",
    404,
    "We could not find that analysis.",
    "It may have been deleted, or it belongs to a different account.",
    "Return to your history to see the analyses saved to this account.",
)
USER_NOT_FOUND = _spec(
    "USER_NOT_FOUND",
    404,
    "We could not find that account.",
    "It may have been deleted.",
    "Sign in again, or register a new account.",
)
VALIDATION_ERROR = _spec(
    "VALIDATION_ERROR",
    422,
    "Some of the information provided was not accepted.",
    "One or more fields did not meet the required format.",
    "Correct the highlighted fields and submit again.",
)
INTERNAL_ERROR = _spec(
    "INTERNAL_ERROR",
    500,
    "Something went wrong on our side.",
    "This is a fault in the service, not in anything you did.",
    "Try again in a moment. If it keeps happening, quote the request ID shown below.",
)
DATABASE_UNAVAILABLE = _spec(
    "DATABASE_UNAVAILABLE",
    503,
    "The service is temporarily unavailable.",
    "We could not reach the database.",
    "Wait a moment and try again.",
)
