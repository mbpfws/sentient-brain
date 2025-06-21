from neo4j import GraphDatabase, Driver
from ...core.config import settings

class Neo4jDriver:
    _driver: Driver = None

    @classmethod
    def get_driver(cls) -> Driver:
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Check if the connection is valid
                cls._driver.verify_connectivity()
                print("Successfully connected to Neo4j.")
            except Exception as e:
                print(f"Failed to connect to Neo4j: {e}")
                raise
        return cls._driver

    @classmethod
    def close_driver(cls):
        if cls._driver is not None and cls._driver.closed() is False:
            cls._driver.close()
            cls._driver = None
            print("Neo4j connection closed.")

def get_neo4j_session():
    driver = Neo4jDriver.get_driver()
    return driver.session()
