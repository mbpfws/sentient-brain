import os
from abc import ABC, abstractmethod

class Embedder(ABC):
    """Abstract base class for all embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a list of texts."""
        pass

def get_embedder() -> Embedder:
    """Factory function to get the configured embedding provider."""
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from .gemini import GeminiEmbedder
        return GeminiEmbedder()
    # Add other providers here in the future (e.g., 'openai', 'local_hf')
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
