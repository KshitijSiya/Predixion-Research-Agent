import asyncio
import sys
import os
import httpx

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode("ascii"))

async def test_fastapi_server():
    safe_print("\n==================================================")
    safe_print(" RUNNING MILESTONE 4 (FASTAPI + REACT) TESTS")
    safe_print("==================================================")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        res = await client.get("/api/health")
        safe_print(f" /api/health status: {res.status_code}")
        assert res.status_code == 200
        health_data = res.json()
        safe_print(f" Health payload: {health_data}")
        assert health_data["status"] == "healthy"
        safe_print(" [PASS] Health check endpoint passed.")

        # 2. Presets check
        res = await client.get("/api/presets")
        safe_print(f" /api/presets status: {res.status_code}")
        assert res.status_code == 200
        presets = res.json()
        safe_print(f" Presets count: {len(presets)}")
        assert len(presets) == 4
        safe_print(" [PASS] Rubric presets endpoint passed.")

        # 3. Serve Frontend index.html
        res = await client.get("/")
        safe_print(f" / (Frontend UI) status: {res.status_code}")
        assert res.status_code == 200
        assert "Predixion AI" in res.text
        assert "React" in res.text
        safe_print(" [PASS] React Frontend served correctly by FastAPI.")

    safe_print("\n==================================================")
    safe_print(" ALL MILESTONE 4 TESTS PASSED SUCCESSFULLY!")
    safe_print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_fastapi_server())
