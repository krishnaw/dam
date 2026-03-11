"""Unit tests for AI / LLM fallback chain, CLIP, NLP, and OCR services."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ai import (
    LLMFallbackChain,
    _parse_tag_response,
    extract_text_ocr,
    generate_clip_embedding,
    generate_text_embedding,
    parse_nlp_query,
)


@pytest.fixture
def llm():
    return LLMFallbackChain()


def _mock_settings(**overrides):
    """Create mock settings with API keys."""
    defaults = {
        "CEREBRAS_API_KEY": "test-cerebras-key",
        "MISTRAL_API_KEY": "test-mistral-key",
        "GROQ_API_KEY": "test-groq-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_openai_response(content: str, status_code: int = 200):
    """Create a mock httpx response in OpenAI-compatible format."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


def _make_anthropic_response(content: str, status_code: int = 200):
    """Create a mock httpx response in Anthropic format."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = {
        "content": [{"text": content}]
    }
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_tries_free_providers_first(self, llm):
        """First provider (Cerebras) succeeds -- should never call later providers."""
        cerebras_resp = _make_openai_response("cerebras answer")

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=cerebras_resp)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                result = await llm.generate("test prompt")
                assert result == "cerebras answer"
                # Only one call (Cerebras), not subsequent providers
                assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, llm):
        """If Cerebras fails, should fall through to Mistral."""
        cerebras_resp = _make_openai_response("", status_code=500)
        mistral_resp = _make_openai_response("mistral answer")

        call_count = 0

        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "cerebras" in url:
                raise httpx.HTTPError("connection error")
            return mistral_resp

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = mock_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                result = await llm.generate("test prompt")
                assert result == "mistral answer"

    @pytest.mark.asyncio
    async def test_rate_limit_backoff(self, llm):
        """429 response should cause provider to be skipped on next call."""
        rate_limited_resp = MagicMock(spec=httpx.Response)
        rate_limited_resp.status_code = 429

        success_resp = _make_openai_response("mistral answer")

        async def mock_post(url, **kwargs):
            if "cerebras" in url:
                return rate_limited_resp
            return success_resp

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = mock_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                # First call: Cerebras returns 429, falls through to Mistral
                result = await llm.generate("prompt1")
                assert result == "mistral answer"

                # Cerebras should now be rate-limited
                assert llm._is_rate_limited("cerebras") is True

    @pytest.mark.asyncio
    async def test_anthropic_used_as_last_resort(self, llm):
        """When all free providers fail, Anthropic should be used."""
        anthropic_resp = _make_anthropic_response("anthropic answer")

        async def mock_post(url, **kwargs):
            if "anthropic" in url:
                return anthropic_resp
            raise httpx.HTTPError("connection error")

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = mock_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                result = await llm.generate("test prompt")
                assert result == "anthropic answer"
                # Verify anthropic window was recorded
                assert len(llm.anthropic_window) == 1

    @pytest.mark.asyncio
    async def test_sliding_window_tracks_anthropic_calls(self, llm):
        """Anthropic call count should be tracked in the sliding window."""
        anthropic_resp = _make_anthropic_response("answer")

        async def mock_post(url, **kwargs):
            if "anthropic" in url:
                return anthropic_resp
            raise httpx.HTTPError("fail")

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = mock_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                for _ in range(3):
                    await llm.generate("prompt")

                assert len(llm.anthropic_window) == 3

    @pytest.mark.asyncio
    async def test_all_providers_exhausted_returns_empty(self, llm):
        """When all providers fail, generate should return empty string."""
        async def mock_post(url, **kwargs):
            raise httpx.HTTPError("connection error")

        with patch("app.services.ai.settings", _mock_settings()):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = mock_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                result = await llm.generate("prompt")
                assert result == ""

    @pytest.mark.asyncio
    async def test_generate_tags_parses_json(self, llm):
        """generate_tags should parse a JSON array from the LLM response."""
        tags = ["nature", "landscape", "mountains", "sunset", "photography"]

        with patch.object(llm, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = json.dumps(tags)
            result = await llm.generate_tags("A beautiful mountain sunset")
            assert result == tags

    @pytest.mark.asyncio
    async def test_generate_tags_handles_markdown_wrapped_json(self, llm):
        """generate_tags should strip markdown code fences."""
        tags = ["tag1", "tag2"]

        with patch.object(llm, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = '```json\n["tag1", "tag2"]\n```'
            result = await llm.generate_tags("test description")
            assert result == tags

    @pytest.mark.asyncio
    async def test_generate_tags_returns_parsed_on_non_json(self, llm):
        """generate_tags falls through to CSV parsing for non-JSON LLM output."""
        with patch.object(llm, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "nature, landscape, mountains"
            result = await llm.generate_tags("test")
            assert "nature" in result
            assert "landscape" in result
            assert "mountains" in result

    @pytest.mark.asyncio
    async def test_generate_description_returns_string(self, llm):
        """generate_description should return a string."""
        with patch.object(llm, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "A scenic mountain landscape at sunset."
            result = await llm.generate_description("mountain photo")
            assert result == "A scenic mountain landscape at sunset."
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_groq_model_is_versatile(self, llm):
        """Verify Groq uses llama-3.3-70b-versatile model."""
        groq = next(p for p in llm.PROVIDERS if p["name"] == "groq")
        assert groq["model"] == "llama-3.3-70b-versatile"


class TestRateLimitLogic:
    def test_is_rate_limited_false_by_default(self, llm):
        assert llm._is_rate_limited("cerebras") is False

    def test_record_rate_limit_sets_backoff(self, llm):
        llm._record_rate_limit("cerebras")
        assert llm._is_rate_limited("cerebras") is True

    def test_check_anthropic_window_empty(self, llm):
        assert llm._check_anthropic_window() is True

    def test_check_anthropic_window_within_5min_limit(self, llm):
        now = time.time()
        for _ in range(9):  # under 10 limit for 5min
            llm.anthropic_window.append(now)
        assert llm._check_anthropic_window() is True

    def test_check_anthropic_window_exceeds_5min_limit(self, llm):
        now = time.time()
        for _ in range(10):  # at the 10 limit for 5min
            llm.anthropic_window.append(now)
        assert llm._check_anthropic_window() is False


class TestParseTagResponse:
    def test_parses_json_array(self):
        assert _parse_tag_response('["a", "b", "c"]') == ["a", "b", "c"]

    def test_strips_markdown_fences(self):
        assert _parse_tag_response('```json\n["x", "y"]\n```') == ["x", "y"]

    def test_parses_csv(self):
        result = _parse_tag_response("nature, landscape, sunset")
        assert result == ["nature", "landscape", "sunset"]

    def test_parses_newline_list(self):
        result = _parse_tag_response("- nature\n- landscape\n- sunset")
        assert result == ["nature", "landscape", "sunset"]

    def test_empty_string(self):
        assert _parse_tag_response("") == []

    def test_none_like(self):
        assert _parse_tag_response("") == []


class TestCLIPEmbedding:
    def test_generate_clip_embedding_returns_512_dim(self):
        """CLIP image embedding should return a 512-dim vector."""
        mock_outputs = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.detach.return_value.numpy.return_value.tolist.return_value = [0.1] * 512
        mock_outputs.__getitem__ = MagicMock(return_value=mock_tensor)

        mock_model = MagicMock()
        mock_model.get_image_features.return_value = mock_outputs

        mock_processor = MagicMock()
        mock_processor.return_value = {"pixel_values": MagicMock()}

        with patch("app.services.ai._clip_model", mock_model), \
             patch("app.services.ai._clip_processor", mock_processor):
            # Create a minimal valid image (1x1 red pixel PNG)
            from PIL import Image
            import io
            img = Image.new("RGB", (1, 1), color="red")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            image_bytes = buf.getvalue()

            result = generate_clip_embedding(image_bytes)
            assert len(result) == 512
            assert all(isinstance(v, float) for v in result)

    def test_generate_text_embedding_returns_512_dim(self):
        """CLIP text embedding should return a 512-dim vector."""
        mock_outputs = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.detach.return_value.numpy.return_value.tolist.return_value = [0.2] * 512
        mock_outputs.__getitem__ = MagicMock(return_value=mock_tensor)

        mock_model = MagicMock()
        mock_model.get_text_features.return_value = mock_outputs

        mock_processor = MagicMock()
        mock_processor.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}

        with patch("app.services.ai._clip_model", mock_model), \
             patch("app.services.ai._clip_processor", mock_processor):
            result = generate_text_embedding("a photo of a dog")
            assert len(result) == 512
            assert all(isinstance(v, float) for v in result)


class TestOCR:
    def test_extract_text_ocr_returns_text(self):
        """OCR should return extracted text from an image."""
        with patch("pytesseract.image_to_string", return_value="Hello World"):
            from PIL import Image
            import io
            img = Image.new("RGB", (100, 30), color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")

            result = extract_text_ocr(buf.getvalue())
            assert result == "Hello World"

    def test_extract_text_ocr_returns_empty_on_error(self):
        """OCR should return empty string when pytesseract is not available."""
        with patch.dict("sys.modules", {"pytesseract": None}):
            from PIL import Image
            import io
            img = Image.new("RGB", (10, 10), color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")

            result = extract_text_ocr(buf.getvalue())
            assert result == ""


class TestNLPQueryParsing:
    @pytest.mark.asyncio
    async def test_parse_nlp_query_extracts_filters(self):
        """NLP parser should extract structured filters from query."""
        mock_response = json.dumps({
            "keywords": ["sunset", "beach"],
            "file_type": "image",
            "date_range": {"from": "2024-01-01", "to": None},
            "color": "orange",
            "description": "sunset photos at the beach",
        })

        with patch.object(LLMFallbackChain, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response
            result = await parse_nlp_query("sunset photos at the beach from 2024")

            assert result["keywords"] == ["sunset", "beach"]
            assert result["file_type"] == "image"
            assert result["color"] == "orange"

    @pytest.mark.asyncio
    async def test_parse_nlp_query_fallback_on_bad_json(self):
        """NLP parser should fallback to raw keywords when LLM returns bad JSON."""
        with patch.object(LLMFallbackChain, "generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "not valid json at all"
            result = await parse_nlp_query("sunset beach photos")

            assert result["keywords"] == ["sunset", "beach", "photos"]
            assert result["description"] == "sunset beach photos"
