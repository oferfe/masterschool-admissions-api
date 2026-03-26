"""FastAPI application entry point for the Admissions System API.

Creates the app, loads the flow configuration on startup via the
lifespan hook, and mounts all route modules.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services.flow_service import load_flow_config
from src.routes.users import router as users_router
from src.routes.flow import router as flow_router
from src.routes.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — loads flow config before serving requests."""
    load_flow_config()
    yield


app = FastAPI(title="Admissions System API", lifespan=lifespan)

app.include_router(users_router)
app.include_router(flow_router)
app.include_router(tasks_router)

@app.get("/")
async def root():
    """Root endpoint to verify the API is running."""
    return {
        "message": "Welcome to the Admissions System API!",
        "hint": "Visit /docs to see the API documentation and test endpoints."
    }
