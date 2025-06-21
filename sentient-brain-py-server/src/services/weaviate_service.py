import weaviate
import os
from dotenv import load_dotenv
from weaviate.auth import AuthApiKey

# Load environment variables from .env file
load_dotenv()

def get_weaviate_client():
    """
    Connects to a Weaviate instance and returns a client object.

    The connection logic prioritizes Weaviate Cloud Services (WCS).
    If WCS credentials are not found, it falls back to a local connection.
    """
    wcs_cluster_url = os.getenv("WCS_CLUSTER_URL")
    wcs_api_key = os.getenv("WCS_API_KEY")
    
    weaviate_host = os.getenv("WEAVIATE_HOST")
    weaviate_port = os.getenv("WEAVIATE_PORT")

    if wcs_cluster_url and wcs_api_key:
        # Connect to Weaviate Cloud Service
        print("Connecting to Weaviate Cloud Service...")
        client = weaviate.connect_to_wcs(
            cluster_url=wcs_cluster_url,
            auth_credentials=AuthApiKey(api_key=wcs_api_key),
        )
        print("Successfully connected to WCS.")
        return client
    elif weaviate_host and weaviate_port:
        # Connect to a local Weaviate instance
        print(f"Connecting to local Weaviate instance at {weaviate_host}:{weaviate_port}...")
        client = weaviate.connect_to_local(
            host=weaviate_host,
            port=int(weaviate_port)
        )
        print("Successfully connected to local Weaviate.")
        return client
    else:
        raise ValueError("Weaviate connection details not found in environment variables. Please check your .env file.")

from weaviate.classes.config import Configure, Property, DataType

def create_code_schema(client: weaviate.WeaviateClient):
    """
    Creates the schema for storing code chunks in Weaviate if it doesn't already exist.
    """
    collection_name = "CodeChunk"
    if client.collections.exists(collection_name):
        print(f"Collection '{collection_name}' already exists. Skipping creation.")
        return

    print(f"Creating collection '{collection_name}'...")
    client.collections.create(
        name=collection_name,
        vectorizer_config=Configure.Vectorizer.text2vec_ollama(
            model="nomic-embed-text",
            api_endpoint="http://ollama:11434",
        ),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="file_path", data_type=DataType.TEXT),
            Property(name="language", data_type=DataType.TEXT),
            Property(name="chunk_type", data_type=DataType.TEXT),
            Property(name="start_line", data_type=DataType.INT),
            Property(name="end_line", data_type=DataType.INT),
        ],
    )
    print(f"Collection '{collection_name}' created successfully.")

# Example usage (for testing purposes)
if __name__ == "__main__":
    client = None
    try:
        client = get_weaviate_client()
        print(f"Weaviate is ready: {client.is_ready()}")
        create_code_schema(client)
    except (ValueError, Exception) as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
            print("Weaviate connection closed.")
