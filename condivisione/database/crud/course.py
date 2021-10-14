from fastapi import HTTPException
from sqlalchemy.orm import Session

from condivisione.authentication import check_permissions
from condivisione.database import schemas, models
from condivisione.database.crud.appointment import create_appointment
from condivisione.database.crud.common import commit
from condivisione.database.crud.server import get_server
from condivisione.database.crud.subjects import get_subject
from condivisione.enums import CourseType, UserType


def get_course(db: Session, id: int) -> models.Course:
    c = db.query(models.Course).filter_by(id=id).first()
    if not c:
        raise HTTPException(404, "Not found")
    return c


def get_courses(db: Session) -> list:
    return db.query(models.Course).all()


def create_course(db: Session, course: schemas.Course, current_user: models.User) -> models.Course:
    s = get_server(db)
    course_permission_check(course, current_user, s)
    get_subject(db, course.subject.id)
    # Todo: Add date enforcement to nearest day in calendar
    db_course = models.Course(topics=course.topics, type=course.type,
                              date=course.date, free_slots=s.max_course_size, subject_id=course.subject.id,
                              host_id=current_user.id)
    return commit(db, db_course)


def update_course(db: Session, id: int, course: schemas.Course, current_user: models.User):
    db_course = get_course(db, id)
    s = get_server(db)
    get_subject(db, course.subject.id)
    course_permission_check(course, current_user, s)
    course_ownership_check(current_user, db_course)
    db_course.subject_id = course.subject.id
    db_course.type = course.type
    db_course.topics = course.topics
    db.commit()
    db.refresh(db_course)
    return db_course


def remove_course(db: Session, id: int, current_user: models.User):
    db_course = get_course(db, id)
    course_ownership_check(current_user, db_course)
    if db_course.appointments:
        raise HTTPException(403, "Not authorized: course has bookings.")
    db.delete(db_course)


def book_course(db: Session, id: int, current_user: models.User) -> models.Course:
    db_course = get_course(db, id)
    if current_user.id in [a.user_id for a in db_course.appointments]:
        raise HTTPException(403, "Already in course!")
    if db_course.free_slots <= 0:
        raise HTTPException(404, "Not found")
    db_course.free_slots -= 1
    db.commit()
    create_appointment(db, current_user, db_course.id)
    db.refresh(db_course)
    return db_course


def toggle_course(db: Session, id: int, current_user: models.User) -> models.Course:
    db_course = get_course(db, id)
    course_ownership_check(current_user, db_course)
    db_course.open = False
    db.commit()
    db.refresh(db_course)
    return db_course


def course_ownership_check(current_user: models.User, db_course: models.Course):
    if db_course.host_id != current_user.id and check_permissions(current_user, level=UserType.ADMIN):
        raise HTTPException(403, "Forbidden")
    if not db_course.open:
        raise HTTPException(403, "Forbidden")


def course_permission_check(course: schemas.Course, current_user: models.User, s: models.Server):
    if not s.teacher_courses_enabled and course.type == CourseType.SCHOOL.value:
        raise HTTPException(403, "Forbidden")
    if course.subject.id not in [i.id for i in
                                 current_user.granted_subjects] and not current_user.type >= UserType.TEACHER.value:
        raise HTTPException(403, "Forbidden")
    if course.type == CourseType.SCHOOL.value and check_permissions(current_user, level=UserType.TEACHER):
        raise HTTPException(403, "Forbidden")
