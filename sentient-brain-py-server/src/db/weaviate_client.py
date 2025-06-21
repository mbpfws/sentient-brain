import os
import time
import weaviate
from weaviate.client import WeaviateClient
from dotenv import load_dotenv

load_dotenv()

class WeaviateClientSingleton:
    _client: WeaviateClient = None

    def get_client(self) -> WeaviateClient:
        if self._client is None:
            retries = 5
            delay = 3
            for i in range(retries):
                try:
                    print(f"Attempting to connect to Weaviate ({i+1}/{retries})...", flush=True)
                    connection_params = weaviate.connect.ConnectionParams.from_params(
                        http_host=os.getenv("WEAVIATE_HOST", "localhost"),
                        http_port=int(os.getenv("WEAVIATE_PORT", 8080)),
                        http_secure=False,
                        grpc_host=os.getenv("WEAVIATE_HOST", "localhost"),
                        grpc_port=50051,
                        grpc_secure=False,
                    )
                    self._client = weaviate.WeaviateClient(connection_params)
                    self._client.connect()
                    print("Successfully connected to Weaviate.", flush=True)
                    return self._client
                except Exception as e:
                    print(f"Failed to connect to Weaviate (attempt {i+1}/{retries}): {e}", flush=True)
                    if i < retries - 1:
                        print(f"Retrying in {delay} seconds...", flush=True)
                        time.sleep(delay)
                    else:
                        print("Could not connect to Weaviate after several retries.", flush=True)
                        raise
        return self._client

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

weaviate_client_singleton = WeaviateClientSingleton()

def get_weaviate_client() -> WeaviateClient:
    return weaviate_client_singleton.get_client()
