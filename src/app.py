"""FastAPI application entry point for the Admissions System API.

Creates the app, loads the flow configuration on startup via the
lifespan hook, and mounts all route modules.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services.flow_service import load_flow_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — loads flow config before serving requests."""
    load_flow_config()
    yield


app = FastAPI(title="Admissions System API", lifespan=lifespan)
