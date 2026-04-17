"""
Root API Router
===============

Entry point router that mounts versioned API routers.

Responsibilities:
-----------------
• Attach versioned APIs (v1, future v2, etc.)
• Maintain clean API versioning strategy

Architecture:
-------------
main.py → root router → versioned routers (v1, v2)
"""

# =========================================================
# IMPORTS
# =========================================================

from fastapi import APIRouter

from app.api.v1.api import api_router as v1_router


# =========================================================
# ROOT ROUTER INITIALIZATION
# =========================================================

router = APIRouter()


# =========================================================
# VERSIONED ROUTE REGISTRATION
# =========================================================

# API Version 1
router.include_router(v1_router, prefix="/api/v1")