from neo4j import GraphDatabase, Driver
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Neo4j Graph Data Model for Codebase AST (Abstract Syntax Tree)

This model represents the structural relationships within a codebase.

NODE LABELS:
- :File
  - properties: {path: string, name: string, language: string}
- :Class
  - properties: {name: string, start_line: int, end_line: int}
- :Function
  - properties: {name: string, signature: string, start_line: int, end_line: int}
- :Import
  - properties: {name: string, alias: string}

RELATIONSHIP TYPES:
- (:Class)-[:DEFINED_IN]->(:File)
- (:Function)-[:DEFINED_IN]->(:File)
- (:Function)-[:DEFINED_IN]->(:Class)
- (:File)-[:IMPORTS]->(:Import)
- (:Function)-[:CALLS]->(:Function)
- (:Class)-[:INHERITS_FROM]->(:Class)
"""

# Global driver instance
_driver = None

def get_neo4j_driver() -> Driver:
    """
    Establishes a connection to the Neo4j AuraDB and returns a driver object.
    Uses a singleton pattern to reuse the existing driver if already connected.
    """
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([uri, user, password]):
            raise ValueError("Neo4j connection details not found in environment variables. Please check your .env file.")

        print("Connecting to Neo4j AuraDB...")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
        print("Successfully connected to Neo4j.")
    return _driver

def close_neo4j_driver():
    """
    Closes the Neo4j driver connection if it exists.
    """
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        print("Neo4j connection closed.")

# Example usage (for testing purposes)
if __name__ == "__main__":
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        print("Neo4j connectivity verified.")
    except (ValueError, Exception) as e:
        print(f"An error occurred: {e}")
    finally:
        close_neo4j_driver()
