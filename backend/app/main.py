import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="SimpleResolve API",
    description="AI-native AML investigation and graduated account restriction system",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SimpleResolve"}


# Routers are registered here as each phase is completed
from app.api import clients, dashboard, investigations, restrictions, transactions  # noqa: E402

app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(restrictions.router, prefix="/restrictions", tags=["restrictions"])
app.include_router(investigations.router, prefix="/investigations", tags=["investigations"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
