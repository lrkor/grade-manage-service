from typing import Optional

from pydantic import BaseModel


class StudentSchema(BaseModel):
    id: int
    name: str
    class_name: str
    last_grade: float

    class Config:
        from_attributes = True


class CreatGradeModel(BaseModel):
    name: str
    class_id: str
    year: str
    semester: str
    exam: str
    score: float

    class Config:
        from_attributes = True


class ImportGradeModel(BaseModel):
    file_id: str
    class_id: str
    year: str
    semester: str
    exam: str

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    id: str
    student_name: str
    year: str
    semester: str
    exam: str
    class_name: str
    class_id: str
    score: float

    class Config:
        from_attributes = True


class StudentGradeModel(BaseModel):
    exam: str
    score: Optional[float]

    class Config:
        from_attributes = True


class StudentGradeCompareModel(BaseModel):
    exam: str
    current_score: Optional[float]
    previous_score: Optional[float]

    class Config:
        from_attributes = True
