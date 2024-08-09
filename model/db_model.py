import uuid

from sqlalchemy import Column, Float, ForeignKey, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DbTbClass(Base):
    __tablename__ = 'tb_class'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    value = Column(String, nullable=True)
    students = relationship('DbStudent', back_populates='class_')


class DbStudent(Base):
    __tablename__ = 'student'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    class_id = Column(String, ForeignKey('tb_class.id'), nullable=True)
    created_time = Column(DateTime, nullable=True)
    class_ = relationship('DbTbClass', back_populates='students')
    grades = relationship('DbGrade', back_populates='student', cascade="all, delete-orphan")


class DbGrade(Base):
    __tablename__ = 'grade'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    score = Column(Float, nullable=True)
    year = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    exam = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)
    student_id = Column(String, ForeignKey('student.id'), nullable=True)
    class_id = Column(String, ForeignKey('tb_class.id'))
    student = relationship('DbStudent', back_populates='grades')
