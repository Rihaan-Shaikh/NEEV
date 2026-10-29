from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid
import time
import logging

from app.core.config import settings
from app.api.v1.api_router import api_router

# Setup secure logging with sensitive data redaction
from app.core.logging_config import setup_secure_logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
setup_secure_logging()
logger = logging.getLogger("neev")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="National Education Evidence & Verification — Phase 4: Release Candidate (Final Implementation, Remediation & Hardening)",
    version="1.0.0-rc1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory rate limiting tracker: {ip_route: [(timestamp)]}
_rate_limits: dict = {}

# Request ID, Security Headers & Rate Limiting Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    # 1. Rate limiting on sensitive endpoints
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    if path in ("/api/v1/auth/login", "/api/v1/auth/forgot-password", "/api/v1/verify"):
        key = f"{client_ip}:{path}"
        now = time.time()
        window = _rate_limits.setdefault(key, [])
        # Prune older than 60s
        _rate_limits[key] = [t for t in window if now - t < 60]
        if len(_rate_limits[key]) >= 30:  # 30 req / min limit
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": "60"},
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests to sensitive endpoint. Please try again in 60 seconds.",
                    "details": None,
                    "request_id": request_id
                }
            )
        _rate_limits[key].append(now)

    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    # 2. Strict Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if path.startswith("/api/v1/auth") or path.startswith("/api/v1/verify") or path.startswith("/api/v1/reports"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        
    return response

# Standard Error Handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": None,
            "request_id": request_id
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    error_details = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        error_details.append({
            "field": loc,
            "message": err.get("msg", "Validation error"),
            "rule_code": "SCH-001"
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed. Please check submitted payload.",
            "details": error_details,
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled error on {request.url.path} (request_id={request_id}): {exc}", exc_info=True)
    # Never expose stack traces or internal secrets to user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred while processing your request. Please contact technical support.",
            "details": None,
            "request_id": request_id
        }
    )

# Mount Health directly at /health as well as through API prefix
from app.api.v1.endpoints import health
app.include_router(health.router, prefix="/health", tags=["Health"])

# Mount API V1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "product": "NEEV — National Education Evidence & Verification",
        "tagline": "Proof Behind Every Record",
        "version": "1.0.0",
        "phase": "Phase 1: Secure Foundation & Enrolment Core",
        "status": "operational",
        "api_docs": "/docs"
    }
