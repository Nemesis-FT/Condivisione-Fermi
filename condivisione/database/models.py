from sqlalchemy import Integer, String, LargeBinary, Column, Boolean, ForeignKey, SmallInteger, DateTime, Float, JSON, \
    Time, Table
from sqlalchemy.orm import relationship, backref
from condivisione.database.schemas import User as UserSchema

from condivisione.database.db import Base

granted_subject = Table('granted_subject', Base.metadata,
                        Column("user_id", ForeignKey('user.id'), primary_key=True),
                        Column("subject_id", ForeignKey('subject.id'), primary_key=True))


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    parent_email = Column(String, nullable=False)
    class_number = Column(String, nullable=False)
    password = Column(LargeBinary, nullable=False)
    type = Column(SmallInteger, nullable=False, default=0)

    granted_subjects = relationship("Subject", secondary=granted_subject, backref="users")
    appointments = relationship("Appointment", backref="student")
    courses = relationship("Course", backref="host")

    def to_schema(self):
        return UserSchema(uid=self.uid, name=self.name, surname=self.surname, email=self.email)


class Server(Base):
    __tablename__ = "server"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String)
    school = Column(String, nullable=False)
    max_course_size = Column(Integer, default=3, nullable=False)
    teacher_courses_enabled = Column(Boolean, default=False)
    custom_logo = Column(String)


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topics = Column(String, nullable=False)
    type = Column(SmallInteger, nullable=False)
    date = Column(DateTime, nullable=False)
    free_slots = Column(SmallInteger, nullable=False)

    host_id = Column(Integer, ForeignKey("user.id"))
    subject_id = Column(Integer, ForeignKey("subject.id"))


class Subject(Base):
    __tablename__ = "subject"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    teacher = Column(String, nullable=True)
    day_week = Column(JSON, nullable=True)
    time = Column(Time, nullable=True)

    courses = relationship("Course", backref="subject")


class Appointment(Base):
    __tablename__ = "appointment"
    student_present = Column(Boolean, default=False, nullable=False)

    student_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)
    course = relationship("Course", backref="appointments")


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(Integer, nullable=False, default=0)
