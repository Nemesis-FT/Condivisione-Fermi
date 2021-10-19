from typing import List, Optional
from datetime import datetime, time

from pydantic import BaseModel


class Day(BaseModel):
    name: str
    number: int


class Subject(BaseModel):
    id: Optional[int]
    name: str
    teacher: str
    day_week: List[Day]
    time: time

    class Config:
        orm_mode = True


class User(BaseModel):
    id: Optional[int]
    name: str
    surname: str
    email: str
    parent_email: str
    class_number: str
    type: int
    granted_subjects: Optional[List[Subject]]
    # Todo : add bookings

    class Config:
        orm_mode = True


class UserList(BaseModel):
    users: Optional[List[User]]


class UserCreatePlain(User):
    password: str

    class Config:
        orm_mode = True


class UserCreate(User):
    hash: bytes

    class Config:
        orm_mode = True


class Server(BaseModel):
    id: Optional[int]
    name: str
    school: str
    max_course_size: int
    teacher_courses_enabled: bool
    custom_logo: str

    class Config:
        orm_mode = True


class SubjectList(BaseModel):
    subjects: Optional[List[Subject]]


class Appointment(BaseModel):
    course_id: int
    student_id: int
    student_present: bool
    student: Optional[User]

    class Config:
        orm_mode = True


class Course(BaseModel):
    id: Optional[int]
    topics: str
    type: int
    date: datetime
    free_slots: int
    open: bool
    host: Optional[User]
    subject: Optional[Subject]

    class Config:
        orm_mode = True


class CourseDetails(Course):
    appointments: Optional[List[Appointment]]


class CourseList(BaseModel):
    courses: Optional[List[Course]]


class Message(BaseModel):
    id: Optional[int]
    title: str
    content: str
    date: datetime
    type: int

    class Config:
        orm_mode = True


class MessageList(BaseModel):
    messages: List[Message]


class Planetarium(BaseModel):
    server: Server
    version: str
    type: str
