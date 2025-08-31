from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .logging_config import configure_logging, get_logger
from .routers.health import router as health_router
from .routers.convert import router as convert_router
from .versioning import get_version

def create_app() -> FastAPI:
    configure_logging()
    log = get_logger(__name__)

    app = FastAPI(
        title="GLB → STL Converter",
        version=get_version(),
        description="Convert GLB (non-Draco) to STL with unit/axis normalization and light repairs."
    )

    if settings.CORS_ALLOW_ALL:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    def root():
        return {"service": settings.SERVICE_NAME, "version": get_version(), "env": settings.ENV}

    app.include_router(health_router)                                # /health/...
    app.include_router(convert_router, prefix=settings.API_PREFIX)   # /api/v1/...

    @app.on_event("startup")
    async def on_startup():
        log.info("service_startup", extra={"service": settings.SERVICE_NAME, "env": settings.ENV})

    @app.on_event("shutdown")
    async def on_shutdown():
        log.info("service_shutdown", extra={"service": settings.SERVICE_NAME})

    return app

app = create_app()
