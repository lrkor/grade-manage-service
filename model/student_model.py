from pydantic import BaseModel


class StudentSchema(BaseModel):
    id: int
    name: str
    class_name: str
    last_grade: float

    class Config:
        from_attributes = True


class CreatStudentModel(BaseModel):
    name: str
    class_id: str

    class Config:
        from_attributes = True
