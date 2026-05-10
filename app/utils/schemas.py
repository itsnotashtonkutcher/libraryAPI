from typing import Annotated

from pydantic import AfterValidator

from app.utils.database import LibSerial


def validate_serial(value: str) -> str:
    LibSerial.raise_error_when_invalid_value(value)
    return value


SerialString = Annotated[str, AfterValidator(validate_serial)]
