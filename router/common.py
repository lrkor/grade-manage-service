import os
import shutil

from fastapi import APIRouter, HTTPException
from fastapi import File, UploadFile

from common.tool import generate_uuid
from model.response import APIResponse

router = APIRouter(
    prefix="/common",
    tags=["Common"],
    responses={404: {"description": "404 Not Found"}},
)

UPLOAD_DIR = "./file"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    # 生成唯一的文件 ID
    file_id = str(generate_uuid())
    file_location = os.path.join(UPLOAD_DIR, file_id + "_" + file.filename)

    try:
        # 保存文件
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")

    return APIResponse(
        status=True,
        data={
            "file_id": file_id,
        },
        message="Success",
        code=200
    )
