import os
import sys
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Resolve pathing for backend imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import HOST, PORT, ENV, validate_config
from backend.scraper import VideoScraper
from backend.rag import RAGEngine

# Initialize FastAPI App
app = FastAPI(
    title="RAG Creator Chatbot",
    description="Engineers Technical Screening - Full-Stack Video Analysis & Comparison Chatbot",
    version="1.0.0"
)

# Enable CORS for local testing flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
scraper = VideoScraper()
rag_engine = RAGEngine()

# Pydantic Schemas
class ProcessRequest(BaseModel):
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

# Core API Routes
@app.on_event("startup")
async def startup_event():
    print(f"\n[STARTUP] Launching RAG Creator Chatbot server on http://{HOST}:{PORT}")
    validate_config()

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serves the premium single-page glassmorphism frontend."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Frontend template index.html not found.")
        
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/api/process")
async def process_videos(request: ProcessRequest):
    """
    Scrapes metadata + transcripts for provided videos, calculates engagement,
    and indexes them into the RAG vector database.
    """
    if not request.youtube_url and not request.instagram_url:
        raise HTTPException(status_code=400, detail="At least one URL (YouTube or Instagram) is mandatory.")
        
    print(f"\n[API /api/process] Received process request:")
    print(f" -> YouTube: {request.youtube_url}")
    print(f" -> Instagram: {request.instagram_url}")
    
    try:
        video_a = None
        video_b = None
        
        # Scrape Video A (YouTube)
        if request.youtube_url:
            video_a = scraper.fetch_metadata_and_transcript(request.youtube_url, "A")
            
        # Scrape Video B (Instagram Reels)
        if request.instagram_url:
            video_b = scraper.fetch_metadata_and_transcript(request.instagram_url, "B")
            
        # Index transcripts into the RAG engine
        rag_engine.index_video_transcripts(video_a, video_b)
        
        # Return cleaned metadata to the client (excluding heavy transcripts to save bandwidth)
        videos_dict = {}
        if video_a:
            videos_dict["A"] = {k: v for k, v in video_a.items() if k != "transcript"}
        if video_b:
            videos_dict["B"] = {k: v for k, v in video_b.items() if k != "transcript"}
            
        response_data = {
            "success": True,
            "videos": videos_dict
        }
        return response_data
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/chat")
async def chat_with_creator_ai(request: ChatRequest):
    """
    Conversational RAG Chat endpoint. Streams the response in real-time
    using Server-Sent Events (SSE), maintaining memory context and providing citations.
    """
    print(f"\n[API /api/chat] User Query: {request.message}")
    
    # Check if vector DB is loaded with data
    if not rag_engine.raw_video_data:
        raise HTTPException(
            status_code=400, 
            detail="No videos have been analyzed yet. Please submit the video URLs first."
        )
        
    # Re-structure history for the RAG engine
    history_list = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # Return Streaming response using text/event-stream
    return StreamingResponse(
        rag_engine.get_streaming_response(request.message, history_list),
        media_type="text/event-stream"
    )
