"""
Weaviate Database Inspector - Comprehensive tools for exploring vector database contents.

This service provides:
1. Schema inspection and visualization
2. Object browsing and filtering
3. Vector similarity searches
4. Collection statistics and health checks
5. Data export capabilities
"""
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from ..db.weaviate_client import get_weaviate_client

@dataclass
class CollectionInfo:
    """Information about a Weaviate collection."""
    name: str
    object_count: int
    properties: List[Dict[str, Any]]
    vectorizer_config: Dict[str, Any]
    sample_objects: List[Dict[str, Any]]

@dataclass
class SearchResult:
    """Result from a vector similarity search."""
    object_id: str
    properties: Dict[str, Any]
    distance: float
    certainty: float

class WeaviateInspector:
    """Service for inspecting and exploring Weaviate database contents."""
    
    def __init__(self):
        self.client = get_weaviate_client()
        print("[WEAVIATE_INSPECTOR] Initialized database inspector", flush=True)
    
    def get_database_overview(self) -> Dict[str, Any]:
        """Get a comprehensive overview of the Weaviate database."""
        try:
            # Get all collections
            collections = []
            collection_names = ["CodeChunk", "DocumentChunk", "DocumentSource"]
            
            for name in collection_names:
                try:
                    collection = self.client.collections.get(name)
                    
                    # Get object count
                    objects = collection.query.fetch_objects(limit=1000)
                    object_count = len(objects.objects) if hasattr(objects, 'objects') else 0
                    
                    # Get sample objects
                    sample_objects = []
                    if hasattr(objects, 'objects') and objects.objects:
                        for obj in objects.objects[:3]:  # First 3 objects as samples
                            sample_objects.append({
                                "id": str(obj.uuid),
                                "properties": obj.properties
                            })
                    
                    collections.append({
                        "name": name,
                        "object_count": object_count,
                        "sample_objects": sample_objects
                    })
                    
                except Exception as e:
                    collections.append({
                        "name": name,
                        "error": str(e),
                        "object_count": 0
                    })
            
            return {
                "status": "success",
                "database_url": "http://localhost:8080",
                "total_collections": len(collections),
                "collections": collections,
                "client_info": "Weaviate v4 Client"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_collection_details(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific collection."""
        try:
            collection = self.client.collections.get(collection_name)
            
            # Fetch all objects
            objects = collection.query.fetch_objects(limit=1000)
            all_objects = []
            
            if hasattr(objects, 'objects') and objects.objects:
                for obj in objects.objects:
                    all_objects.append({
                        "id": str(obj.uuid),
                        "properties": obj.properties,
                        "created": getattr(obj, 'created_at', None),
                        "updated": getattr(obj, 'updated_at', None)
                    })
            
            # Analyze properties
            property_stats = {}
            if all_objects:
                for obj in all_objects:
                    for prop, value in obj["properties"].items():
                        if prop not in property_stats:
                            property_stats[prop] = {
                                "type": type(value).__name__,
                                "sample_values": [],
                                "null_count": 0
                            }
                        
                        if value is None:
                            property_stats[prop]["null_count"] += 1
                        elif len(property_stats[prop]["sample_values"]) < 3:
                            property_stats[prop]["sample_values"].append(str(value)[:100])
            
            return {
                "status": "success",
                "collection_name": collection_name,
                "object_count": len(all_objects),
                "objects": all_objects,
                "property_statistics": property_stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "collection_name": collection_name,
                "message": str(e)
            }
    
    def search_by_content(
        self, 
        query: str, 
        collection_name: str = "CodeChunk",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for objects by content similarity."""
        try:
            collection = self.client.collections.get(collection_name)
            
            # Perform vector search
            results = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=["distance", "certainty"]
            )
            
            search_results = []
            if hasattr(results, 'objects') and results.objects:
                for obj in results.objects:
                    metadata = getattr(obj, 'metadata', {})
                    search_results.append({
                        "id": str(obj.uuid),
                        "properties": obj.properties,
                        "distance": metadata.get('distance', 0.0),
                        "certainty": metadata.get('certainty', 0.0)
                    })
            
            return {
                "status": "success",
                "query": query,
                "collection": collection_name,
                "results_count": len(search_results),
                "results": search_results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "collection": collection_name,
                "message": str(e)
            }
    
    def filter_objects(
        self,
        collection_name: str,
        property_name: str,
        property_value: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Filter objects by property values."""
        try:
            collection = self.client.collections.get(collection_name)
            
            # Fetch all objects and filter client-side (simplified approach)
            objects = collection.query.fetch_objects(limit=1000)
            filtered_objects = []
            
            if hasattr(objects, 'objects') and objects.objects:
                for obj in objects.objects:
                    prop_val = obj.properties.get(property_name)
                    if prop_val and property_value.lower() in str(prop_val).lower():
                        filtered_objects.append({
                            "id": str(obj.uuid),
                            "properties": obj.properties
                        })
                        
                        if len(filtered_objects) >= limit:
                            break
            
            return {
                "status": "success",
                "collection": collection_name,
                "filter": f"{property_name} contains '{property_value}'",
                "results_count": len(filtered_objects),
                "results": filtered_objects
            }
            
        except Exception as e:
            return {
                "status": "error",
                "collection": collection_name,
                "message": str(e)
            }
    
    def get_code_chunks_by_file(self, file_path: str) -> Dict[str, Any]:
        """Get all code chunks for a specific file."""
        return self.filter_objects(
            collection_name="CodeChunk",
            property_name="file_path",
            property_value=file_path
        )
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all collections."""
        stats = {}
        collection_names = ["CodeChunk", "DocumentChunk", "DocumentSource"]
        
        for name in collection_names:
            try:
                collection = self.client.collections.get(name)
                objects = collection.query.fetch_objects(limit=1000)
                
                if hasattr(objects, 'objects') and objects.objects:
                    # Analyze content lengths
                    content_lengths = []
                    file_paths = set()
                    node_types = {}
                    
                    for obj in objects.objects:
                        props = obj.properties
                        
                        # Content length analysis
                        content = props.get('content', '')
                        if content:
                            content_lengths.append(len(content))
                        
                        # File path tracking
                        file_path = props.get('file_path')
                        if file_path:
                            file_paths.add(file_path)
                        
                        # Node type distribution
                        node_type = props.get('node_type')
                        if node_type:
                            node_types[node_type] = node_types.get(node_type, 0) + 1
                    
                    stats[name] = {
                        "total_objects": len(objects.objects),
                        "unique_files": len(file_paths),
                        "node_type_distribution": node_types,
                        "content_stats": {
                            "avg_length": sum(content_lengths) / len(content_lengths) if content_lengths else 0,
                            "min_length": min(content_lengths) if content_lengths else 0,
                            "max_length": max(content_lengths) if content_lengths else 0
                        }
                    }
                else:
                    stats[name] = {"total_objects": 0, "status": "empty"}
                    
            except Exception as e:
                stats[name] = {"error": str(e)}
        
        return {
            "status": "success",
            "statistics": stats,
            "summary": {
                "total_chunks": sum(s.get("total_objects", 0) for s in stats.values() if isinstance(s, dict)),
                "collections_with_data": len([s for s in stats.values() if isinstance(s, dict) and s.get("total_objects", 0) > 0])
            }
        }
    
    def export_collection_data(self, collection_name: str) -> Dict[str, Any]:
        """Export all data from a collection in JSON format."""
        try:
            details = self.get_collection_details(collection_name)
            
            if details["status"] == "success":
                # Format for easy JSON export
                export_data = {
                    "collection_name": collection_name,
                    "exported_at": "2025-01-22",  # Current date
                    "object_count": details["object_count"],
                    "objects": details["objects"]
                }
                
                return {
                    "status": "success",
                    "export_data": export_data,
                    "json_string": json.dumps(export_data, indent=2)
                }
            else:
                return details
                
        except Exception as e:
            return {
                "status": "error",
                "collection": collection_name,
                "message": str(e)
            }

# Factory function
def get_weaviate_inspector() -> WeaviateInspector:
    """Get a configured Weaviate inspector instance."""
    return WeaviateInspector() 