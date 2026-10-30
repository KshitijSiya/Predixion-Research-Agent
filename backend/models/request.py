from typing import Literal, Optional
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    """
    Input schema for a user's research query.
    """
    query: str = Field(
        ..., 
        description="The research question to be investigated by the agent.",
        min_length=3,
        examples=["Compare the top 3 open-source vector databases for a startup building RAG products."]
    )
    mode: Literal["deep", "fast"] = Field(
        default="deep",
        description="Execution mode: 'deep' scrapes top pages, 'fast' uses search snippets only."
    )
    simulate_failure: Optional[Literal["none", "timeout", "bad_scrape", "empty_results", "injection_attack"]] = Field(
        default="none",
        description="Failure injection flag for test resilience and demo purposes."
    )
