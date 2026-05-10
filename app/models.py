import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.database import LibPrimaryKey


class User(Base):
    library_card_id: Mapped[LibPrimaryKey]
    # only name for simplicity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    borrowings: Mapped[list["Borrowing"]] = relationship(
        "Borrowing", back_populates="user"
    )


class Book(Base):
    serial_number: Mapped[LibPrimaryKey]
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)

    borrowing_history: Mapped[list["Borrowing"]] = relationship(
        "Borrowing", back_populates="book", cascade="all, delete-orphan"
    )


class Borrowing(Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    book_serial: Mapped[int] = mapped_column(
        ForeignKey("books.serial_number"), nullable=False
    )
    user_serial: Mapped[int] = mapped_column(
        ForeignKey("users.library_card_id"), nullable=False
    )

    borrowed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="borrowing_history")
    user: Mapped["User"] = relationship("User", back_populates="borrowings")
