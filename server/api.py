import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .auth import verify_firebase_token
from .voice_ws import router as voice_router

app = FastAPI(title="GENESIS Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

@app.get("/")
async def root():
    return {"status": "GENESIS Cloud API Online", "cloud_mode": os.environ.get("CLOUD_MODE", "false")}

@app.get("/health")
async def health():
    return {"status": "ok"}
