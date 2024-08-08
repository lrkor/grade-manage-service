from fastapi import APIRouter

from router import student

router = APIRouter()
router.include_router(student.router)
