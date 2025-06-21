import weaviate
import weaviate.classes.config as wvc
from weaviate.collections.classes.config import Configure
from uuid import uuid4

from ..db.weaviate_client import get_weaviate_client
from ..models.document_models import DocumentSource, DocumentChunk, DocumentType, IngestionStatus
from ..embedding.embedder import get_embedder

class IngestionService:
    """Service for ingesting and processing documents into Weaviate."""

    def __init__(self):
        self.client = get_weaviate_client()
        self.embedder = get_embedder()

    def initialize_schema(self, recreate: bool = False):
        """Ensures the required collections exist in Weaviate."""
        # Configuration for collections
        source_collection_name = "DocumentSource"
        chunk_collection_name = "DocumentChunk"

        # Delete collections if recreation is requested
        if recreate:
            if self.client.collections.exists(source_collection_name):
                self.client.collections.delete(source_collection_name)
                print(f"Deleted existing collection: {source_collection_name}")
            if self.client.collections.exists(chunk_collection_name):
                self.client.collections.delete(chunk_collection_name)
                print(f"Deleted existing collection: {chunk_collection_name}")

        # Create DocumentSource collection if it doesn't exist
        if not self.client.collections.exists(source_collection_name):
            self.client.collections.create(
                name=source_collection_name,
                vectorizer_config=Configure.Vectorizer.none(),  # no automatic embeddings; we manage vectors manually where needed
                properties=[
                    wvc.Property(name="title", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="document_type", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="uri", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="status", data_type=wvc.DataType.TEXT),
                ]
            )
            print(f"Created collection: {source_collection_name}")

        # Create DocumentChunk collection if it doesn't exist
        if not self.client.collections.exists(chunk_collection_name):
            self.client.collections.create(
                name=chunk_collection_name,
                vectorizer_config=Configure.Vectorizer.none(), # We provide vectors manually
                properties=[
                    wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="order", data_type=wvc.DataType.INT),
                    wvc.Property(name="embedding_provider", data_type=wvc.DataType.TEXT),
                ],
                references=[
                    wvc.ReferenceProperty(name="from_source", target_collection=source_collection_name)
                ]
            )
            print(f"Created collection: {chunk_collection_name}")

    def ingest_document_source(self, source: DocumentSource) -> str:
        """Ingests a single DocumentSource and returns its Weaviate UUID."""
        source_collection = self.client.collections.get("DocumentSource")
        properties = {
            "title": source.title,
            "document_type": source.document_type.value,
            "uri": source.uri,
            "status": source.status.value,
        }
        uuid = source_collection.data.insert(properties)
        return str(uuid)

    def ingest_document_chunks(self, source_uuid: str, chunks: list[str]):
        """Generates embeddings and ingests document chunks in a batch."""
        chunk_collection = self.client.collections.get("DocumentChunk")
        
        # Generate embeddings for all chunks
        vectors = self.embedder.embed(chunks)
        embedding_provider_name = self.embedder.__class__.__name__

        # Insert each chunk individually (v4 client no longer supports .batch() on DataCollection)
        for i, chunk_content in enumerate(chunks):
            data_object = {
                "content": chunk_content,
                "order": i,
                "embedding_provider": embedding_provider_name,
            }
            chunk_collection.data.insert(
                properties=data_object,
                vector=vectors[i],
                references={
                    "from_source": [source_uuid]
                }
            )
        print(f"Successfully ingested {len(chunks)} chunks for source {source_uuid}.")
