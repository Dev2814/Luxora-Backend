from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from swagger_ui_bundle import swagger_ui_path
from contextlib import asynccontextmanager

from app.core.log_config import setup_logging
from app.core.logger import log_event

from app.api.v1.api import api_router
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.api.v1.auth.error_handler import auth_exception_handler
from app.core.security_headers_middleware import SecurityHeadersMiddleware

from fastapi.staticfiles import StaticFiles
import time
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from sqlalchemy import text

# --------------------------------------------------
# APPLICATION LIFECYCLE
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    log_event("application_startup")

    yield

    # Shutdown
    log_event("application_shutdown")


# --------------------------------------------------
# INITIALIZE LOGGING
# --------------------------------------------------

setup_logging()


# --------------------------------------------------
# CREATE FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="Luxora Backend",
    description="Enterprise E-Commerce Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
def custom_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Luxora API Docs",
        swagger_js_url=f"{swagger_ui_path}/swagger-ui-bundle.js",
        swagger_css_url=f"{swagger_ui_path}/swagger-ui.css",
    )

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# --------------------------------------------------
# GLOBAL ERROR HANDLER
# --------------------------------------------------

app.add_exception_handler(Exception, auth_exception_handler)


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

app.add_middleware(RateLimitMiddleware)

app.add_middleware(SecurityHeadersMiddleware)


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    start = time.perf_counter()

    db.execute(text("SELECT 1"))

    latency = (time.perf_counter() - start) * 1000

    return {
        "status": "ok",
        "latency_ms": round(latency, 2)
    }