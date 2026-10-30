import logging
from typing import Dict, Any, List
from backend.core.llm_client import llm_client
from backend.models.plan import ResearchPlan, SubTask

logger = logging.getLogger("agent.planner")

PLANNER_SYSTEM_PROMPT = """You are an expert AI Research Planner.
Your job is to analyze a user's research question and create a structured research execution plan.

Rules:
1. Decompose the request into 2 to 4 precise, targeted sub-tasks.
2. For each sub-task, provide an exact search query optimized for a web search engine.
3. Identify key entities, technologies, or organizations mentioned in the query.
4. Output valid JSON strictly following this schema:
{
  "reasoning": "string explaining how you plan to tackle this research topic",
  "key_entities": ["list", "of", "entities"],
  "sub_tasks": [
    {
      "id": 1,
      "description": "What this step investigates",
      "search_query": "specific search engine query",
      "tool": "web_search"
    }
  ]
}
"""

class ResearchPlanner:
    async def create_plan(self, query: str) -> ResearchPlan:
        """
        Generates a structured research plan for a given query.
        """
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a research plan for the following question:\n\n\"{query}\""}
        ]
        
        data, response = await llm_client.generate_json(messages, temperature=0.2)
        
        sub_tasks = []
        for item in data.get("sub_tasks", []):
            sub_tasks.append(SubTask(
                id=item.get("id", len(sub_tasks) + 1),
                description=item.get("description", ""),
                search_query=item.get("search_query", query),
                tool=item.get("tool", "web_search")
            ))
            
        # Fallback if model returned empty tasks
        if not sub_tasks:
            sub_tasks.append(SubTask(
                id=1,
                description=f"Initial research on: {query}",
                search_query=query,
                tool="web_search"
            ))
            
        return ResearchPlan(
            original_query=query,
            reasoning=data.get("reasoning", "Direct research on target query."),
            sub_tasks=sub_tasks,
            key_entities=data.get("key_entities", [])
        )

planner = ResearchPlanner()
