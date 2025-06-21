import os
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Neo4jDriver:
    _driver: Driver = None

    def get_driver(self) -> Driver:
        if self._driver is None:
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USERNAME")
            password = os.getenv("NEO4J_PASSWORD")

            if not all([uri, user, password]):
                raise ValueError("NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set in the environment.")

            try:
                self._driver = GraphDatabase.driver(uri, auth=(user, password))
                self._driver.verify_connectivity()
                print("Successfully connected to Neo4j.", flush=True)
            except Exception as e:
                print(f"Failed to connect to Neo4j: {e}", flush=True)
                raise
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            print("Neo4j connection closed.", flush=True)

# Singleton instance
neo4j_driver = Neo4jDriver()

def get_neo4j_driver() -> Driver:
    return neo4j_driver.get_driver()

def close_neo4j_driver():
    neo4j_driver.close()

# This function is what CodeGraphService expects
def get_neo4j_session():
    driver = get_neo4j_driver()
    db_name = os.getenv("NEO4J_DATABASE", "neo4j")
    return driver.session(database=db_name)
