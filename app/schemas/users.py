from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.schemas import SerialString


class UserBase(BaseModel):
    name: str
    library_card_id: SerialString


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)


class BorrowingResponse(BaseModel):
    id: UUID

    user_serial: str
    book_serial: str

    borrowed_at: datetime
    returned_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
