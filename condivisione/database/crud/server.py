from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import UploadFile, HTTPException
import bcrypt

from condivisione.database import schemas, models


def get_server(db: Session) -> models.Server:
    return db.query(models.Server).first()


def create_server(db: Session) -> models.Server:
    server = models.Server(name="Condivisione", school="Ignota", custom_logo="Condivisione.png")
    db.add(server)
    db.commit()
    return server


def update_server(db: Session, update: schemas.Server) -> models.Server:
    absent = False
    server: models.Server = get_server(db)
    if not server:
        server = models.Server()
        absent = True
    server.name = update.name
    server.school = update.school
    server.max_course_size = update.max_course_size
    server.teacher_courses_enabled = update.teacher_courses_enabled
    server.custom_logo = update.custom_logo
    if absent:
        db.add(server)
        db.commit()
    db.commit()
    db.refresh(server)
    return server
