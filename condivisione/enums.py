from enum import Enum


class UserType(Enum):
    DEFAULT = 0
    PEER = 1
    TEACHER = 2
    ADMIN = 3


class CourseType(Enum):
    PEER = 0
    SCHOOL = 1


class MessageType(Enum):
    INFO = 0
    MAINTENANCE = 1
    DANGER = 2
