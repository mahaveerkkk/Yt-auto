import json
import requests
from typing import Optional
from config.settings import settings
from utils.logger import logger
from core.resilience import quota_tracker

class OmniRouter:
    """
    Omni-Model Cloud Routing Engine v2.
    Intelligent multi-model failover across ALL available free cloud brains:
    
    Priority Chain:
    1. Gemini 2.5 Flash / 2.0 Flash (Google Cloud Direct - Fastest, Most Reliable)
    2. Gemini 1.5 Flash (Google Cloud Direct - Ultra fast lite fallback)
    3. OpenRouter Pool (Qwen 2.5, Gemma 2, LLaMA 3.3, Mistral Small - All FREE)
    
    Features:
    - Auto-retry on rate limit (429) with next model in chain
    - JSON extraction from markdown code blocks
    - Conversation mode for CEO chat responses
    """

    OPENROUTER_MODELS = [
        "qwen/qwen-2.5-72b-instruct:free",
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3-instruct:free"
    ]

    def __init__(self):
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def _call_gemini(self, prompt: str, system_prompt: str = "", history: Optional[list] = None) -> Optional[str]:
        """Direct Google Gemini Cloud API call using new google-genai SDK."""
        if not self.gemini_key or not quota_tracker.can_use("gemini"):
            return None

        configured_model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        models_to_try = ["gemini-2.0-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash", configured_model, "gemini-flash-latest"]
        models_to_try = list(dict.fromkeys(models_to_try))
        
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)

            history_context = ""
            if history:
                history_lines = []
                for h in history[-8:]:
                    role = "Veer (Boss)" if h.get("role") == "user" else "AI CEO"
                    history_lines.append(f"{role}: {h.get('content', '')}")
                history_context = "Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

            user_content = f"{history_context}Veer: {prompt}" if history_context else prompt
            config = types.GenerateContentConfig(system_instruction=system_prompt) if system_prompt else None

            for model_name in models_to_try:
                try:
                    logger.info(f"[OmniRouter] Trying Gemini Cloud: {model_name}...")
                    kwargs = {"model": model_name, "contents": user_content}
                    if config:
                        kwargs["config"] = config

                    res = client.models.generate_content(**kwargs)
                    if res and res.text and len(res.text.strip()) > 5:
                        quota_tracker.record_use("gemini")
                        logger.info(f"[OmniRouter] ✅ Success from Gemini {model_name}!")
                        return res.text
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        logger.warning(f"[OmniRouter] Gemini {model_name} rate limited, trying next...")
                        continue
                    elif "404" in err_str:
                        logger.warning(f"[OmniRouter] Gemini {model_name} not available, trying next...")
                        continue
                    else:
                        logger.warning(f"[OmniRouter] Gemini {model_name} error: {err_str[:80]}")
                        continue
        except ImportError:
            logger.warning("[OmniRouter] google-genai SDK not installed")
        return None

    def _call_openrouter(self, prompt: str, system_prompt: str = "", history: Optional[list] = None) -> Optional[str]:
        """OpenRouter free models pool with sequential fallback."""
        if not self.openrouter_key or not quota_tracker.can_use("openrouter"):
            return None

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://voidarchive.local",
            "X-Title": "Void Archive AutoDirector",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for h in history[-8:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        for model_id in self.OPENROUTER_MODELS:
            try:
                logger.info(f"[OmniRouter] Trying OpenRouter: {model_id}...")
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model_id, "messages": messages, "temperature": 0.7},
                    timeout=25
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content and len(content.strip()) > 10:
                        quota_tracker.record_use("openrouter")
                        logger.info(f"[OmniRouter] ✅ Success from OpenRouter {model_id}!")
                        return content
                elif res.status_code == 429:
                    logger.warning(f"[OmniRouter] {model_id} rate limited, trying next...")
                    continue
                else:
                    logger.warning(f"[OmniRouter] {model_id} returned {res.status_code}")
            except Exception as e:
                logger.warning(f"[OmniRouter] {model_id} error: {str(e)[:60]}")
        return None

    def query(self, prompt: str, system_prompt: str = "", history: Optional[list] = None) -> Optional[str]:
        """
        Master query method. Routes through all available cloud models:
        1. Gemini Cloud Direct (fastest, most reliable)
        2. OpenRouter Free Pool (fallback)
        """
        # Priority 1: Gemini Cloud (Direct API, no middleman)
        result = self._call_gemini(prompt, system_prompt, history=history)
        if result:
            return result

        # Priority 2: OpenRouter Free Models Pool
        result = self._call_openrouter(prompt, system_prompt, history=history)
        if result:
            return result

        logger.error("[OmniRouter] ❌ All cloud models exhausted!")
        return None

omni_router = OmniRouter()
