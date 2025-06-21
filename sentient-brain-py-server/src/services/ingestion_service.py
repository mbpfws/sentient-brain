import weaviate
import weaviate.classes.config as wvc
from weaviate.collections.classes.config import Configure

from ..db.weaviate_client import get_weaviate_client
from ..models.document_models import DocumentSource, DocumentChunk, DocumentType, IngestionStatus

class IngestionService:
    """Service for ingesting and processing documents into Weaviate."""

    def __init__(self):
        self.client = get_weaviate_client()

    def initialize_schema(self, recreate: bool = False):
        """Ensures the required collections exist in Weaviate."""
        collection_names = list(self.client.collections.list_all().keys())

        # 1. Define and create DocumentSource collection
        source_collection_name = "DocumentSource"
        if recreate and source_collection_name in collection_names:
            self.client.collections.delete(source_collection_name)
            print(f"Deleted existing collection: {source_collection_name}")
        
        if not self.client.collections.exists(source_collection_name):
            self.client.collections.create(
                name=source_collection_name,
                properties=[
                    wvc.Property(name="title", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="document_type", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="tech_stack", data_type=wvc.DataType.TEXT_ARRAY),
                    wvc.Property(name="last_crawled_at", data_type=wvc.DataType.DATE),
                    wvc.Property(name="status", data_type=wvc.DataType.TEXT),
                ]
            )
            print(f"Created collection: {source_collection_name}")

        # 2. Define and create DocumentChunk collection
        chunk_collection_name = "DocumentChunk"
        if recreate and chunk_collection_name in collection_names:
            self.client.collections.delete(chunk_collection_name)
            print(f"Deleted existing collection: {chunk_collection_name}")

        if not self.client.collections.exists(chunk_collection_name):
            self.client.collections.create(
                name=chunk_collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_ollama(
                    model="nomic-embed-text",
                    api_endpoint="http://ollama:11434",
                ),
                properties=[
                    wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="order", data_type=wvc.DataType.INT),
                    wvc.Property(name="headings", data_type=wvc.DataType.TEXT_ARRAY),
                    wvc.Property(name="metadata_tags", data_type=wvc.DataType.TEXT_ARRAY),
                    wvc.Property(name="embedding_provider", data_type=wvc.DataType.TEXT),
                ],
                references=[
                    wvc.ReferenceProperty(name="from_source", target_collection=source_collection_name)
                ]
            )
            print(f"Created collection: {chunk_collection_name}")
