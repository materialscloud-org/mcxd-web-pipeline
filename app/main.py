# main.py
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pymongo.errors import NetworkTimeout, ServerSelectionTimeoutError

from .routers import mc2d_router, mc3d_router

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
ROOT_PATH = os.environ.get("ROOT_PATH", "")

# Initialize MongoDB client (shared across routers)
mongo_client = MongoClient(
    MONGODB_URI,
    socketTimeoutMS=5000,
    connectTimeoutMS=5000,
)

app = FastAPI(docs_url="/docs", openapi_url="/openapi.json", root_path=ROOT_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware to catch exceptions
@app.middleware("http")
async def add_exception_handling(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except ServerSelectionTimeoutError:
        return JSONResponse(
            status_code=503, content={"detail": "MongoDB server access timed out."}
        )
    except NetworkTimeout:
        return JSONResponse(status_code=503, content={"detail": "Server timeout."})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"An unexpected error occurred: {str(e)}"},
        )


# Include routers
app.include_router(mc3d_router.router)
app.include_router(mc2d_router.router)
