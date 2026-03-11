"""AI services: LLM fallback chain, CLIP embeddings, NLP query parsing, OCR."""

import io
import json
import logging
import time
from collections import deque

import httpx
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CLIP model singleton
# ---------------------------------------------------------------------------

_clip_model = None
_clip_processor = None


def _load_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor

        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return _clip_model, _clip_processor


def generate_clip_embedding(image_bytes: bytes) -> list[float]:
    """Generate CLIP embedding for an image. Returns 512-dim vector."""
    model, processor = _load_clip()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    outputs = model.get_image_features(**inputs)
    embedding = outputs[0].detach().numpy().tolist()
    return embedding


def generate_text_embedding(text: str) -> list[float]:
    """Generate CLIP text embedding for semantic search."""
    model, processor = _load_clip()
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    outputs = model.get_text_features(**inputs)
    embedding = outputs[0].detach().numpy().tolist()
    return embedding


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------


def extract_text_ocr(image_bytes: bytes) -> str:
    """Extract text from image using pytesseract."""
    try:
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# LLM Fallback Chain
# ---------------------------------------------------------------------------


class LLMFallbackChain:
    """Cascade through LLM providers: Cerebras -> Mistral -> Groq -> Anthropic."""

    PROVIDERS = [
        {
            "name": "cerebras",
            "url": "https://api.cerebras.ai/v1/chat/completions",
            "key_attr": "CEREBRAS_API_KEY",
            "model": "llama-3.3-70b",
        },
        {
            "name": "mistral",
            "url": "https://api.mistral.ai/v1/chat/completions",
            "key_attr": "MISTRAL_API_KEY",
            "model": "mistral-small-latest",
        },
        {
            "name": "groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key_attr": "GROQ_API_KEY",
            "model": "llama-3.3-70b-versatile",
        },
        {
            "name": "anthropic",
            "url": "https://api.anthropic.com/v1/messages",
            "key_attr": "ANTHROPIC_API_KEY",
            "model": "claude-haiku-4-5-20251001",
            "is_anthropic": True,
        },
    ]

    def __init__(self) -> None:
        self.rate_limits: dict[str, float] = {}  # provider -> backoff_until timestamp
        self.anthropic_window: deque[float] = deque()  # sliding window timestamps
        self.anthropic_limits = {"5min": 10, "1hr": 40, "24hr": 200}

    def _is_rate_limited(self, provider_name: str) -> bool:
        backoff_until = self.rate_limits.get(provider_name, 0)
        return time.time() < backoff_until

    def _record_rate_limit(self, provider_name: str) -> None:
        self.rate_limits[provider_name] = time.time() + 600  # 10 min backoff

    def _check_anthropic_window(self) -> bool:
        now = time.time()
        # Clean old entries
        while self.anthropic_window and self.anthropic_window[0] < now - 86400:
            self.anthropic_window.popleft()

        count_5min = sum(1 for t in self.anthropic_window if t > now - 300)
        count_1hr = sum(1 for t in self.anthropic_window if t > now - 3600)
        count_24hr = len(self.anthropic_window)

        return (
            count_5min < self.anthropic_limits["5min"]
            and count_1hr < self.anthropic_limits["1hr"]
            and count_24hr < self.anthropic_limits["24hr"]
        )

    async def generate(self, prompt: str, system: str = "") -> str:
        """Cascade through providers until one succeeds."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            for provider in self.PROVIDERS:
                name = provider["name"]
                api_key = getattr(settings, provider["key_attr"], "")
                if not api_key:
                    continue
                if self._is_rate_limited(name):
                    continue

                if provider.get("is_anthropic"):
                    if not self._check_anthropic_window():
                        continue

                try:
                    if provider.get("is_anthropic"):
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        }
                        body = {
                            "model": provider["model"],
                            "max_tokens": 1024,
                            "messages": [{"role": "user", "content": prompt}],
                        }
                        if system:
                            body["system"] = system
                        resp = await client.post(
                            provider["url"], json=body, headers=headers
                        )
                    else:
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        }
                        messages = []
                        if system:
                            messages.append({"role": "system", "content": system})
                        messages.append({"role": "user", "content": prompt})
                        body = {
                            "model": provider["model"],
                            "messages": messages,
                            "max_tokens": 1024,
                        }
                        resp = await client.post(
                            provider["url"], json=body, headers=headers
                        )

                    if resp.status_code in (429, 503):
                        self._record_rate_limit(name)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                    if provider.get("is_anthropic"):
                        self.anthropic_window.append(time.time())
                        return data["content"][0]["text"]
                    else:
                        return data["choices"][0]["message"]["content"]

                except (httpx.HTTPError, KeyError, IndexError):
                    continue

        return ""

    async def generate_tags(self, description: str) -> list[str]:
        """Generate tags for an asset description."""
        prompt = (
            "Given this asset description, generate a JSON array of 5-15 relevant tags "
            "categorized into: objects, scene, mood, colors, style. "
            "Return ONLY the JSON array, no other text.\n\n"
            f"Description: {description}"
        )
        result = await self.generate(prompt)
        return _parse_tag_response(result)

    async def generate_description(self, context: str) -> str:
        """Generate a description for an asset."""
        prompt = (
            "Generate a brief, descriptive caption for a digital asset with this context. "
            f"Return only the description text, no formatting.\n\nContext: {context}"
        )
        return await self.generate(prompt)


# ---------------------------------------------------------------------------
# NLP query parsing
# ---------------------------------------------------------------------------


async def parse_nlp_query(query: str) -> dict:
    """Use LLM to parse natural language query into structured search params."""
    prompt = (
        'Parse this search query into structured filters. Return JSON only.\n'
        f'Query: "{query}"\n\n'
        'Return format:\n'
        '{"keywords": ["list", "of", "keywords"], '
        '"file_type": "image|video|audio|document|null", '
        '"date_range": {"from": "YYYY-MM-DD|null", "to": "YYYY-MM-DD|null"}, '
        '"color": "dominant color or null", '
        '"description": "what the user is looking for"}'
    )
    llm = LLMFallbackChain()
    result = await llm.generate(prompt)
    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(result)
    except (json.JSONDecodeError, ValueError):
        # Fallback: use the raw query as keywords
        return {
            "keywords": query.split(),
            "file_type": None,
            "date_range": {"from": None, "to": None},
            "color": None,
            "description": query,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_tag_response(result: str) -> list[str]:
    """Robustly parse tags from LLM response (JSON array, markdown fences, CSV)."""
    if not result:
        return []

    result = result.strip()

    # Strip markdown code fences
    if result.startswith("```"):
        result = result.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    # Try JSON array
    try:
        parsed = json.loads(result)
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if t]
    except (json.JSONDecodeError, ValueError):
        pass

    # Try comma-separated
    if "," in result:
        return [t.strip().strip('"').strip("'") for t in result.split(",") if t.strip()]

    # Try newline-separated
    lines = [line.strip().lstrip("-").lstrip("*").strip() for line in result.splitlines()]
    return [line for line in lines if line]
