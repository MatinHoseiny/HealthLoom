"""
HealthLoom FastAPI Application
Main entry point for the backend API
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time

from config import settings
from database import init_db, close_db, check_db_health

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================
# LIFESPAN CONTEXT MANAGER
# ==============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 HealthLoom API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"LangFuse Enabled: {settings.langfuse_enabled}")
    
    # Initialize database
    try:
        await init_db()
        db_healthy = await check_db_health()
        if db_healthy:
            logger.info("✅ Database connection healthy")
        else:
            logger.warning("⚠️  Database health check failed")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Create upload directory
    settings.upload_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    
    logger.info("✅ HealthLoom API startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 HealthLoom API shutting down...")
    await close_db()
    logger.info("✅ HealthLoom API shutdown complete")


# ==============================================
# FASTAPI APPLICATION
# ==============================================

app = FastAPI(
    title="HealthLoom API",
    description="AI-powered health data aggregation and analysis platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# ==============================================
# MIDDLEWARE
# ==============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)")
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ==============================================
# EXCEPTION HANDLERS
# ==============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "error": str(exc) if settings.is_development else "Internal server error"
        }
    )


# ==============================================
# HEALTH CHECK ENDPOINT
# ==============================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns API and database status
    """
    db_healthy = await check_db_health()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "api_version": "1.0.0",
        "environment": settings.environment,
        "database": "healthy" if db_healthy else "unhealthy",
        "gemini_configured": bool(settings.gemini_api_key),
        "langfuse_enabled": settings.langfuse_enabled
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "HealthLoom API",
        "version": "1.0.0",
        "description": "AI-powered health data aggregation platform",
        "documentation": "/api/docs",
        "health_check": "/health"
    }


# ==============================================
# API ROUTES
# ==============================================

# Import and include routers
from api.routes.users import router as users_router
from api.routes.upload import router as upload_router
from api.routes.chat import router as chat_router
from api.routes.medications import router as medications_router
from api.routes.health import router as health_router

app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(medications_router, prefix="/api/medications", tags=["Medications"])
app.include_router(health_router, prefix="/api/health", tags=["Health Data"])


# ==============================================
# STATIC FILES
# ==============================================

# Serve uploaded files (in production, use CDN/S3)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


# ==============================================
# DEVELOPMENT SERVER
# ==============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
