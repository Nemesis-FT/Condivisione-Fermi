from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import UploadFile, HTTPException
import bcrypt

from condivisione.database import schemas, models
from condivisione.database.crud.common import commit
from condivisione.database.crud.subjects import get_subject
from condivisione.enums import UserType


def get_user(db: Session, uid: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == uid).first()
    if not user:
        raise HTTPException(404, "Not found.")
    else:
        return user


def get_user_by_email(db: Session, email: str) -> models.User:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session) -> list:
    return db.query(models.User).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(email=user.email, name=user.name, surname=user.surname, password=user.hash,
                          parent_email=user.parent_email, class_number=user.class_number, type=user.type)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: schemas.UserCreate, uid: int) -> models.User:
    db_user = get_user(db, uid)
    if not db_user:
        return
    db_user.name = user.name
    db_user.surname = user.surname
    if user.hash:
        db_user.password = user.hash
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user


def add_grant(db: Session, user_id: int, subject_id: int, current_user: models.User) -> models.User:
    if not current_user.type == UserType.ADMIN.value:
        raise HTTPException(403, "Forbidden")
    u = get_user(db, user_id)
    s = get_subject(db, subject_id)
    u.granted_subjects.append(s)
    db.commit()
    db.refresh(u)
    return u


def remove_grant(db: Session, user_id: int, subject_id: int, current_user: models.User) -> models.User:
    if not current_user.type == UserType.ADMIN.value:
        raise HTTPException(403, "Forbidden")
    u = get_user(db, user_id)
    s = get_subject(db, subject_id)
    try:
        u.granted_subjects.remove(s)
    except ValueError:
        raise HTTPException(404, "Not found")
    db.commit()
    db.refresh(u)
    return u

