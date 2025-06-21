import os
import google.genai as genai
from .embedder import Embedder

class GeminiEmbedder(Embedder):
    """Embedding provider using Google's Gemini models."""

    def __init__(self, model_name: str = "models/embedding-001"):
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a list of texts."""
        try:
            # Note: The 'task_type' is recommended for future models and specific use cases.
            result = genai.embed_content(model=self.model_name, content=texts, task_type="RETRIEVAL_DOCUMENT")
            return result['embedding']
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            # Return a list of empty lists to match the expected output structure on failure
            return [[] for _ in texts]
