import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router.api import router as api_router

app = FastAPI()

origins = ["http://localhost:8083"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有头部
)

app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host='127.0.0.1', port=8083, log_level="info", reload=True)
    print("running")
