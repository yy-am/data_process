from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ApiResponse(APIModel, Generic[T]):
    code: str = "OK"
    message: str = "成功"
    data: T
