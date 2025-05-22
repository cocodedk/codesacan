import os
from neo4j import GraphDatabase
from .constants import NEO4J_HOST, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

def clear_database(session):
    """Clear all nodes and relationships in the database."""
    print("Clearing database...")
    session.run("MATCH (n) DETACH DELETE n")

def get_db_session():
    """Create and return a Neo4j database session."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver.session()

def close_db_connection(driver):
    """Close the Neo4j database connection."""
    driver.close()

def print_db_info():
    """Print database connection information and usage instructions."""
    print("Analysis complete. View the graph in Neo4j Browser with commands:")
    print(f"- Neo4j Browser: http://{NEO4J_HOST}:{os.getenv('NEO4J_PORT_HTTP', '7400')}")
    print("- Show all nodes: MATCH (n) RETURN n")
    print("- Find functions by line: MATCH (f:Function) WHERE f.line > 100 RETURN f")
    print("- Show relationships: MATCH (n)-[r]->(m) RETURN n, r, m")
    print("- Show calls at specific line: MATCH ()-[r:CALLS {line: 42}]->() RETURN r")
