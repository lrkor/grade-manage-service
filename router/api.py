from fastapi import APIRouter

from router import student, grade, common

router = APIRouter()
router.include_router(student.router)
router.include_router(grade.router)
router.include_router(common.router)
