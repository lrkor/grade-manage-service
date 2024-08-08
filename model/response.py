from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    code: int
    status: bool
    message: str
    data: Optional[Any]

    class Config:
        from_attributes = True
