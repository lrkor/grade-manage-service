import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from common.tool import generate_uuid, handle_nan
from db.db import Database, get_db_session
from model.db_model import DbStudent, DbTbClass, DbGrade
from model.grade_model import GradeResponse, CreatGradeModel, ImportGradeModel, StudentGradeModel, \
    StudentGradeCompareModel
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
                DbTbClass.name.label('class_name'),
                DbTbClass.id.label('class_id')
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
                class_name=row.class_name,
                class_id=row.class_id
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
        session.rollback()
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


@router.post("/import-grades", response_model=APIResponse)
async def import_grades(gradeImp: ImportGradeModel):
    session = get_db_session(engine)
    # 找到上传的文件
    file_name = None
    for f in os.listdir('./file'):
        if f.startswith(gradeImp.file_id):
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

    try:
        # 遍历文件内容，导入成绩
        for index, row in df.iterrows():
            student_name = str(row['姓名'])
            score = row['成绩']

            student = session.query(DbStudent).filter(DbStudent.name == student_name).first()
            student_id = ''
            if not student:
                db_student = DbStudent(id=generate_uuid(), name=student_name, class_id=gradeImp.class_id,
                                       created_time=datetime.now())
                session.add(db_student)
                student_id = db_student.id

            grade = DbGrade(
                id=generate_uuid(),
                student_id=student.id if student else student_id,
                class_id=gradeImp.class_id,
                score=handle_nan(score),
                year=gradeImp.year,
                semester=gradeImp.semester,
                exam=gradeImp.exam,
                date=datetime.now()
            )
            session.add(grade)

        session.commit()
        return APIResponse(
            status=True,
            data={},
            message="Success",
            code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/get-student-grades/{student_id}/{year}/{semester}', response_model=APIResponse)
async def get_student_grades(student_id: str, year: str, semester: str):
    session = get_db_session(engine)
    try:
        query = session.query(DbGrade).filter(
            DbGrade.student_id == student_id,
            DbGrade.year == year,
            DbGrade.semester == semester
        )

        # 查询结果
        results = query.all()
        data = [
            StudentGradeModel(
                score=grade.score,
                exam=grade.exam,
            )
            for grade in results
        ]

        data_len = len(data)
        res = []
        for i in range(4):
            res.append(StudentGradeModel(
                score=None,
                exam=str(i + 1)
            ))

        if data_len != 4:
            for item in res:
                for item1 in data:
                    if item.exam == item1.exam:
                        item.score = item1.score

        return APIResponse(
            status=True,
            data=res,
            message="Success",
            code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/get-student-compare-grades/{student_id}/{year}/{semester}')
async def get_student_compare_grades(student_id: str, year: str, semester: str):
    session = get_db_session(engine)
    try:
        if semester == '1':
            prev_semester = '2'
            prev_year = str(int(year) - 1)
        else:
            prev_year = year
            prev_semester = '1'

        # 获取当前学期的成绩
        current_grades = session.query(DbGrade).filter(
            DbGrade.student_id == student_id,
            DbGrade.year == year,
            DbGrade.semester == semester
        ).all()

        current_data = [
            StudentGradeModel(
                score=grade.score,
                exam=grade.exam
            )
            for grade in current_grades
        ]

        # 上一个学期成绩查询
        previous_grades = session.query(DbGrade).filter(
            DbGrade.student_id == student_id,
            DbGrade.year == prev_year,
            DbGrade.semester == prev_semester
        )

        current_data_len = len(current_data)

        previous_data = [
            StudentGradeModel(
                score=grade.score,
                exam=grade.exam
            )
            for grade in previous_grades
        ]

        res = []
        for i in range(4):
            res.append(StudentGradeCompareModel(
                current_score=None,
                previous_score=None,
                exam=str(i + 1)
            ))

        previous_data_len = len(previous_data)
        if previous_data_len != 4 and current_data_len != 4:
            for item in res:
                for item1 in current_data:
                    if item.exam == item1.exam:
                        item.current_score = item1.score
                for item2 in previous_data:
                    if item.exam == item2.exam:
                        item.previous_score = item2.score

        return APIResponse(
            status=True,
            data=res,
            message="Success",
            code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
