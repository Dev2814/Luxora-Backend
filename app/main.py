"""
Application Entry Point
======================

Initializes FastAPI application with:

• Middleware configuration
• Routing
• Background jobs
• Logging
• Health monitoring
• Static file serving

Architecture:
-------------
Startup → Middleware → Routes → Services → Database
"""

# =========================================================
# IMPORTS
# =========================================================

from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# from app.infrastructure.scheduler import start_scheduler
from contextlib import asynccontextmanager
import threading
import time

from sqlalchemy.orm import Session
from sqlalchemy import text

from swagger_ui_bundle import swagger_ui_path
from app.infrastructure.cleanup.notification_cleanup import delete_old_notifications

from app.infrastructure.database.session import SessionLocal, get_db
from app.api.v1.api import api_router

from app.jobs.order_scheduler import auto_update_orders

from app.core.log_config import setup_logging
from app.core.logger import log_event

from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.core.security_headers_middleware import SecurityHeadersMiddleware
from app.api.v1.auth.error_handler import auth_exception_handler


# =========================================================
# APPLICATION LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle.
    """

    # --------------------------------------------------
    # STARTUP
    # --------------------------------------------------

    log_event("application_startup")

    def start_scheduler():
        """
        Background scheduler to auto-update order statuses.
        Runs continuously in a separate thread.
        """
        while True:
            db = SessionLocal()
            try:
                auto_update_orders(db)
                delete_old_notifications(db, minutes=1)
            finally:
                db.close()

            time.sleep(60)  # run every 60 seconds

    threading.Thread(target=start_scheduler, daemon=True).start()

    yield

    # --------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------

    log_event("application_shutdown")


# =========================================================
# INITIALIZE LOGGING
# =========================================================

setup_logging()


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Luxora Backend",
    description="Enterprise E-Commerce Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/", include_in_schema=False)
def root():
    return {
        "title": "Luxora",
        "description": "Luxora E-Commerce Application",
    }

# =========================================================
# MIDDLEWARE CONFIGURATION
# =========================================================

# CORS Middleware (Allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)


# =========================================================
# STATIC FILES
# =========================================================

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =========================================================
# CUSTOM DOCUMENTATION
# =========================================================

@app.get("/docs", include_in_schema=False)
def custom_docs():
    """
    Custom Swagger UI documentation endpoint.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Luxora API Docs",
        swagger_js_url=f"{swagger_ui_path}/swagger-ui-bundle.js",
        swagger_css_url=f"{swagger_ui_path}/swagger-ui.css",
    )


# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================

app.add_exception_handler(Exception, auth_exception_handler)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(api_router, prefix="/api/v1")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Verifies:
    • Database connectivity
    • Response latency
    """

    start = time.perf_counter()

    db.execute(text("SELECT 1"))

    latency = (time.perf_counter() - start) * 1000

    return {
        "status": "ok",
        "latency_ms": round(latency, 2)
    }