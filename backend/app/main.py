from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload  # import the router

app = FastAPI(title="Code Archaeologist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with a prefix
app.include_router(upload.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Code Archaeologist is running"}