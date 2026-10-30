from typing import Optional, Literal
from pydantic import BaseModel, Field

class SearchCandidate(BaseModel):
    """
    Normalized result from search engine.
    """
    title: str = Field(..., description="Page title.")
    url: str = Field(..., description="Target URL.")
    snippet: str = Field(..., description="Search snippet or summary.")
    rank: int = Field(default=0, description="Search result rank.")
    domain: str = Field(default="", description="Domain name (e.g., github.com).")

class ScrapedDocument(BaseModel):
    """
    Normalized document extracted by web scraper.
    """
    url: str = Field(..., description="Source URL.")
    title: Optional[str] = Field(default="", description="Page title extracted from HTML.")
    content: str = Field(..., description="Cleaned, markdown-formatted text content.")
    char_count: int = Field(default=0, description="Extracted character count.")
    status: Literal["success", "timeout", "parse_error", "blocked"] = Field(
        default="success", 
        description="Extraction status."
    )
    error_message: Optional[str] = Field(default=None, description="Error detail if failed.")
