import asyncio
import logging
import time
from typing import Callable, Optional, Dict, Any, List
from backend.models.request import ResearchRequest
from backend.models.report import ResearchReport, ExecutionMetadata
from backend.models.plan import ResearchPlan
from backend.models.tool_result import SearchCandidate, ScrapedDocument
from backend.core.planner import planner
from backend.core.synthesizer import synthesizer
from backend.core.verifier import verifier
from backend.tools.search_tool import search_tool
from backend.tools.scraper_tool import scraper_tool

logger = logging.getLogger("agent.orchestrator")

class AgentOrchestrator:
    """
    Deterministic Planner-Executor-Critic State Machine.
    Coordinates query decomposition, parallel tool retrieval,
    sanitization, grounded synthesis, and citation verification.
    """

    async def run(
        self,
        request: ResearchRequest,
        on_step_update: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> ResearchReport:
        """
        Executes the full research pipeline.
        Optionally emits step updates for reactive UI streaming.
        """
        start_overall = time.time()
        sim_failure = request.simulate_failure or "none"

        # --- STEP 1: PLANNING ---
        t_plan_start = time.time()
        if on_step_update:
            on_step_update("planning", {"status": "in_progress", "message": "Analyzing query and formulating plan..."})
            
        plan: ResearchPlan = await planner.create_plan(request.query)
        plan_duration = round(time.time() - t_plan_start, 3)
        
        if on_step_update:
            on_step_update("planning", {
                "status": "completed", 
                "plan": plan.model_dump(), 
                "duration_sec": plan_duration
            })

        # --- STEP 2: TOOL DISPATCH & RETRIEVAL ---
        t_tools_start = time.time()
        if on_step_update:
            on_step_update("searching", {
                "status": "in_progress", 
                "queries": [t.search_query for t in plan.sub_tasks]
            })

        # 2a. Parallel Search
        search_queries = [t.search_query for t in plan.sub_tasks]
        candidates: List[SearchCandidate] = await search_tool.search_multi(
            search_queries, 
            max_results_per_query=3,
            simulate_failure="empty_results" if sim_failure == "empty_results" else "none"
        )

        # 2b. Deep Scraping (Top candidate URLs if in 'deep' mode)
        scraped_docs: List[ScrapedDocument] = []
        if request.mode == "deep" and candidates:
            if on_step_update:
                on_step_update("scraping", {
                    "status": "in_progress", 
                    "target_urls": [c.url for c in candidates[:3]]
                })
            
            top_urls = [c.url for c in candidates[:3]]
            scraped_docs = await scraper_tool.scrape_multi(
                top_urls, 
                simulate_failure="bad_scrape" if sim_failure == "bad_scrape" else "none"
            )

        tools_duration = round(time.time() - t_tools_start, 3)
        
        if on_step_update:
            on_step_update("retrieval_complete", {
                "status": "completed",
                "candidates_count": len(candidates),
                "scraped_count": len([d for d in scraped_docs if d.status == "success"]),
                "duration_sec": tools_duration
            })

        # --- STEP 3: GROUNDED SYNTHESIS ---
        t_synth_start = time.time()
        if on_step_update:
            on_step_update("synthesizing", {"status": "in_progress", "message": "Synthesizing source-grounded report..."})

        raw_report, llm_resp = await synthesizer.synthesize(
            query=request.query,
            candidates=candidates,
            documents=scraped_docs
        )
        synth_duration = round(time.time() - t_synth_start, 3)

        # --- STEP 4: CITATION VERIFICATION & CRITIC ---
        if on_step_update:
            on_step_update("verifying", {"status": "in_progress", "message": "Verifying citations and factual grounding..."})

        verified_sources, confidence_score, confidence_level, limitations = verifier.verify_and_score(
            raw_report=raw_report,
            candidates=candidates,
            documents=scraped_docs,
            query=request.query
        )

        total_latency = round(time.time() - start_overall, 3)

        execution_metadata = ExecutionMetadata(
            plan_duration_sec=plan_duration,
            tools_duration_sec=tools_duration,
            synthesis_duration_sec=synth_duration,
            total_latency_sec=total_latency,
            sources_retrieved_count=len(candidates),
            sources_retained_count=len(verified_sources),
            primary_provider=llm_resp.provider,
            model_used=llm_resp.model,
            failover_triggered=llm_resp.failover_triggered,
            failover_reason=llm_resp.failover_reason
        )

        final_report = ResearchReport(
            user_question=request.query,
            short_answer=raw_report.get("short_answer", "Research completed."),
            key_findings=raw_report.get("key_findings", []),
            sources_used=verified_sources,
            confidence_level=confidence_level,  # type: ignore
            confidence_score=confidence_score,
            limitations_or_assumptions=limitations,
            suggested_next_steps=raw_report.get("suggested_next_steps", []),
            execution_metadata=execution_metadata
        )

        if on_step_update:
            on_step_update("done", {"status": "completed", "report": final_report.model_dump()})

        return final_report

orchestrator = AgentOrchestrator()
