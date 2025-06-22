import os
import google.genai as genai
from .embedder import Embedder

class GeminiEmbedder(Embedder):
    """Embedding provider using Google's Gemini models."""

    def __init__(self, model_name: str = "gemini-embedding-exp-03-07"):
        """Initialize the Gemini client and select an embedding model.

        Google's latest experimental embedding model `gemini-embedding-exp-03-07` (8 k-token context) offers larger context windows and improved quality over `text-embedding-004`. The default can be overridden by passing `model_name`.
        A dedicated client object is now required instead of the deprecated
        `genai.configure()` global setter.
        """
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        # New pattern (>= v1.20): instantiate a client per API key.
        self.client = genai.Client(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Uses the `batch_embed_contents` endpoint (introduced mid-2024) which
        accepts up to 96 documents per call and is more cost-efficient than
        individual `embed_content` calls.
        """
        try:
            # The new SDK uses `embed_content`; it accepts either a single string or a list of strings.
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=texts,  # list[str]
            )
            # response.embeddings will be a list of ContentEmbedding objects in the same order
            return [emb.values for emb in response.embeddings]
        except Exception as e:
            print(f"Gemini embedding error: {e}")
            return [[] for _ in texts]
