import os
from abc import ABC, abstractmethod

class Embedder(ABC):
    """Abstract base class for all embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a list of texts."""
        pass

def get_embedder() -> Embedder:
    """Factory function to get the configured embedding provider with fallback."""
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()

    if provider == "gemini":
        try:
            from .gemini import GeminiEmbedder
            embedder = GeminiEmbedder()
            # Test with a small embedding to check quota
            test_result = embedder.embed(["test"])
            if not test_result or not test_result[0]:
                raise Exception("Gemini embedder returned empty result - likely quota exhausted")
            return embedder
        except Exception as e:
            print(f"[EMBEDDER] Gemini failed ({e}), falling back to local HF model", flush=True)
            # Fall back to local HuggingFace model
            from .local_hf import LocalHFEmbedder
            return LocalHFEmbedder()
    elif provider == "local_hf":
        from .local_hf import LocalHFEmbedder
        return LocalHFEmbedder()
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
