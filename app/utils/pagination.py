from functools import wraps
from typing import Any

from fastapi import Request
from furl import furl
from pydantic import create_model

from app.utils.dependencies import PaginationParams


def get_pagination_model_for(record_model: type[Any], label: str):
    # pass valid response_model for endpoint statement
    return create_model(
        f"{record_model}Pagination",
        **{label: list[record_model]},
        next=str | None,
    )


def paginate(label: str, record_model: type[Any]):
    # use only for endpoints with request
    # and pagination_params (app.utils.dependencies.get_pagination_params) defined

    def decorator(func):
        func.response_model = get_pagination_model_for(record_model, label)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise RuntimeError("Define request in endpoint arguments.")

            records = await func(*args, **kwargs)

            params: PaginationParams = kwargs.get("page_params")
            if not params:
                raise RuntimeError(
                    "There are no pagination params in endpoint definition."
                )
            # params already validated by Query objects in dependency
            page = params.page
            size = params.size

            next_link = None
            if len(records) == size:
                link = furl(str(request.url))
                link.args["page"] = page + 1
                next_link = link.url

            return {label: records, "next": next_link}

        return wrapper

    return decorator
