import re
from typing import List
from backend.models.tool_result import ScrapedDocument, SearchCandidate

class ContentSanitizer:
    """
    Sanitizes external web content and isolates untrusted data to protect
    against prompt injection attacks, malicious control sequences, and context overflows.
    """
    
    # Common prompt injection patterns to neutralize
    SUSPICIOUS_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+an?\s+unrestricted", re.IGNORECASE),
        re.compile(r"\[/?(inst|sys|system|assistant)\]", re.IGNORECASE),
        re.compile(r"<\|im_start\|>", re.IGNORECASE),
        re.compile(r"<\|im_end\|>", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_text(cls, raw_text: str) -> str:
        """
        Cleans raw scraped text: strips control chars, neutralizes injection tags,
        and normalizes excessive whitespace.
        """
        if not raw_text:
            return ""
            
        text = raw_text
        
        # Replace suspicious prompt injection keywords with neutralized tokens
        for pattern in cls.SUSPICIOUS_PATTERNS:
            text = pattern.sub("[FILTERED_COMMAND]", text)
            
        # Remove non-printable control characters (except common whitespace)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        
        # Collapse excessive newlines and spaces
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        
        return text.strip()

    @classmethod
    def wrap_untrusted_document(cls, doc: ScrapedDocument) -> str:
        """
        Wraps extracted web document into strict XML boundaries so the LLM
        treats it strictly as reference data rather than executable instructions.
        """
        cleaned = cls.sanitize_text(doc.content)
        return (
            f'<untrusted_external_source url="{doc.url}" title="{doc.title}">\n'
            f"{cleaned}\n"
            f"</untrusted_external_source>"
        )

    @classmethod
    def wrap_search_snippets(cls, candidates: List[SearchCandidate]) -> str:
        """
        Formats search snippets within isolated tags.
        """
        blocks = []
        for c in candidates:
            cleaned_snippet = cls.sanitize_text(c.snippet)
            blocks.append(
                f'<search_result rank="{c.rank}" url="{c.url}" domain="{c.domain}" title="{c.title}">\n'
                f"{cleaned_snippet}\n"
                f"</search_result>"
            )
        return "\n".join(blocks)

sanitizer = ContentSanitizer()
