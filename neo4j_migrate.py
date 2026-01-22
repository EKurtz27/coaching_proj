"""
Data Migration Script
Reads coach network data from JSON and imports into Neo4j
"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


class CoachNetworkMigrator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {"coaches_created": 0, "teams_created": 0, "connections_created": 0}
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def load_json_data(self, filepath):
        """Load elements from JSON file"""
        print(f"📂 Loading JSON from {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   Loaded {len(data)} elements")
        return data
    
    def separate_nodes_and_edges(self, elements):
        """Separate nodes (coaches) and edges (connections) from elements"""
        nodes = []
        edges = []
        
        for element in elements:
            data = element.get("data", {})
            if "coach_name" in data:  # It's a coach node
                nodes.append(data)
            elif "source" in data and "target" in data:  # It's an edge
                edges.append(data)
        
        print(f"✓ Separated {len(nodes)} coach nodes and {len(edges)} connection edges")
        return nodes, edges
    
    def create_coach_nodes(self, coaches):
        """Create Coach nodes in Neo4j"""
        print(f"\n👥 Creating {len(coaches)} coach nodes...")
        
        with self.driver.session() as session:
            for coach_data in tqdm(coaches, desc="Coaches"):
                coach_name = coach_data.get("coach_name", "")
                if coach_name:
                    session.run(
                        """
                        MERGE (c:Coach {name: $name})
                        ON CREATE SET c.created_at = datetime()
                        """,
                        name=coach_name
                    )
                    self.stats["coaches_created"] += 1
        
        print(f"✓ Created {self.stats['coaches_created']} coach nodes")
    
    def create_team_nodes(self, edges):
        """Extract and create Team nodes from edges"""
        teams = set()
        for edge in edges:
            team = edge.get("team_of_connection", "")
            years = edge.get("years_of_connection", [])
            if team:
                for year in years:
                    teams.add((team, year))
        
        print(f"\n🏈 Creating {len(teams)} team nodes...")
        
        with self.driver.session() as session:
            for team, year in tqdm(teams, desc="Teams"):
                session.run(
                    """
                    MERGE (t:Team {name: $name, year: $year})
                    ON CREATE SET t.created_at = datetime()
                    """,
                    name=team,
                    year=year
                )
                self.stats["teams_created"] += 1
        
        print(f"✓ Created {self.stats['teams_created']} team nodes")
    
    def create_connections(self, edges):
        """Create CONNECTED_TO relationships between coaches"""
        print(f"\n🔗 Creating {len(edges)} connection edges...")
        
        with self.driver.session() as session:
            for edge in tqdm(edges, desc="Connections"):
                source = edge.get("source", "")
                target = edge.get("target", "")
                
                if source and target:
                    # Build relationship properties
                    rel_props = {
                        "id": edge.get("id", ""),
                        "description": edge.get("description", ""),
                        "relationship": edge.get("relationship", ""),
                        "encoded_connection": edge.get("encoded_connection", []),
                        "years_of_connection": edge.get("years_of_connection", []),
                        "team_of_connection": edge.get("team_of_connection", ""),
                        "mentor_status": edge.get("mentor_status", ""),
                        "source_position": edge.get("source_position", ""),
                        "target_position": edge.get("target_position", ""),
                    }
                    
                    session.run(
                        """
                        MATCH (source:Coach {name: $source})
                        MATCH (target:Coach {name: $target})
                        MERGE (source)-[r:CONNECTED_TO]->(target)
                        ON CREATE SET r += $props
                        """,
                        source=source,
                        target=target,
                        props=rel_props
                    )
                    self.stats["connections_created"] += 1
        
        print(f"✓ Created {self.stats['connections_created']} connection relationships")
    
    def create_coach_team_relationships(self, edges):
        """Create relationships between coaches and teams based on their connections"""
        print(f"\n📍 Creating coach-team relationships...")
        
        # Create a set of unique (coach, team) pairs
        coach_teams = set()
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            team = edge.get("team_of_connection", "")
            years = edge.get("years_of_connection", [])
            
            # Add ALL year-specific connections
            if source and team:
                for year in years: 
                    coach_teams.add((source, team, year, edge.get("source_position", "")))
            if target and team:
                for year in years: 
                    coach_teams.add((target, team, year, edge.get("target_position", "")))
        
        print(f"   Found {len(coach_teams)} unique coach-team-year associations")
        
        with self.driver.session() as session:
            for coach, team, year, position in tqdm(coach_teams, desc="Coach-Team Links"):
                session.run(
                    """
                    MATCH (c:Coach {name: $coach})
                    MATCH (t:Team {name: $team, year: $year})
                    MERGE (c)-[r:WORKED_FOR]->(t)
                    ON CREATE SET r.position = $position
                    """,
                    coach=coach,
                    team=team,
                    year=year,
                    position=position
                )
        
        print(f"✓ Created {len(coach_teams)} coach-team relationships")
    
    def migrate(self, json_filepath):
        """Execute full migration"""
        print("=" * 60)
        print("🚀 Starting Coach Network Migration to Neo4j")
        print("=" * 60)
        
        # Load and parse data
        elements = self.load_json_data(json_filepath)
        coaches, edges = self.separate_nodes_and_edges(elements)
        
        # Create nodes
        self.create_coach_nodes(coaches)
        self.create_team_nodes(edges)
        
        # Create relationships
        self.create_connections(edges)
        self.create_coach_team_relationships(edges)
        
        # Report
        print("\n" + "=" * 60)
        print("📊 Migration Statistics")
        print("=" * 60)
        print(f"  Coaches created:     {self.stats['coaches_created']}")
        print(f"  Teams created:       {self.stats['teams_created']}")
        print(f"  Connections created: {self.stats['connections_created']}")
        print("=" * 60)
        
        return self.stats


def get_migration_instance():
    """Get migrator with environment variables"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    
    return CoachNetworkMigrator(uri, user, password)


if __name__ == "__main__":
    # Use the visualization JSON file
    json_file = Path(__file__).parent / "data" / "mentor_only_elements_dump.json"
    
    migrator = get_migration_instance()
    
    try:
        migrator.migrate(str(json_file))
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        migrator.close()
