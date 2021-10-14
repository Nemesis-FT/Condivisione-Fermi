from fastapi import HTTPException
from sqlalchemy.orm import Session

from condivisione.database import schemas, models
from condivisione.database.crud.common import commit
from condivisione.database.crud.users import get_user


def get_course(db: Session, id: int) -> models.Course:
    c = db.query(models.Course).filter_by(id=id).first()
    if not c:
        raise HTTPException(404, "Not found")
    return c


def get_appointment(db: Session, user_id: int, course_id: int) -> models.Appointment:
    a = db.query(models.Appointment).filter_by(user_id=user_id, course_id=course_id).first()
    if not a:
        raise HTTPException(404, "Not found")
    return a


def create_appointment(db: Session, current_user: models.User, course_id: int) -> models.Appointment:
    c = get_course(db, course_id)
    if not c.open:
        raise HTTPException(404, "Not found")
    return commit(db, models.Appointment(student_id=current_user.id, course_id=c.id))


def toggle_appointment(db: Session, user_id: int, course_id: int, current_user: models.User) -> models.Appointment:
    u = get_user(db, user_id)
    c = get_course(db, course_id)
    a = get_appointment(db, u.id, c.id)
    if c.host_id != current_user.id:
        raise HTTPException(403, "Forbidden")
    a.student_present = not a.student_present
    db.commit()
    db.refresh(a)
    return a
