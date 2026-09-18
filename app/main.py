import asyncio

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import SessionLocal
from app.utils.logger import logger
from app.services.auth_service import create_default_admin

from app.routes.auth import router as auth_router
from app.routes.events import router as events_router
from app.routes.venues import router as venues_router
from app.routes.speakers import router as speakers_router
from app.routes.sessions import router as sessions_router
from app.routes.attendees import router as attendees_router
from app.routes.registrations import router as registrations_router
from app.routes.tickets import router as tickets_router
from app.routes.payments import router as payments_router
from app.routes.checkin import router as checkin_router
from app.routes.certificates import router as certificates_router
from app.routes.feedback import router as feedback_router
from app.routes.refunds import router as refunds_router
from app.routes.organizer_dashboard import router as organizer_dashboard_router
from app.routes.admin_dashboard import router as admin_dashboard_router
from app.routes.websocket import router as websocket_router, manager as websocket_manager

app = FastAPI(title="Event & Conference Management System", version="1.0.0")


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------------------------------------------------------------------------
# Global Exception Handling
# ---------------------------------------------------------------------------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):

    logger.warning(f"HTTP {exc.status_code} : {exc.detail} : {request.method} {request.url.path}")

    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    logger.warning(f"Validation failed : {request.method} {request.url.path} : {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"message": "Validation failed.", "errors": exc.errors()})
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled exception : {request.method} {request.url.path} : {str(exc)}")

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An unexpected error occurred."})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------


@app.on_event("startup")
def startup():

    logger.info("Application starting.")

    db = SessionLocal()

    try:

        create_default_admin(db)

    finally:

        db.close()

    logger.info("Application started successfully.")


@app.on_event("startup")
async def capture_event_loop():

    websocket_manager.set_loop(asyncio.get_running_loop())


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/")
def root():

    return {"message": "Event & Conference Management System API", "docs": "/docs"}


@app.get("/health")
def health_check():

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(venues_router)
app.include_router(speakers_router)
app.include_router(sessions_router)
app.include_router(attendees_router)
app.include_router(registrations_router)
app.include_router(tickets_router)
app.include_router(payments_router)
app.include_router(checkin_router)
app.include_router(certificates_router)
app.include_router(feedback_router)
app.include_router(refunds_router)
app.include_router(organizer_dashboard_router)
app.include_router(admin_dashboard_router)
app.include_router(websocket_router)