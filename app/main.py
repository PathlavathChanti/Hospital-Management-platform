from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db import Base, engine
from app.routes import health, auth, doctors, appointments
from app.logging_conf import setup_logging, RequestIDMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (Alembic is preferred in production)."""
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Hospital Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Structured JSON logging + request-ID middleware
setup_logging()
app.add_middleware(RequestIDMiddleware)

# Register routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
