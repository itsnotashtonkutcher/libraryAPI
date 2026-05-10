from pydantic import BaseModel, ConfigDict

from app.utils.schemas import SerialString, String255, String255OrNone


class BookBase(BaseModel):
    title: String255
    author: String255


class BookCreate(BookBase):
    serial_number: SerialString


class BookUpdate(BaseModel):
    title: String255OrNone
    author: String255OrNone


class BookResponse(BookBase):
    serial_number: SerialString
    model_config = ConfigDict(from_attributes=True)


class BookWithStatus(BookResponse):
    is_borrowed: bool
