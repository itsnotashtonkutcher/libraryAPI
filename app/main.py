from fastapi import FastAPI

from app.api.books import router as books_router
from app.api.users import router as users_router

app = FastAPI(title="Library API")
app.include_router(users_router)
app.include_router(books_router)
