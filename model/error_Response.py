from typing import Optional, Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[Any] = None
