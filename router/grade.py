import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from common.tool import generate_uuid
from db.db import Database, get_db_session
from model.db_model import DbStudent, DbTbClass, DbGrade
from model.grade_model import GradeResponse, CreatGradeModel
from model.response import APIResponse

router = APIRouter(
    prefix="/grade",
    tags=["Grade"],
    responses={404: {"description": "404 Not Found"}},
)

database = Database()
engine = database.get_db_connection()


class StudentGradeResponse(BaseModel):
    id: str
    name: str
    class_name: str
    class_id: str

    class Config:
        from_attributes = True


@router.get("", response_model=APIResponse)
async def get_grades(
        year: Optional[str] = None,
        semester: Optional[str] = None,
        exam: Optional[str] = None,
        class_id: Optional[str] = None,
        name: Optional[str] = None,
        page: int = Query(1, gt=0),
        page_size: int = Query(10, gt=0, le=100)
):
    session = get_db_session(engine)
    try:
        query = (
            session.query(
                DbGrade.id.label('grade_id'),
                DbGrade.score.label('score'),
                DbGrade.year.label('year'),
                DbGrade.semester.label('semester'),
                DbGrade.exam.label('exam'),
                DbGrade.date.label('date'),
                DbStudent.name.label('student_name'),
                DbTbClass.name.label('class_name')
            )
            .join(DbStudent, DbGrade.student_id == DbStudent.id)
            .join(DbTbClass, DbGrade.class_id == DbTbClass.id)
            .order_by(desc(DbGrade.date))  # 按成绩日期倒序排序
        )
        if year:
            query = query.filter(DbGrade.year == year)

        if semester:
            query = query.filter(DbGrade.semester == semester)

        if exam:
            query = query.filter(DbGrade.exam == exam)

        if class_id:
            query = query.filter(DbGrade.class_id == class_id)

        if name:
            query = query.filter(DbStudent.name.like(f"%{name}%"))

        total = query.count()

        results = query.offset((page - 1) * page_size).limit(page_size).all()

        data = [
            GradeResponse(
                id=row.grade_id,
                score=row.score,
                year=row.year,
                semester=row.semester,
                exam=row.exam,
                date=row.date,
                student_name=row.student_name,
                class_name=row.class_name
            )
            for row in results
        ]

        return APIResponse(
            status=True,
            data={
                "data": data,
                "pagination": {
                    "total_count": total,
                    "page": page,
                    "page_size": page_size,
                }
            },
            message="Success",
            code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=APIResponse)
async def create_grade(grade: CreatGradeModel):
    session = get_db_session(engine)
    try:
        student = session.query(DbStudent).filter(DbStudent.name == grade.name).first()
        student_id = ''
        if not student:
            db_student = DbStudent(id=generate_uuid(), name=grade.name, class_id=grade.class_id,
                                   created_time=datetime.now())
            session.add(db_student)
            student_id = db_student.id

        new_grade = DbGrade(
            id=generate_uuid(),
            score=grade.score,
            year=grade.year,
            semester=grade.semester,
            exam=grade.exam,
            date=datetime.now(),
            student_id=student.id if student else student_id,
            class_id=grade.class_id
        )
        session.add(new_grade)
        session.commit()
        return APIResponse(
            status=True,
            data={"id": new_grade.id},
            message="Success",
            code=201
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{grade_id}", response_model=APIResponse)
async def delete_grade(grade_id: str):
    session = get_db_session(engine)
    try:
        grade = session.query(DbGrade).filter(DbGrade.id == grade_id).first()
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")
        session.delete(grade)
        session.commit()
        return APIResponse(
            status=True,
            data={},
            message="Success",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{grade_id}", response_model=APIResponse)
async def update_grade(grade_id: str, grade: CreatGradeModel):
    session = get_db_session(engine)
    try:
        grade_to_update = session.query(DbGrade).filter(DbGrade.id == grade_id).first()
        if not grade_to_update:
            raise HTTPException(status_code=404, detail="Grade not found")
        grade_to_update.score = grade.score
        grade_to_update.year = grade.year
        grade_to_update.semester = grade.semester
        grade_to_update.exam = grade.exam
        grade_to_update.date = datetime.now()
        session.commit()
        return APIResponse(
            status=True,
            data={},
            message="Success",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-grades/")
async def import_grades(
        file_id: str,
        class_id: str,
        year: str,
        semester: str,
        exam: str,
):
    session = get_db_session(engine)
    # 找到上传的文件
    file_name = None
    for f in os.listdir('./file'):
        if f.startswith(file_id):
            file_name = os.path.join('./file', f)
            break

    if not file_name or not os.path.exists(file_name):
        raise HTTPException(status_code=404, detail="File not found")

    # 读取Excel文件
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Failed to read Excel file: {str(e)}"})

    # 检查Excel文件的结构
    if "姓名" not in df.columns or "成绩" not in df.columns:
        raise HTTPException(status_code=400,
                            detail="Excel file format incorrect. Required columns: 'student_name', 'score'")

    # 遍历文件内容，导入成绩
    for index, row in df.iterrows():
        student_name = str(row['姓名'])
        score = row['成绩']

        student = session.query(DbStudent).filter(DbStudent.name == student_name).first()
        student_id = ''
        if not student:
            db_student = DbStudent(id=generate_uuid(), name=student_name, class_id=class_id,
                                   created_time=datetime.now())
            session.add(db_student)
            student_id = db_student.id

        grade = DbGrade(
            id=generate_uuid(),
            student_id=student.id if student else student_id,
            class_id=class_id,
            score=score,
            year=year,
            semester=semester,
            exam=exam,
            date=datetime.now()
        )
        session.add(grade)

    session.commit()
    return {"message": "Grades imported successfully"}
