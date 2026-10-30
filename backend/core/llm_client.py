import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
from groq import AsyncGroq, Groq
from backend.config import settings

logger = logging.getLogger("agent.llm")

class LLMResponse:
    def __init__(
        self, 
        content: str, 
        provider: str, 
        model: str, 
        latency_sec: float, 
        failover_triggered: bool = False,
        failover_reason: Optional[str] = None
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.latency_sec = latency_sec
        self.failover_triggered = failover_triggered
        self.failover_reason = failover_reason

class ResilientLLMClient:
    """
    Production-grade LLM client implementing primary routing to Groq (openai/gpt-oss-120b)
    with automatic failover to fallback model (qwen/qwen3.8-27b) or secondary provider
    upon rate-limits (HTTP 429), timeouts, or server errors.
    """
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.groq_fallback_model = settings.GROQ_FALLBACK_MODEL
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        
        self.groq_async_client = AsyncGroq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.groq_sync_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

    async def _call_groq(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        json_mode: bool = False, 
        temperature: float = 0.2
    ) -> str:
        if not self.groq_async_client:
            raise ValueError("GROQ_API_KEY is not configured.")
        
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        response = await self.groq_async_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        json_mode: bool = False, 
        temperature: float = 0.2,
        force_failover: bool = False
    ) -> LLMResponse:
        """
        Executes request against primary model and automatically falls back to secondary model on failure.
        """
        start_time = time.time()
        
        if not force_failover and self.groq_async_client:
            try:
                content = await self._call_groq(
                    messages, 
                    model=self.groq_model, 
                    json_mode=json_mode, 
                    temperature=temperature
                )
                latency = round(time.time() - start_time, 3)
                return LLMResponse(
                    content=content,
                    provider="groq",
                    model=self.groq_model,
                    latency_sec=latency,
                    failover_triggered=False
                )
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"[FAILOVER TRIGGERED] Primary model {self.groq_model} failed: {err_msg}. Routing to failover model {self.groq_fallback_model}.")
                # Route to failover model
                content = await self._call_groq(
                    messages, 
                    model=self.groq_fallback_model, 
                    json_mode=json_mode, 
                    temperature=temperature
                )
                latency = round(time.time() - start_time, 3)
                return LLMResponse(
                    content=content,
                    provider="groq",
                    model=self.groq_fallback_model,
                    latency_sec=latency,
                    failover_triggered=True,
                    failover_reason=f"Primary failed ({err_msg}). Routed to {self.groq_fallback_model}."
                )
        else:
            # Force failover testing
            reason = "Force failover test flag active"
            content = await self._call_groq(
                messages, 
                model=self.groq_fallback_model, 
                json_mode=json_mode, 
                temperature=temperature
            )
            latency = round(time.time() - start_time, 3)
            return LLMResponse(
                content=content,
                provider="groq",
                model=self.groq_fallback_model,
                latency_sec=latency,
                failover_triggered=True,
                failover_reason=reason
            )

    async def generate_json(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        force_failover: bool = False
    ) -> Tuple[Dict[str, Any], LLMResponse]:
        """
        Enforces structured JSON output with automatic markdown fence stripping.
        """
        response = await self.generate(messages, json_mode=True, temperature=temperature, force_failover=force_failover)
        raw_text = response.content.strip()
        
        # Strip potential markdown fences
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        try:
            parsed = json.loads(raw_text)
            return parsed, response
        except json.JSONDecodeError as decode_err:
            logger.error(f"Malformed JSON from {response.provider} ({response.model}): {raw_text[:200]}...")
            raise ValueError(f"Failed to parse structured JSON from {response.model}: {decode_err}")

# Singleton instance
llm_client = ResilientLLMClient()
