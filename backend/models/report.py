from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceMetadata(BaseModel):
    """
    Source citation metadata used in final report.
    """
    title: str = Field(..., description="Source title.")
    url: str = Field(..., description="Verified source URL.")
    snippet: str = Field(..., description="Relevant snippet or quote supporting the finding.")
    domain: str = Field(..., description="Domain name (e.g., arxiv.org, github.com).")
    relevance_score: float = Field(default=1.0, description="Relevance score (0.0 to 1.0).")

class ExecutionMetadata(BaseModel):
    """
    Observability and telemetry tracking.
    """
    plan_duration_sec: float = Field(default=0.0)
    tools_duration_sec: float = Field(default=0.0)
    synthesis_duration_sec: float = Field(default=0.0)
    total_latency_sec: float = Field(default=0.0)
    sources_retrieved_count: int = Field(default=0)
    sources_retained_count: int = Field(default=0)
    primary_provider: str = Field(default="groq")
    model_used: str = Field(default="llama-3.3-70b-versatile")
    failover_triggered: bool = Field(default=False)
    failover_reason: Optional[str] = Field(default=None)

class ResearchReport(BaseModel):
    """
    Deterministic final output matching the Predixion evaluation rubric.
    """
    user_question: str = Field(..., description="Original user question.")
    short_answer: str = Field(..., description="Concise executive summary answering the question.")
    key_findings: List[str] = Field(..., description="Detailed, bulleted key findings with factual specifics.")
    sources_used: List[SourceMetadata] = Field(..., description="List of verified sources used to ground the report.")
    confidence_level: Literal["High", "Medium", "Low"] = Field(..., description="Subjective confidence rating.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Algorithmic confidence score between 0.0 and 1.0.")
    limitations_or_assumptions: List[str] = Field(..., description="Explicit limitations of retrieved data or assumptions made.")
    suggested_next_steps: List[str] = Field(..., description="Actionable follow-up research recommendations.")
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata, description="Telemetry & latency data.")
