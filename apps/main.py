from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.generator import generate_video

app = FastAPI(title="AI Video Generator", version="1.0.0")

# Allow the web form (index.html) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    topic: str

@app.get("/")
def root():
    return {"status": "AI Video Generator is running"}

@app.post("/generate-video")
def create_video(request: VideoRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    try:
        result = generate_video(request.topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
