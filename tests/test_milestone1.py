import asyncio
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from backend.models import ResearchRequest, ResearchReport, SourceMetadata
from backend.core.llm_client import llm_client

def safe_print(text: str):
    """Safely prints strings without failing on Windows console cp1252 codecs."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode("ascii"))

async def test_pydantic_contracts():
    safe_print("\n--- 1. Testing Pydantic Contracts ---")
    req = ResearchRequest(query="Compare top 3 vector databases for RAG")
    assert req.query == "Compare top 3 vector databases for RAG"
    assert req.mode == "deep"
    safe_print(" [PASS] ResearchRequest schema valid.")

    report = ResearchReport(
        user_question="Test query",
        short_answer="Short test answer.",
        key_findings=["Finding 1: Qdrant is fast.", "Finding 2: Milvus is scalable."],
        sources_used=[
            SourceMetadata(title="Qdrant Docs", url="https://qdrant.tech", snippet="Vector DB", domain="qdrant.tech")
        ],
        confidence_level="High",
        confidence_score=0.95,
        limitations_or_assumptions=["Assumes open-source deployment."],
        suggested_next_steps=["Benchmark latency."]
    )
    assert report.confidence_score == 0.95
    safe_print(" [PASS] ResearchReport schema valid.")

async def test_groq_primary():
    safe_print("\n--- 2. Testing Primary LLM (Groq openai/gpt-oss-120b) ---")
    messages = [
        {"role": "system", "content": "You are a concise research assistant. Respond in 1 brief sentence without emojis."},
        {"role": "user", "content": "What is Chroma DB?"}
    ]
    resp = await llm_client.generate(messages)
    safe_print(f" Provider: {resp.provider} ({resp.model})")
    safe_print(f" Latency: {resp.latency_sec}s")
    safe_print(f" Response: {resp.content.strip()[:100]}...")
    assert resp.provider == "groq"
    assert resp.model == settings.GROQ_MODEL
    assert len(resp.content) > 10
    safe_print(" [PASS] Groq Primary text generation passed.")

async def test_groq_json():
    safe_print("\n--- 3. Testing Structured JSON Generation ---")
    messages = [
        {"role": "system", "content": "Return valid JSON with keys: query, sub_topics (list of 2 strings)."},
        {"role": "user", "content": "Plan research for: Top vector databases for RAG"}
    ]
    data, resp = await llm_client.generate_json(messages)
    safe_print(f" Parsed JSON keys: {list(data.keys())}")
    assert isinstance(data, dict)
    assert "query" in data or "sub_topics" in data
    safe_print(" [PASS] Structured JSON output parsed successfully.")

async def test_failover_routing():
    safe_print("\n--- 4. Testing Automatic Failover Routing (120B -> 27B) ---")
    messages = [
        {"role": "system", "content": "You are a concise assistant. Respond in 10 words without emojis."},
        {"role": "user", "content": "Explain what Qdrant is."}
    ]
    resp = await llm_client.generate(messages, force_failover=True)
    safe_print(f" Failover Model: {resp.model}")
    safe_print(f" Failover Latency: {resp.latency_sec}s")
    safe_print(f" Failover Triggered: {resp.failover_triggered}")
    safe_print(f" Content: {resp.content.strip()[:100]}...")
    assert resp.model == settings.GROQ_FALLBACK_MODEL
    assert resp.failover_triggered is True
    safe_print(" [PASS] Automatic Failover routing passed.")

async def main():
    safe_print("==================================================")
    safe_print(" RUNNING MILESTONE 1 VERIFICATION SUITE")
    safe_print("==================================================")
    await test_pydantic_contracts()
    await test_groq_primary()
    await test_groq_json()
    await test_failover_routing()
    safe_print("\n==================================================")
    safe_print(" ALL MILESTONE 1 TESTS PASSED SUCCESSFULLY!")
    safe_print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
