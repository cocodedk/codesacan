#!/usr/bin/env python3
"""
Test Neo4j Graph Queries for Code Analysis
This script tests the Neo4j database queries directly without using the MCP server.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_neo4j_graph_queries")

# Load environment variables
load_dotenv(".env", override=True)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7600")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "strongpassword")

def test_graph_summary():
    """Test the graph summary query."""
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session() as session:
            # Test graph summary query
            result = session.run("""
                MATCH (n)
                RETURN
                    count(n) as nodeCount,
                    size([x IN labels(n) WHERE x <> "Reference" | x]) as labelCount,
                    count(distinct labels(n)) as uniqueLabelCount
            """)
            summary = result.single()

            if summary and summary["nodeCount"] > 0:
                logger.info(f"Graph summary: {summary}")
                print(f"\nGraph contains {summary['nodeCount']} nodes with {summary['uniqueLabelCount']} unique labels")
                return True
            else:
                logger.warning("No data in graph or connection failed")
                return False

def test_function_query():
    """Test querying functions from the graph."""
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session() as session:
            # Test function query
            result = session.run("""
                MATCH (f:Function)
                RETURN f.name as name, f.file as file, f.line as line
                LIMIT 10
            """)

            functions = list(result)
            if functions:
                print("\nFound functions:")
                for func in functions:
                    print(f"  - {func['name']} ({func['file']}:{func['line']})")
                return True
            else:
                logger.warning("No functions found in graph or connection failed")
                return False

def test_call_relationships():
    """Test querying function call relationships."""
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        with driver.session() as session:
            # Test call relationship query
            result = session.run("""
                MATCH (caller:Function)-[:CALLS]->(callee:Function)
                RETURN caller.name as caller, callee.name as callee
                LIMIT 10
            """)

            calls = list(result)
            if calls:
                print("\nFound function calls:")
                for call in calls:
                    print(f"  - {call['caller']} calls {call['callee']}")
                return True
            else:
                logger.warning("No call relationships found in graph or connection failed")
                return False

def main():
    """Run all the tests."""
    tests = [
        ("Graph Summary", test_graph_summary),
        ("Function Query", test_function_query),
        ("Call Relationships", test_call_relationships)
    ]

    success = True
    for name, test_func in tests:
        print(f"\n=== Testing {name} ===")
        try:
            if not test_func():
                success = False
                logger.error(f"Test failed: {name}")
        except Exception as e:
            success = False
            logger.exception(f"Error during test {name}: {e}")

    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
