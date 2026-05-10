import re
from typing import Annotated

from sqlalchemy import types
from sqlalchemy.orm import mapped_column


class LibSerial(types.TypeDecorator):
    impl = types.Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        self.raise_error_when_invalid_value(value)

        return int(value)

    def process_result_value(self, value: int, _):
        return f"{value:06d}"

    @staticmethod
    def raise_error_when_invalid_value(value: str):
        if not re.match(r"^\d{6}$", value):
            raise ValueError("Value for library serial should be six digit number.")
        return int(value)


type LibPrimaryKey = Annotated[str, mapped_column(LibSerial, primary_key=True)]
