from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load flow config into the in-memory store
    # (will be wired in Phase 3)
    yield
    # Shutdown: nothing to clean up for in-memory storage


app = FastAPI(title="Admissions System API", lifespan=lifespan)
