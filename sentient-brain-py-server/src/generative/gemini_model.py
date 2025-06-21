"""Simple wrapper around Google GenAI SDK for server-side reasoning tasks.

This keeps generative usage separate from the embedding-only wrapper so that
we can pick different models for chat/agent flows (flash / flash-lite) versus
high-dimensional embeddings.

Usage:
    from generative.gemini_model import GeminiGenerative
    gen = GeminiGenerative()  # picks model from $GEMINI_MODEL_NAME (or default)
    response = gen.generate_text("Explain vector databases in 2 sentences")
"""
from __future__ import annotations

import os

import google.genai as genai

__all__ = ["GeminiGenerative"]


class GeminiGenerative:
    """Lightweight helper for text-generation / reasoning with Gemini models."""

    def __init__(self, model_name: str | None = None) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable not set.")

        # Allow override via argument or env; fall back to flash-lite preview.
        model_name = (
            model_name
            or os.getenv("GEMINI_MODEL_NAME")
            or "gemini-2.5-flash-lite-preview-06-17"
        )

        self.client = genai.Client(api_key=api_key)
        # The unified GenAI SDK exposes `GenerativeModel` via the client
        self.model = self.client.GenerativeModel(model_name=model_name)

    # ---------------------------------------------------------------------
    # Convenience helpers
    # ---------------------------------------------------------------------
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Return the model's text response for a single prompt."""
        response = self.model.generate_content(prompt, **kwargs)
        # `generate_content` returns a GenerativeResponse; join parts as text
        return "".join(part.text for part in response.candidates[0].content.parts)

    def chat_stream(self, prompt: str, **kwargs):
        """Yield streamed chunks for real-time chat UIs."""
        for chunk in self.model.generate_content_stream(prompt, **kwargs):
            yield "".join(part.text for part in chunk.candidates[0].content.parts)
