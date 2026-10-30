import asyncio
import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.request import ResearchRequest
from backend.core.orchestrator import orchestrator

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "ignore").decode("ascii"))

async def test_end_to_end_research():
    safe_print("\n==================================================")
    safe_print(" RUNNING END-TO-END RESEARCH AGENT TEST (MILESTONE 3)")
    safe_print(" Query: 'Compare top 3 open-source vector databases for RAG'")
    safe_print("==================================================")
    
    req = ResearchRequest(
        query="Compare the top 3 open-source vector databases for a startup building RAG products.",
        mode="deep"
    )

    steps_recorded = []
    def step_callback(step_name, data):
        steps_recorded.append(step_name)
        safe_print(f" [PIPELINE EVENT] {step_name.upper()}: {data.get('status', '')}")

    report = await orchestrator.run(req, on_step_update=step_callback)

    safe_print("\n--- AGENT REPORT SUMMARY ---")
    safe_print(f" User Question:    {report.user_question}")
    safe_print(f" Short Answer:     {report.short_answer}")
    safe_print(f"\n Key Findings ({len(report.key_findings)}):")
    for idx, f in enumerate(report.key_findings):
        safe_print(f"   {idx+1}. {f}")
        
    safe_print(f"\n Sources Used ({len(report.sources_used)}):")
    for s in report.sources_used:
        safe_print(f"   * [{s.domain}] {s.title} ({s.url})")
        
    safe_print(f"\n Confidence:       {report.confidence_level} ({report.confidence_score * 100}%)")
    safe_print(f" Limitations:      {len(report.limitations_or_assumptions)} reported")
    safe_print(f" Next Steps:       {len(report.suggested_next_steps)} suggested")
    safe_print(f"\n Telemetry:")
    safe_print(f"   * Total Latency:    {report.execution_metadata.total_latency_sec}s")
    safe_print(f"   * Plan Time:        {report.execution_metadata.plan_duration_sec}s")
    safe_print(f"   * Tool Time:        {report.execution_metadata.tools_duration_sec}s")
    safe_print(f"   * Synthesis Time:   {report.execution_metadata.synthesis_duration_sec}s")
    safe_print(f"   * Model Used:       {report.execution_metadata.model_used}")

    # Assertions
    assert len(report.short_answer) > 20, "Short answer should be substantive"
    assert len(report.key_findings) >= 2, "Should return at least 2 key findings"
    assert len(report.sources_used) >= 1, "Should cite at least 1 verified source"
    assert 0.0 <= report.confidence_score <= 1.0
    assert report.execution_metadata.total_latency_sec > 0
    safe_print("\n [PASS] Full End-to-End Orchestrator Pipeline Executed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_research())
