from .embedder import Embedder
from sentence_transformers import SentenceTransformer

class LocalHFEmbedder(Embedder):
    """Embedding provider using local Hugging Face Sentence-Transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load model; this will download the model on first run
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a list of texts using a local HF model."""
        # Returns list of embeddings as Python lists
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
