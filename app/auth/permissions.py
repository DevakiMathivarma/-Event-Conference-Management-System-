from fastapi import Depends, HTTPException, status

from app.auth.current_user import get_current_user
from app.models.user import User, UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


def require_event_organizer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.EVENT_ORGANIZER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event Organizer access required.")
    return current_user


def require_speaker(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SPEAKER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Speaker access required.")
    return current_user


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required.")
    return current_user


def require_attendee(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ATTENDEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendee access required.")
    return current_user


# admin or event organizer - event/venue/session/ticket setup and
# management, matching our confirmed decision that both can create venues
def require_admin_or_organizer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.EVENT_ORGANIZER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Event Organizer access required.")
    return current_user


# admin, organizer, or staff - day-to-day event operations like check-in
def require_event_staff_side(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.EVENT_ORGANIZER, UserRole.STAFF):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event staff access required.")
    return current_user


def require_any_role(current_user: User = Depends(get_current_user)) -> User:
    return current_user