from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services.flow_service import load_flow_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_flow_config()
    yield


app = FastAPI(title="Admissions System API", lifespan=lifespan)
