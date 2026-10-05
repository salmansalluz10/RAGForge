import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.search import router as search_router
from app.api.v1.rag import router as rag_router
from app.api.v1.chat import router as chat_router
from app.api.v1.collections import router as collections_router
from app.api.v1.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ragforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and extensions
    logger.info("Initializing database and storage directories...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    yield
    # Shutdown
    logger.info("Shutting down RAGForge backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade Document Intelligence & Retrieval-Augmented Generation (RAG) Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request, exc: Exception):
    """Prevent internal trace leakage to clients while logging full details internally."""
    logger.error(f"Unhandled exception at {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact system administrator."},
    )

# Root health check endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Include Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(collections_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
