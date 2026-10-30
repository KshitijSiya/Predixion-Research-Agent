import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from backend.config import settings
from backend.models.request import ResearchRequest
from backend.models.report import ResearchReport
from backend.core.orchestrator import orchestrator

app = FastAPI(
    title="Predixion AI Research Agent",
    description="Production-grade AI research agent with planning, tool use, citation grounding, and failure handling.",
    version="1.2.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Predixion Assignment Sample Presets
PRESET_QUERIES = [
    {
        "id": "vector_dbs",
        "title": "Vector Databases for RAG",
        "query": "Compare the top 3 open-source vector databases for a startup building RAG products."
    },
    {
        "id": "hr_tech",
        "title": "Indian HR Tech Startups",
        "query": "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning."
    },
    {
        "id": "multi_agent",
        "title": "Multi-Agent Support Pros/Cons",
        "query": "Research the pros and cons of using a multi-agent architecture for customer support automation."
    },
    {
        "id": "agent_memory",
        "title": "Memory in AI Support Agents",
        "query": "Compare different approaches to adding memory in an AI support agent."
    }
]

@app.get("/api/health")
async def health_check():
    """Health and runtime diagnostic endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "primary_model": settings.GROQ_MODEL,
        "fallback_model": settings.GROQ_FALLBACK_MODEL,
        "search_backend": settings.SEARCH_BACKEND,
        "api_version": "1.2.0"
    }

@app.get("/api/presets")
async def get_presets():
    """Returns curated assignment research query presets."""
    return PRESET_QUERIES

@app.post("/api/research", response_model=ResearchReport)
async def conduct_research(request: ResearchRequest):
    """
    Main research orchestrator endpoint.
    Accepts research request, plans, executes tools, synthesizes, and verifies output.
    """
    try:
        report = await orchestrator.run(request)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research agent error: {str(e)}")

# Mount static frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
