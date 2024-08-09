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


class GradeResponse(BaseModel):
    id: str
    student_name: str
    year: str
    semester: int
    exam: int
    class_name: str
    score: float

    class Config:
        from_attributes = True
