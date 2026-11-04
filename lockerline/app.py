"""The application: settings read once, the schema created and seeded before the first request, routers mounted,
one error handler."""
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .db import init_db, make_engine, make_sessionmaker
from .handlers import install_handlers
from .routers import doors
from .routers import drops as drops_router
from .routers import parcels as parcels_router
from .routers import pickups as pickups_router
from .routers import INTERNAL
from .schemas import HealthOut, SettingsOut
from .services.seed import seed
from .settings import Settings

STATIC = Path(__file__).parent / "static"
log = logging.getLogger("lockerline.access")
app_logger = logging.getLogger("lockerline")
app_logger.setLevel(logging.INFO)

# Send LockerLine logs to stdout and remove file handlers from its loggers.
for named_logger in (
    logging.getLogger(),
    logging.getLogger("lockerline"),
    logging.getLogger("lockerline.access"),
    logging.getLogger("lockerline.events"),
):
    for handler in tuple(named_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            named_logger.removeHandler(handler)
            handler.close()

if not any(
    isinstance(handler, logging.StreamHandler)
    and not isinstance(handler, logging.FileHandler)
    for handler in app_logger.handlers
):
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    app_logger.addHandler(stream_handler)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(engine)
        with app.state.sessionmaker() as session:
            seed(session, settings.seed_dir)
        yield
        engine.dispose()

    app = FastAPI(title="LockerLine", version="0.7.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    install_handlers(app)
    for router in (
        doors.router,
        drops_router.router,
        parcels_router.router,
        pickups_router.router,
    ):
        app.include_router(router)

    @app.get(
        "/settings",
        response_model=SettingsOut,
        tags=["runtime"],
        summary="Read active locker policy",
    )
    def read_settings() -> SettingsOut:
        return SettingsOut(free_window_hours=settings.free_window_hours)

    @app.get(
        "/healthz",
        response_model=HealthOut,
        tags=["runtime"],
        summary="Check app and database availability",
        responses={500: INTERNAL},
    )
    def health() -> HealthOut:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return HealthOut(status="ok")

    def openapi_schema():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        schema["paths"]["/towers/{tower}/doors"]["get"]["responses"].pop(
            "422", None
        )

        for path, method in (
            ("/towers/{tower}/doors/{no}", "get"),
            ("/parcels/{parcel_id}", "get"),
        ):
            schema["paths"][path][method]["responses"].pop("422", None)

        app.openapi_schema = schema
        return schema

    app.openapi = openapi_schema

    @app.middleware("http")
    async def log_request(request, call_next):
        request.state.request_id = uuid4().hex
        started = perf_counter()
        response = await call_next(request)

        log.info(
            "request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started) * 1000,
        )
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    return app


app = create_app()