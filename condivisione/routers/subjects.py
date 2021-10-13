import json

from fastapi import APIRouter, Depends, HTTPException

from condivisione.dependencies import get_auth_token, get_db
from condivisione.authentication import get_current_user, check_permissions
from condivisione.database.crud.subjects import get_subject, get_subjects, create_subject, \
    update_subject, delete_subject
from sqlalchemy.orm import Session
from condivisione.database import schemas, models
from condivisione.enums import UserType
from typing import Optional
import bcrypt

router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
    responses={404: {"description": "Not found"}, 403: {"description": "Access Denied"},
               401: {"description": "Unauthorized"}}
)


@router.get("/", response_model=schemas.SubjectList)
async def read_subjects(db: Session = Depends(get_db)):
    """
    Returns data about the subjects.
    """
    subjects = get_subjects(db)
    return schemas.SubjectList(subjects=[schemas.Subject(id=s.id, name=s.name, teacher=s.teacher,
                                                         day_week=[schemas.Day(name=json.loads(d)['name'],
                                                                               number=json.loads(d)['number']) for d in
                                                                   s.day_week], time=s.time) for s in subjects])


@router.get("/{_id}", response_model=schemas.Subject)
async def read_subject(_id: int, db: Session = Depends(get_db)):
    """
    Returns data about the selected subject.
    """
    s = get_subject(db, _id)
    return schemas.Subject(id=s.id, name=s.name, teacher=s.teacher,
                           day_week=[schemas.Day(name=json.loads(d)['name'],
                                                 number=json.loads(d)['number']) for d in s.day_week], time=s.time)


@router.post("/", response_model=schemas.Subject)
async def forge_subject(subject: schemas.Subject, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """
    Creates a new subject.
    """
    if not (check_permissions(current_user, level=UserType.TEACHER) or
            check_permissions(current_user, level=UserType.ADMIN)):
        raise HTTPException(403)
    s = create_subject(db, subject)
    return schemas.Subject(id=s.id, name=s.name, teacher=s.teacher,
                           day_week=[schemas.Day(name=json.loads(d)['name'], number=json.loads(d)['number']) for d in
                                     s.day_week], time=s.time)


@router.patch("/{_id}", response_model=schemas.Subject)
async def forge_subject(_id: int, subject: schemas.Subject, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """
    Updates the selected subject.
    """
    if not (check_permissions(current_user, level=UserType.TEACHER) or
            check_permissions(current_user, level=UserType.ADMIN)):
        raise HTTPException(403)
    s = update_subject(db, _id, subject)
    return schemas.Subject(id=s.id, name=s.name, teacher=s.teacher,
                           day_week=[schemas.Day(name=json.loads(d)['name'], number=json.loads(d)['number']) for d in
                                     s.day_week], time=s.time)


@router.delete("/{_id}", response_model=schemas.Subject)
async def remove_subject(_id: int, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    """
    Removes the selected subject.
    """
    if not (check_permissions(current_user, level=UserType.TEACHER) or
            check_permissions(current_user, level=UserType.ADMIN)):
        raise HTTPException(403)
    return delete_subject(db, _id)
