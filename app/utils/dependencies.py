from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    page: int
    size: int
    offset: int


def get_pagination_params(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
) -> PaginationParams:
    offset = (page - 1) * size
    return PaginationParams(page=page, size=size, offset=offset)
