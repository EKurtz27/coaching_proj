"""
Neo4j Query Utilities
Helper functions for common graph queries used by the API and frontend
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

load_dotenv()


class CoachNetworkQueries:
    """Query builder for coach network operations"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    # ==================== Search Queries ====================
    
    def search_coaches(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search for coaches by name (case-insensitive substring match)"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach)
                WHERE toLower(c.name) CONTAINS toLower($search_term)
                RETURN c.name as name
                LIMIT $limit
                """,
                search_term=search_term,
                limit=limit
            )
            return [{"name": row["name"]} for row in result]
    
    def get_coach_details(self, coach_name: str) -> Optional[Dict]:
        """Get detailed information about a coach"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach {name: $name})
                WITH c, 
                     COUNT {(c)-[:CONNECTED_TO]->()} as out_degree,
                     COUNT {(c)<-[:CONNECTED_TO]-()} as in_degree,
                     COUNT {(c)-[:WORKED_FOR]->()} as teams_count
                RETURN {
                    name: c.name,
                    out_connections: out_degree,
                    in_connections: in_degree,
                    teams: teams_count
                } as coach_info
                """,
                name=coach_name
            )
            row = result.single()
            return row["coach_info"] if row else None
    
    # ==================== Path Finding Queries ====================
    
    def find_shortest_path(self, coach1: str, coach2: str) -> Optional[Dict]:
        """
        Find the shortest connection path between two coaches
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (start:Coach {name: $coach1})
                MATCH (end:Coach {name: $coach2})
                MATCH path = SHORTEST 1 ((start)-[:CONNECTED_TO]-+(end))
                WITH nodes(path) as nodes, relationships(path) as rels, length(path) as len
                RETURN {
                    length: len,
                    coaches: [n in nodes | n.name],
                    connections: [r in rels | {
                        from: startNode(r).name,
                        to: endNode(r).name,
                        relationship: r.relationship,
                        team: r.team_of_connection,
                        years: r.years_of_connection
                    }]
                } as path_data
                """,
                coach1=coach1,
                coach2=coach2
            )
            row = result.single()
            return row["path_data"] if row else None
    
    def find_all_paths(self, coach1: str, coach2: str, limit: int = 10) -> List[Dict]:
        """Find multiple connection paths between coaches"""
        with self.driver.session() as session:
            result = session.run( ###Replace X with a number, find a way to convert this into difficulty (avg length? number of paths doesn't work, too many paths)
                """ 
                MATCH path = SHORTEST X (start:Coach {name: $coach1})-[:CONNECTED_TO*1..10]-(end:Coach {name: $coach2})
                WITH nodes(path) as nodes, relationships(path) as rels, length(path) as path_length
                RETURN {
                    length: path_length,
                    coaches: [n in nodes | n.name],
                    connections: [r in rels | {
                        from: startNode(r).name,
                        to: endNode(r).name,
                        relationship: r.relationship,
                        team: r.team_of_connection,
                        years: r.years_of_connection
                    }]
                } as path_data
                ORDER BY path_length ASC
                LIMIT $limit
                """,
                coach1=coach1,
                coach2=coach2,
                limit=limit
            )
            return [row["path_data"] for row in result]
    
    # ==================== Network Analysis Queries ====================
    
    def get_coaching_network(self, year: Optional[int] = None, team: Optional[str] = None) -> Dict:
        """
        Get network data for visualization
        Can filter by year and/or team
        """
        filters = []
        params = {}
        
        if year:
            filters.append("$year in r.years_of_connection")
            params["year"] = year
        
        if team:
            filters.append("r.team_of_connection = $team")
            params["team"] = team
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        with self.driver.session() as session:
            # Get nodes
            nodes_result = session.run(
                """
                MATCH (c:Coach)-[r:CONNECTED_TO]->()
                WHERE """ + where_clause + """
                WITH DISTINCT c
                RETURN {
                    id: c.name,
                    label: c.name,
                    type: "coach"
                } as node
                """,
                **params
            )
            nodes = [row["node"] for row in nodes_result]
            
            # Get edges
            edges_result = session.run(
                """
                MATCH (source:Coach)-[r:CONNECTED_TO]->(target:Coach)
                WHERE """ + where_clause + """
                RETURN {
                    id: r.id,
                    source: source.name,
                    target: target.name,
                    relationship: r.relationship,
                    team: r.team_of_connection,
                    years: r.years_of_connection,
                    mentor_status: r.mentor_status,
                    source_position: r.source_position,
                    target_position: r.target_position
                } as edge
                """,
                **params
            )
            edges = [row["edge"] for row in edges_result]
            
            return {"nodes": nodes, "edges": edges}
    
    def get_coach_connections(self, coach_name: str, depth: int = 1) -> Dict:
        """Get all connections for a specific coach"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (coach:Coach {name: $name})-[r:CONNECTED_TO*1..$depth]-(connected:Coach)
                WITH coach, connected, r
                RETURN {
                    coach: coach.name,
                    connections: collect(DISTINCT {
                        name: connected.name,
                        hops: length(r)
                    })
                } as data
                """,
                name=coach_name,
                depth=depth
            )
            row = result.single()
            return row["data"] if row else {"coach": coach_name, "connections": []}
    
    # ==================== Statistics Queries ====================
    
    def get_most_connected_coaches(self, limit: int = 10) -> List[Dict]:
        """Get coaches with most connections (high degree centrality)"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach)
                WITH c, COUNT {(c)-[:CONNECTED_TO]->()} + COUNT {(c)<-[:CONNECTED_TO]-()} as total_connections
                RETURN {
                    name: c.name,
                    connections: total_connections
                } as coach
                ORDER BY total_connections DESC
                LIMIT $limit
                """,
                limit=limit
            )
            return [row["coach"] for row in result]
    
    def get_network_statistics(self) -> Dict:
        """Get overall network statistics"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach)
                WITH count(c) as total_coaches
                MATCH (t:Team)
                WITH total_coaches, count(t) as total_teams
                MATCH ()-[r:CONNECTED_TO]-()
                WITH total_coaches, total_teams, count(r) as total_connections
                MATCH (c:Coach)
                WITH total_coaches, total_teams, total_connections,
                     avg(COUNT {(c)-[:CONNECTED_TO]->()} + COUNT {(c)<-[:CONNECTED_TO]-()} * 1.0) as avg_degree
                RETURN {
                    total_coaches: total_coaches,
                    total_teams: total_teams,
                    total_connections: total_connections,
                    avg_connections: avg_degree
                } as stats
                """
            )
            return result.single()["stats"]
    
    def get_teams_list(self) -> List[str]:
        """Get all teams in the network"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Team)
                RETURN t.name as name
                ORDER BY name ASC
                """
            )
            return [row["name"] for row in result]
    
    def get_years_range(self) -> Tuple[int, int]:
        """Get minimum and maximum years in the network"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH ()-[r:CONNECTED_TO]-()
                WITH r.years_of_connection as years
                UNWIND years as year
                RETURN min(year) as min_year, max(year) as max_year
                """
            )
            row = result.single()
            if row:
                return (row["min_year"], row["max_year"])
            return (None, None)
    
    # ==================== Centrality Measures ====================
    
    def get_coach_centrality(self, coach_name: str) -> Dict:
        """Calculate centrality measures for a coach"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach {name: $name})
                WITH c,
                     COUNT {(c)-[:CONNECTED_TO]->()} as out_degree,
                     COUNT {(c)<-[:CONNECTED_TO]-()} as in_degree
                RETURN {
                    name: c.name,
                    out_degree: out_degree,
                    in_degree: in_degree,
                    total_degree: out_degree + in_degree
                } as centrality
                """,
                name=coach_name
            )
            row = result.single()
            return row["centrality"] if row else None
    
    def get_betweenness_centrality_top(self, limit: int = 10) -> List[Dict]:
        """
        Get coaches who are bridges between different parts of the network
        (simplified betweenness approximation)
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Coach)
                WITH c, 
                     COUNT {(c)-[:CONNECTED_TO]->()} as out_deg,
                     COUNT {(c)<-[:CONNECTED_TO]-()} as in_deg
                RETURN {
                    name: c.name,
                    bridge_score: (out_deg * in_deg)
                } as coach
                ORDER BY coach.bridge_score DESC
                LIMIT $limit
                """,
                limit=limit
            )
            return [row["coach"] for row in result]
    
    # ==================== Challenge Generation ====================
    
    def generate_challenge(self, steps: int = 3) -> Optional[Dict]:
        """
        Generate a user challenge by randomly walking through the network
        
        Algorithm:
        1. Pick a random coach from the network
        2. Follow random CONNECTED_TO edges for `steps` hops
        3. Record the path for validation
        4. Return start coach, end coach, and difficulty info
        
        Args:
            steps: Number of hops to walk (default 3)
                  Recommended: 2-5 (higher = harder)
        
        Returns:
            {
                "start_coach": "Nick Saban",
                "end_coach": "Dan Lanning", 
                "steps": 3,
                "difficulty": "medium",
                "hint": "There is definitely a path between these coaches"
            }
        """
        with self.driver.session() as session:
            # Step 1: Start at random coach
            result = session.run(
                """
                MATCH (c:Coach)
                RETURN c.name as name
                ORDER BY rand()
                LIMIT 1
                """
            )
            start_row = result.single()
            if not start_row:
                return None
            
            start_coach = start_row["name"]
            current_coach = start_coach
            path_taken = [start_coach]
            
            # Step 2-N: Random walk through network
            for hop in range(steps):
                result = session.run(
                    """
                    MATCH (current:Coach {name: $current})-[:CONNECTED_TO]->(next:Coach)
                    RETURN next.name as name
                    ORDER BY rand()
                    LIMIT 1
                    """,
                    current=current_coach
                )
                next_row = result.single()
                
                # If no connections available, stop walking
                if not next_row:
                    break
                
                current_coach = next_row["name"]
                path_taken.append(current_coach)
            
            # Step 3: Determine difficulty based on actual path length
            actual_steps = len(path_taken) - 1
            
            if actual_steps == 0:
                difficulty = "impossible"  # No path found
            elif actual_steps == 1:
                difficulty = "easy"
            elif actual_steps == 2:
                difficulty = "easy"
            elif actual_steps == 3:
                difficulty = "medium"
            elif actual_steps == 4:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            return {
                "start_coach": start_coach,
                "end_coach": current_coach,
                "steps": actual_steps,
                "difficulty": difficulty,
                "hint": f"There is a path with {actual_steps} connection(s) between these coaches"
            }


def get_query_instance() -> CoachNetworkQueries:
    """Get query instance with environment variables"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")
    
    return CoachNetworkQueries(uri, user, password)


if __name__ == "__main__":
    # Test queries
    queries = get_query_instance()
    
    try:
        print("🧪 Testing Neo4j Queries\n")
        
        # Get stats
        stats = queries.get_network_statistics()
        print(f"Network Stats: {stats}\n")
        
        # Get teams
        teams = queries.get_teams_list()
        print(f"Teams ({len(teams)}): {teams[:5]}...\n")
        
        # Get top coaches
        top = queries.get_most_connected_coaches(5)
        print(f"Top connected coaches: {top}\n")
        
        # Search
        search_results = queries.search_coaches("Dan", 5)
        print(f"Search for 'Dan': {search_results}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        queries.close()
