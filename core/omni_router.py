import json
import requests
from typing import Optional
from config.settings import settings
from utils.logger import logger

class OmniRouter:
    """
    Omni-Model Cloud Routing Engine v2.
    Intelligent multi-model failover across ALL available free cloud brains:
    
    Priority Chain:
    1. Gemini 3.8 Flash (Google Cloud Direct - Fastest, Most Reliable, FREE)
    2. Gemini 3.1 Flash Lite (Google Cloud Direct - Ultra fast lite model)
    3. OpenRouter Pool (Liquid LFM, Gemma 4, Nemotron, Qwen - All FREE)
    
    Features:
    - Auto-retry on rate limit (429) with next model in chain
    - JSON extraction from markdown code blocks
    - Conversation mode for CEO chat responses
    """

    OPENROUTER_MODELS = [
        "liquid/lfm-2.5-2.6b:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
        "qwen/qwen3.8-27b:free",
        "nvidia/nemotron-3-super-120b-a12b:free"
    ]

    def __init__(self):
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def _call_gemini(self, prompt: str, system_prompt: str = "", history: Optional[list] = None) -> Optional[str]:
        """Direct Google Gemini Cloud API call using new google-genai SDK."""
        if not self.gemini_key:
            return None

        models_to_try = ["gemini-3.8-flash", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
        
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)

            history_context = ""
            if history:
                history_lines = []
                for h in history[-8:]:
                    role = "Veer (Boss)" if h.get("role") == "user" else "CEO"
                    history_lines.append(f"{role}: {h.get('content', '')}")
                history_context = "\nRecent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

            full_prompt = f"{system_prompt}\n{history_context}Current Message from Veer:\n{prompt}" if (system_prompt or history_context) else prompt

            for model_name in models_to_try:
                try:
                    logger.info(f"[OmniRouter] Trying Gemini Cloud: {model_name}...")
                    res = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                    )
                    if res and res.text and len(res.text.strip()) > 10:
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
        if not self.openrouter_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
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
