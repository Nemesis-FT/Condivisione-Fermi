import json

from fastapi import APIRouter, Depends, HTTPException

from condivisione.dependencies import get_auth_token, get_db
from condivisione.authentication import get_current_user, check_permissions
from condivisione.database.crud.course import get_course, get_courses, create_course, update_course, remove_course, \
    book_course, toggle_course
from sqlalchemy.orm import Session
from condivisione.database import schemas, models
from condivisione.enums import UserType, CourseType
from typing import Optional
import bcrypt

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}, 403: {"description": "Access Denied"},
               401: {"description": "Unauthorized"}}
)


@router.get("/", response_model=schemas.CourseList)
async def read_courses(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns data about the courses.
    """
    courses = get_courses(db)
    return schemas.CourseList(courses=[c.to_schema() for c in courses])


@router.get("/{_id}", response_model=schemas.Course)
async def read_course(_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns data about the selected course.
    """
    course = get_course(db, _id)
    return course.to_schema()


@router.get("/{_id}/details", response_model=schemas.CourseDetails)
async def read_course(_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Returns data about the selected course.
    """
    c = get_course(db, _id)
    if current_user.id != c.host_id and check_permissions(current_user, level=UserType.ADMIN.value):
        raise HTTPException(403, "Forbidden")
    return c.to_schema(details=True)


@router.post("/", response_model=schemas.Course)
async def forge_course(course: schemas.Course, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """
    Creates a new course.
    """
    c = create_course(db, course, current_user)
    return c.to_schema()


@router.put("/{_id}/book", response_model=schemas.Course, tags=["appointments"])
async def book_course_(_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Allows course booking
    """
    c = book_course(db, _id, current_user)
    return c.to_schema()


@router.put("/{_id}/close", response_model=schemas.Course)
async def toggle_course_(_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Allows course to be closed
    """
    c = toggle_course(db, _id, current_user)
    return c.to_schema()


@router.delete("/{_id}")
async def remove_course_(_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Allows course to be removed
    """
    remove_course(db, _id, current_user)
    return HTTPException(204)
