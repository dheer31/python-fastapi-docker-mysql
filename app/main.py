import logging
import time

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.database import Base, engine
from app import models  # noqa: F401  (ensures models are registered on Base.metadata)
from app.routers import items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(
    title="FastAPI + MySQL Docker Demo",
    description="A production-ready FastAPI project using MySQL, Docker and docker-compose. "
                 "Tables are created automatically on startup if they do not exist.",
    version="1.0.0",
)


def init_db_with_retry(max_retries: int = 15, delay_seconds: int = 3) -> None:
    """
    Try to connect to MySQL and create tables (if not exists).
    Retries because the MySQL container may still be starting up
    when the app container boots (docker-compose does not wait
    for MySQL to be fully READY, only for the container to start).
    """
    attempt = 0
    while attempt < max_retries:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")
            return
        except OperationalError as exc:
            attempt += 1
            logger.warning(
                "Database not ready yet (attempt %s/%s): %s",
                attempt, max_retries, exc,
            )
            time.sleep(delay_seconds)
    raise RuntimeError("Could not connect to the database after multiple retries.")


@app.on_event("startup")
def on_startup() -> None:
    init_db_with_retry()


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "FastAPI + MySQL service is running"}


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}


app.include_router(items.router)
