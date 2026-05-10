from typing import Annotated

from pydantic import Field

SerialString = Annotated[str, Field(pattern=r"^\d{6}$")]
String100 = Annotated[str, Field(max_length=100)]
String255 = Annotated[str, Field(max_length=255)]
String255OrNone = Annotated[str | None, Field(default=None, max_length=255)]
