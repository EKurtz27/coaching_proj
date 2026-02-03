"""
Coach Network REST API
FastAPI application for accessing coaching network data from Neo4j
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j_queries import get_query_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global queries instance
app_queries = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan: startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting Coach Network API")
    global app_queries
    try:
        app_queries = get_query_instance()
        logger.info("✅ Neo4j connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neo4j: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Coach Network API")
    if app_queries:
        try:
            app_queries.close()
            logger.info("✅ Neo4j connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Neo4j connection: {e}")


# Create FastAPI app
app = FastAPI(
    title="Coach Network API",
    description="Graph database API for exploring college football coaching networks. Find connections between coaches, discover paths, and generate challenges.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:8000",      # FastAPI docs
        "http://localhost:8080",      # Alternative dev
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        {"status": "healthy"}
    """
    return {"status": "healthy"}


@app.get("/api/status")
async def api_status():
    """
    Get API and database status
    
    Returns:
        {
            "api_status": "online",
            "database_status": "connected",
            "version": "2.0.0"
        }
    """
    try:
        if app_queries:
            # Quick test query
            stats = app_queries.get_network_statistics()
            db_status = "connected" if stats else "error"
        else:
            db_status = "not_initialized"
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        db_status = "error"
    
    return {
        "api_status": "online",
        "database_status": db_status,
        "version": "2.0.0"
    }


# ==================== Search Endpoints ====================

@app.get("/api/search/coaches")
async def search_coaches(query: str, limit: int = 20):
    """
    Search for coaches by name (case-insensitive substring match)
    
    Query Parameters:
        - query (str, required): Search term (e.g., "Dan")
        - limit (int, optional): Maximum results (default: 20, max: 100)
    
    Returns:
        {
            "results": [
                {"name": "Dan Lanning"},
                {"name": "Dan Mullen"}
            ],
            "count": 2,
            "query": "Dan"
        }
    """
    if not query or len(query.strip()) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Search query cannot be empty"}
        )
    
    if limit < 1 or limit > 100:
        limit = 20
    
    try:
        results = app_queries.search_coaches(query, limit)
        return {
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Search failed"}
        )


@app.get("/api/search/coaches/{coach_name}")
async def get_coach_details(coach_name: str):
    """
    Get detailed information about a coach
    
    Path Parameters:
        - coach_name (str): Exact coach name (e.g., "Nick Saban")
    
    Returns:
        {
            "name": "Nick Saban",
            "in_degree": 45,
            "out_degree": 20,
            "total_connections": 65,
            "teams_worked_for": 3
        }
    """
    if not coach_name or len(coach_name.strip()) == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Coach name cannot be empty"}
        )
    
    try:
        details = app_queries.get_coach_details(coach_name)
        if not details:
            return JSONResponse(
                status_code=404,
                content={"error": f"Coach '{coach_name}' not found"}
            )
        return details
    except Exception as e:
        logger.error(f"Get coach details error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve coach details"}
        )


# ==================== Pathfinding Endpoints ====================

@app.get("/api/paths/shortest")
async def find_shortest_path(coach1: str, coach2: str):
    """
    Find the shortest path between two coaches
    
    Query Parameters:
        - coach1 (str, required): Starting coach name
        - coach2 (str, required): Ending coach name
        - max_depth (int, optional): Maximum hops to search (default: 5)
    
    Returns:
        {
            "path": [
                {"name": "Coach A"},
                {"name": "Coach B"},
                {"name": "Coach C"}
            ],
            "length": 3,
            "connections": [
                {
                    "from": "Coach A",
                    "to": "Coach B",
                    "description": "Worked together at Team X"
                }
            ]
        }
    """
    if not coach1 or not coach2 or coach1.strip() == "" or coach2.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Both coach1 and coach2 are required"}
        )
    
    if coach1.lower() == coach2.lower():
        return JSONResponse(
            status_code=400,
            content={"error": "coach1 and coach2 must be different"}
        )
    
    try:
        path = app_queries.find_shortest_path(coach1, coach2)
        if not path:
            return JSONResponse(
                status_code=404,
                content={"error": f"No path found between '{coach1}' and '{coach2}' within 5 hops"}
            )
        return path
    except Exception as e:
        logger.error(f"Shortest path error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Pathfinding failed"}
        )


@app.get("/api/paths/all")
async def find_all_paths(coach1: str, coach2: str, limit: int = 5):
    """
    Find multiple paths between two coaches
    
    Query Parameters:
        - coach1 (str, required): Starting coach name
        - coach2 (str, required): Ending coach name
        - max_depth (int, optional): Maximum hops per path (default: 4)
        - limit (int, optional): Maximum number of paths to return (default: 5)
    
    Returns:
        {
            "paths": [
                {
                    "path": [{"name": "A"}, {"name": "B"}],
                    "length": 2
                },
                ...
            ],
            "total_paths": 3
        }
    """
    if not coach1 or not coach2:
        return JSONResponse(
            status_code=400,
            content={"error": "Both coach1 and coach2 are required"}
        )
    
    if coach1.lower() == coach2.lower():
        return JSONResponse(
            status_code=400,
            content={"error": "coach1 and coach2 must be different"}
        )
    
    # if max_depth < 1:
    #     max_depth = 4
    # if limit < 1 or limit > 20:
    #     limit = 5
    
    try:
        paths = app_queries.find_all_paths(coach1, coach2, max_depth, limit)
        if not paths:
            return JSONResponse(
                status_code=404,
                content={"error": f"No paths found between '{coach1}' and '{coach2}'"}
            )
        return {
            "paths": paths,
            "total_paths": len(paths)
        }
    except Exception as e:
        logger.error(f"All paths error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Pathfinding failed"}
        )


# ==================== Network Analysis ====================

@app.get("/api/network")
async def get_coaching_network(year: int = None, team: str = None):
    """
    Get coaching network data for visualization
    
    Query Parameters:
        - year (int, optional): Filter by year
        - team (str, optional): Filter by team name
    
    Returns:
        {
            "nodes": [
                {"id": "coach_1", "label": "Nick Saban", "type": "coach"},
                {"id": "team_1", "label": "Alabama", "type": "team"}
            ],
            "edges": [
                {"source": "coach_1", "target": "team_1", "relationship": "WORKED_FOR"}
            ],
            "node_count": 150,
            "edge_count": 450,
            "filters": {"year": 2024, "team": "Alabama"}
        }
    """
    try:
        network = app_queries.get_coaching_network(year=year, team=team)
        if not network:
            return JSONResponse(
                status_code=404,
                content={"error": "No network data found for the given filters"}
            )
        return network
    except Exception as e:
        logger.error(f"Network retrieval error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve network data"}
        )


@app.get("/api/network/connections/{coach_name}")
async def get_coach_connections(coach_name: str, depth: int = 1):
    """
    Get a coach's connection neighborhood
    
    Path Parameters:
        - coach_name (str): Coach name
    
    Query Parameters:
        - depth (int, optional): Connection depth (1-3, default: 1)
    
    Returns:
        {
            "center_coach": "Nick Saban",
            "depth": 1,
            "nodes": [...],
            "edges": [...],
            "connection_count": 65
        }
    """
    if not coach_name or coach_name.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Coach name is required"}
        )
    
    if depth < 1 or depth > 3:
        depth = 1
    
    try:
        connections = app_queries.get_coach_connections(coach_name, depth)
        if not connections:
            return JSONResponse(
                status_code=404,
                content={"error": f"Coach '{coach_name}' not found"}
            )
        return connections
    except Exception as e:
        logger.error(f"Coach connections error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve connections"}
        )


# ==================== Statistics ====================

@app.get("/api/statistics/network")
async def get_network_statistics():
    """
    Get overall network statistics
    
    Returns:
        {
            "total_coaches": 1118,
            "total_teams": 2593,
            "total_connections": 26695,
            "avg_connections": 23.88
        }
    """
    try:
        stats = app_queries.get_network_statistics()
        if not stats:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to calculate statistics"}
            )
        return stats
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve statistics"}
        )


@app.get("/api/statistics/coaches/top-connected")
async def get_most_connected_coaches(limit: int = 10):
    """
    Get the most connected coaches (by degree centrality)
    
    Query Parameters:
        - limit (int, optional): Number of coaches to return (default: 10, max: 50)
    
    Returns:
        {
            "coaches": [
                {"rank": 1, "name": "Lane Kiffin", "connections": 69},
                {"rank": 2, "name": "Nick Saban", "connections": 65},
                ...
            ],
            "limit": 10
        }
    """
    if limit < 1 or limit > 50:
        limit = 10
    
    try:
        coaches = app_queries.get_most_connected_coaches(limit)
        if not coaches:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to retrieve top coaches"}
            )
        
        # Add rank
        ranked = [
            {**coach, "rank": idx + 1}
            for idx, coach in enumerate(coaches)
        ]
        
        return {
            "coaches": ranked,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Top coaches error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve top coaches"}
        )


@app.get("/api/statistics/teams")
async def get_teams_list():
    """
    Get list of all teams in the network
    
    Returns:
        {
            "teams": ["Abilene Christian", "Air Force", "Alabama", ...],
            "count": 2593,
            "years_range": [2000, 2024]
        }
    """
    try:
        teams = app_queries.get_teams_list()
        years_min, years_max = app_queries.get_years_range()
        
        return {
            "teams": teams,
            "count": len(teams),
            "years_range": [years_min, years_max]
        }
    except Exception as e:
        logger.error(f"Teams list error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve teams list"}
        )


@app.get("/api/statistics/years")
async def get_years_range():
    """
    Get the year range of data in the network
    
    Returns:
        {
            "min_year": 2000,
            "max_year": 2024
        }
    """
    try:
        min_year, max_year = app_queries.get_years_range()
        return {
            "min_year": min_year,
            "max_year": max_year
        }
    except Exception as e:
        logger.error(f"Years range error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve years range"}
        )


# ==================== Centrality Measures ====================

@app.get("/api/centrality/coaches/{coach_name}")
async def get_coach_centrality(coach_name: str):
    """
    Get centrality measures for a coach
    
    Path Parameters:
        - coach_name (str): Coach name
    
    Returns:
        {
            "name": "Nick Saban",
            "in_degree": 45,
            "out_degree": 20,
            "total_degree": 65
        }
    """
    if not coach_name or coach_name.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Coach name is required"}
        )
    
    try:
        centrality = app_queries.get_coach_centrality(coach_name)
        if not centrality:
            return JSONResponse(
                status_code=404,
                content={"error": f"Coach '{coach_name}' not found"}
            )
        return centrality
    except Exception as e:
        logger.error(f"Centrality error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to calculate centrality"}
        )


@app.get("/api/centrality/betweenness/top")
async def get_betweenness_centrality_top(limit: int = 10):
    """
    Get top bridge coaches (betweenness centrality)
    Bridge coaches are those who connect different parts of the network
    
    Query Parameters:
        - limit (int, optional): Number of coaches to return (default: 10, max: 50)
    
    Returns:
        {
            "bridge_coaches": [
                {"rank": 1, "name": "Coach A", "bridge_score": 0.95},
                ...
            ]
        }
    """
    if limit < 1 or limit > 50:
        limit = 10
    
    try:
        coaches = app_queries.get_betweenness_centrality_top(limit)
        if not coaches:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to retrieve bridge coaches"}
            )
        
        ranked = [
            {**coach, "rank": idx + 1}
            for idx, coach in enumerate(coaches)
        ]
        
        return {
            "bridge_coaches": ranked
        }
    except Exception as e:
        logger.error(f"Betweenness centrality error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve bridge coaches"}
        )


# ==================== Challenge Endpoints ====================

@app.get("/api/challenge/generate")
async def generate_challenge(steps: int = 3):
    """
    Generate a user challenge by randomly walking through the network
    
    Users get two coach names and must find a path between them.
    The system guarantees a path exists.
    
    Query Parameters:
        - steps (int, optional): Difficulty level (1-5, default: 3)
          1-2: Easy
          3-4: Medium
          5+: Hard
    
    Returns:
        {
            "start_coach": "Nick Saban",
            "end_coach": "Dan Lanning",
            "steps": 3,
            "difficulty": "medium",
            "hint": "There is a path with 3 connection(s) between these coaches"
        }
    """
    if steps < 1 or steps > 5:
        steps = 3
    
    try:
        challenge = app_queries.generate_challenge(steps)
        if not challenge:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to generate challenge"}
            )
        return challenge
    except Exception as e:
        logger.error(f"Challenge generation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate challenge"}
        )


# ==================== Root & Info ====================

@app.get("/")
async def root():
    """
    API root endpoint with information
    """
    return {
        "name": "Coach Network API",
        "version": "2.0.0",
        "description": "Graph database API for exploring college football coaching networks",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "status": "/api/status",
            "search": "/api/search/coaches",
            "pathfinding": "/api/paths/shortest",
            "network": "/api/network",
            "statistics": "/api/statistics/network",
            "challenge": "/api/challenge/generate"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
