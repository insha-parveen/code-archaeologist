from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Code Archaeologist API")

# This allows the frontend (localhost:5173) to talk to the backend (localhost:8000)
# Without this, the browser blocks cross-origin requests for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Code Archaeologist is running"}