import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.db.seed import seed_data
from app.db.session import engine
from app.models.base import Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("app.startup")

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    logger.info("Startup step: init DB schema (create_all)")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Startup failed on DB schema init")
        raise

    logger.info("Startup step: seed data files")
    try:
        seed_data(settings.topic_dictionary_path, settings.mock_users_path, settings.task_keywords_path)
    except Exception:
        logger.exception("Startup failed on seed data")
        raise

    logger.info("Startup completed: app ready")


@app.exception_handler(Exception)
def global_exception_handler(_: Request, exc: Exception):
    logging.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
