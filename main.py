"""
Predixion AI Research Agent - Application Entrypoint
Run this file to launch the server:
    python main.py
Then open http://localhost:8000 in your browser.
"""
import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print("================================================================")
    print(" PREDIXION AI RESEARCH AGENT - STARTING PLATFORM SERVER")
    print(f" Web UI:      http://localhost:{settings.PORT}")
    print(f" API Docs:    http://localhost:{settings.PORT}/docs")
    print(f" Health API:  http://localhost:{settings.PORT}/api/health")
    print("================================================================")
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)
