from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app import models  # noqa: F401 — registers all models on Base.metadata
from app.routers import health, auth, colleges, companies, experiences, questions, bookmarks, reports, admin


def _build_validation_details(errors: list) -> dict:
    """
    Reshapes Pydantic's error list into a nested dict keyed by field name,
    e.g. {"email": ["not a valid email address"]} — mirrors the old
    marshmallow error shape closely enough that the frontend's existing
    `err.response.data.details` handling (see Register.jsx) keeps working
    unmodified.
    """
    details: dict = {}
    for err in errors:
        loc = [p for p in err["loc"] if p != "body"]
        node = details
        for part in loc[:-1]:
            node = node.setdefault(str(part), {})
        leaf_key = str(loc[-1]) if loc else "_"
        node.setdefault(leaf_key, []).append(err["msg"])
    return details


def create_app(testing: bool = False) -> FastAPI:
    """
    App factory — mirrors the old Flask create_app(config_name) pattern.
    Pass testing=True to run against an isolated in-memory SQLite DB instead
    of the real MySQL database (used by the pytest suite).
    """
    settings = get_settings()
    app = FastAPI(title="Campus Placement Experience Hub API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if testing:
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.state.test_engine = test_engine  # keep a reference alive for the app's lifetime
        app.state.SessionLocal = TestSessionLocal  # exposed so tests can seed data through the same DB

    # --- routers, all under /api to match the old Flask blueprint prefixes ---
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(colleges.router, prefix="/api")
    app.include_router(companies.router, prefix="/api")
    app.include_router(experiences.router, prefix="/api")
    app.include_router(questions.router, prefix="/api")
    app.include_router(bookmarks.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")

    # --- exception handlers: keep the response shape the frontend expects ---

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        body = exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": "Validation failed", "details": _build_validation_details(exc.errors())},
        )

    return app


app = create_app()
