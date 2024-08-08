from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from common.tool import generate_uuid
from db.db import Database, get_db_session
from model.db_model import DbStudent, DbTbClass
from model.response import APIResponse
from model.student_model import CreatStudentModel

router = APIRouter(
    prefix="/student",
    tags=["Student"],
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
async def get_students(
        class_id: Optional[str] = None,
        name: Optional[str] = None,
        page: int = Query(1, gt=0),
        page_size: int = Query(10, gt=0, le=100)
):
    session = get_db_session(engine)
    # 获取每个学生最新成绩的子查询
    try:
        # 创建一个别名来用于连接子查询
        query = (
            session.query(
                DbStudent.id.label('student_id'),
                DbStudent.name.label('student_name'),
                DbTbClass.name.label('class_name'),
                DbTbClass.id.label('class_id'),
            )
            .outerjoin(DbTbClass, DbStudent.class_id == DbTbClass.id)
            .order_by(desc(DbStudent.created_time))  # 按时间倒序排序
        )

        if class_id:
            query = query.filter(DbTbClass.id == class_id)

        if name:
            query = query.filter(DbStudent.name.ilike(f'%{name}%'))

        total = query.count()

        results = query.offset((page - 1) * page_size).limit(page_size).all()

        data = [
            StudentGradeResponse(
                id=student_id,
                name=student_name,
                class_name=class_name,
                class_id=class_id,
            )
            for student_id, student_name, class_name, class_id in results
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
async def create_student(student: CreatStudentModel):
    session = get_db_session(engine)
    try:
        # listArr = ['王若宸', '翟嘉晟', '王梓宸', '宋恩硕', '李淼', '陈忠鹏', '葛君祥', '陈振宇', '王若杰', '邱海洋',
        #            '潘星宇', '陈夏森', '叶峻熙', '王腾骏', '鲍俊熙', '朱锦鹏', '李佳蒴', '余子骞', '王子轩', '王艺泽',
        #            '冯易博', '郭一鸣', '石天佑', '徐巳龙', '朱铭昊', '姚沁松', '朱博衍', '翁鸣宇', '李晨灏', '杨淼淼',
        #            '沈昕', '董文萱', '汤心怡', '杨瑾玥', '汪姝伊', '卢宇芝', '穆梓晗', '王诗懿', '陈雅馨', '李梓妍',
        #            '张可佳', '蔡欣桐']
        #
        # students_data = []
        # createdTime = datetime.now()
        # for x in range(len(listArr)):
        #     students_data.append({
        #         "id": generate_uuid(),
        #         "name": listArr[x],
        #         "class_id": student.class_id,
        #         "created_time": createdTime,
        #     })
        #
        # new_student = [
        #     DbStudent(id=row['id'], name=row['name'], class_id=row['class_id'], created_time=row['created_time']) for
        #     row in students_data]
        # session.bulk_save_objects(new_student)
        # 判空处理
        if not student.name:
            raise HTTPException(status_code=400, detail="Student name cannot be empty")

        if not student.class_id:
            raise HTTPException(status_code=400, detail="class id cannot be empty")

        db_student = DbStudent(id=generate_uuid(), name=student.name, class_id=student.class_id,
                               created_time=datetime.now())
        session.add(db_student)
        session.commit()
        return APIResponse(
            status=True,
            data={"id": ''},
            message="Student created successfully",
            code=201
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{student_id}", response_model=APIResponse)
async def delete_student(student_id: str):
    session = get_db_session(engine)
    try:
        db_student = session.query(DbStudent).filter_by(id=student_id).first()
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")

        session.delete(db_student)
        session.commit()
        return APIResponse(
            status=True,
            data={},
            message="Student deleted successfully",
            code=200
        )

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{student_id}", response_model=APIResponse)
async def update_student(student_id: str, student: CreatStudentModel):
    session = get_db_session(engine)
    try:
        db_student = session.query(DbStudent).filter_by(id=student_id).first()
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")

        db_student.name = student.name
        db_student.class_id = student.class_id
        session.commit()
        return APIResponse(
            status=True,
            data={},
            message="Student updated successfully",
            code=200
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
