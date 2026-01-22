"""
Neo4j Setup and Configuration
Initializes the Neo4j database schema and creates indices for optimal performance.
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✓ Connected to Neo4j successfully")
            return True
        except ServiceUnavailable:
            print("✗ Failed to connect to Neo4j. Make sure the service is running.")
            return False
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def create_schema(self):
        """Create graph schema and indices"""
        with self.driver.session() as session:
            # Create indices for performance
            print("\n📊 Creating schema indices...")
            
            # Coach node index
            try:
                session.run(
                    """
                    CREATE INDEX coach_name IF NOT EXISTS 
                    FOR (c:Coach) ON (c.name)
                    """
                )
                print("✓ Created index on Coach.name")
            except Exception as e:
                print(f"  Coach name index may already exist: {e}")
            
            # Team node index
            try:
                session.run(
                    """
                    CREATE INDEX team_name IF NOT EXISTS 
                    FOR (t:Team) ON (t.name)
                    """
                )
                print("✓ Created index on Team.name")
            except Exception as e:
                print(f"  Team name index may already exist: {e}")
            
            # Edge ID index
            try:
                session.run(
                    """
                    CREATE INDEX connection_id IF NOT EXISTS 
                    FOR ()-[r:CONNECTED_TO]-() ON (r.id)
                    """
                )
                print("✓ Created index on CONNECTED_TO.id")
            except Exception as e:
                print(f"  Connection ID index may already exist: {e}")
    
    def clear_database(self):
        """Clear all nodes and relationships (DANGER - use with caution!)"""
        response = input("⚠️  This will DELETE all data in the Neo4j database. Type 'YES' to confirm: ")
        if response == "YES":
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                print("✓ Database cleared")
            return True
        else:
            print("✗ Operation cancelled")
            return False
    
    def get_db_stats(self):
        """Get database statistics"""
        with self.driver.session() as session:
            coaches = session.run("MATCH (c:Coach) RETURN count(c) as count").single()[0]
            teams = session.run("MATCH (t:Team) RETURN count(t) as count").single()[0]
            connections = session.run("MATCH ()-[r:CONNECTED_TO]-() RETURN count(r) as count").single()[0]
            
            print("\n📈 Database Statistics:")
            print(f"  Coaches: {coaches}")
            print(f"  Teams: {teams}")
            print(f"  Connections: {connections}")
            
            return {"coaches": coaches, "teams": teams, "connections": connections}


def get_connection():
    """Get Neo4j connection with environment variables"""
    # Default to local Neo4j instance
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    
    return Neo4jConnection(uri, user, password)


if __name__ == "__main__":
    print("🔧 Neo4j Setup Tool\n")
    
    conn = get_connection()
    
    if not conn.connect():
        print("\n❌ Cannot proceed without database connection")
        exit(1)
    
    print(f"\nUsing database: {conn.uri}")
    print(f"User: {conn.user}")
    
    conn.clear_database()
    # Create schema
    conn.create_schema()
    
    # Show stats
    conn.get_db_stats()
    
    conn.close()
    print("\n✓ Setup complete!")
