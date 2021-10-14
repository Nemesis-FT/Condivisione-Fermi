import json

from sqlalchemy import Integer, String, LargeBinary, Column, Boolean, ForeignKey, SmallInteger, DateTime, Float, JSON, \
    Time, Table
from sqlalchemy.orm import relationship, backref
from condivisione.database.schemas import User as UserSchema, Course as CourseSchema, CourseDetails, \
    Subject as SubjectSchema, Day, Appointment as AppointmentSchema

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

    granted_subjects = relationship("Subject", secondary=granted_subject, backref="users", lazy="subquery")
    appointments = relationship("Appointment", backref="student")
    courses = relationship("Course", backref="host")

    def to_schema(self):
        return UserSchema(id=self.id, name=self.name, surname=self.surname, email=self.email,
                          parent_email=self.parent_email, class_number=self.class_number, type=self.type)


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
    open = Column(Boolean, nullable=False, default=True)

    host_id = Column(Integer, ForeignKey("user.id"))
    subject_id = Column(Integer, ForeignKey("subject.id"))

    def to_schema(self, details=False):
        if details:
            return CourseDetails(id=self.id, topics=self.topics, type=self.type, date=self.date,
                                 free_slots=self.free_slots,
                                 open=self.open, host=self.host.to_schema(), subject=self.subject.to_schema(),
                                 appointments=[a.to_schema() for a in self.appointments])
        return CourseSchema(id=self.id, topics=self.topics, type=self.type, date=self.date, free_slots=self.free_slots,
                            open=self.open, host=self.host.to_schema(), subject=self.subject.to_schema())


class Subject(Base):
    __tablename__ = "subject"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    teacher = Column(String, nullable=True)
    day_week = Column(JSON, nullable=True)
    time = Column(Time, nullable=True)

    courses = relationship("Course", backref="subject")

    def convert_day(self):
        return [Day(name=json.loads(d)['name'], number=json.loads(d)['number']) for d in self.day_week]

    def to_schema(self):
        return SubjectSchema(id=self.id, name=self.name, teacher=self.teacher, time=self.time,
                             day_week=self.convert_day())


class Appointment(Base):
    __tablename__ = "appointment"
    student_present = Column(Boolean, default=False, nullable=False)

    student_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id"), primary_key=True)
    course = relationship("Course", backref="appointments")

    def to_schema(self):
        return AppointmentSchema(course_id=self.course_id, student_id=self.student_id, student_present=self.student_present,
                                 student=self.student.to_schema())


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(Integer, nullable=False, default=0)
