from pydantic import BaseModel, ConfigDict

from app.utils.schemas import SerialString


class BookBase(BaseModel):
    title: str
    author: str


class BookCreate(BookBase):
    serial_number: SerialString


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None


class BookResponse(BookBase):
    serial_number: str
    model_config = ConfigDict(from_attributes=True)


class BookWithStatus(BookResponse):
    is_borrowed: bool
