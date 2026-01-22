"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ==================== Search Models ====================

class CoachResponse(BaseModel):
    """Single coach in search results"""
    name: str = Field(..., description="Coach name")
    
    class Config:
        json_json_schema_extra = {
            "example": {"name": "Nick Saban"}
        }


class SearchCoachesResponse(BaseModel):
    """Search results for coaches"""
    results: List[CoachResponse]
    count: int = Field(..., description="Number of results")
    query: str = Field(..., description="Search query used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {"name": "Dan Lanning"},
                    {"name": "Dan Mullen"}
                ],
                "count": 2,
                "query": "Dan"
            }
        }


class CoachDetailsResponse(BaseModel):
    """Detailed coach information"""
    name: str
    in_degree: int = Field(..., description="Number of incoming connections")
    out_degree: int = Field(..., description="Number of outgoing connections")
    total_connections: int = Field(..., description="Total connections")
    teams_worked_for: int = Field(..., description="Number of teams worked for")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nick Saban",
                "in_degree": 45,
                "out_degree": 20,
                "total_connections": 65,
                "teams_worked_for": 3
            }
        }


# ==================== Pathfinding Models ====================

class PathCoach(BaseModel):
    """Coach in a path"""
    name: str


class ConnectionDetail(BaseModel):
    """Details about a connection between coaches"""
    from_coach: str = Field(..., alias="from")
    to_coach: str = Field(..., alias="to")
    description: Optional[str] = None
    year: Optional[int] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "from": "Coach A",
                "to": "Coach B",
                "description": "Worked together at Alabama",
                "year": 2015
            }
        }


class PathResponse(BaseModel):
    """Shortest path between two coaches"""
    path: List[PathCoach]
    length: int = Field(..., description="Number of hops")
    connections: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": [
                    {"name": "Coach A"},
                    {"name": "Coach B"},
                    {"name": "Coach C"}
                ],
                "length": 3,
                "connections": []
            }
        }


class AllPathsResponse(BaseModel):
    """Multiple paths between two coaches"""
    paths: List[PathResponse]
    total_paths: int


# ==================== Network Models ====================

class NetworkNode(BaseModel):
    """Node in network visualization"""
    id: str
    label: str
    type: str = Field(..., description="'coach' or 'team'")


class NetworkEdge(BaseModel):
    """Edge in network visualization"""
    source: str
    target: str
    relationship: Optional[str] = None


class NetworkResponse(BaseModel):
    """Network data for visualization"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    node_count: int
    edge_count: int
    filters: Optional[Dict[str, Any]] = None


class CoachConnectionsResponse(BaseModel):
    """Coach's connection neighborhood"""
    center_coach: str
    depth: int
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    connection_count: int


# ==================== Statistics Models ====================

class NetworkStatsResponse(BaseModel):
    """Overall network statistics"""
    total_coaches: int
    total_teams: int
    total_connections: int
    avg_connections: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_coaches": 1118,
                "total_teams": 2593,
                "total_connections": 26695,
                "avg_connections": 23.88
            }
        }


class RankedCoach(BaseModel):
    """Coach with ranking"""
    rank: int
    name: str
    connections: int


class TopCoachesResponse(BaseModel):
    """Most connected coaches"""
    coaches: List[RankedCoach]
    limit: int


class TeamsListResponse(BaseModel):
    """List of all teams"""
    teams: List[str]
    count: int
    years_range: List[int] = Field(..., description="[min_year, max_year]")


class YearsRangeResponse(BaseModel):
    """Year range of data"""
    min_year: int
    max_year: int


# ==================== Centrality Models ====================

class CoachCentralityResponse(BaseModel):
    """Centrality measures for a coach"""
    name: str
    in_degree: int = Field(..., description="Incoming connections")
    out_degree: int = Field(..., description="Outgoing connections")
    total_degree: int = Field(..., description="Total connections")


class RankedBridgeCoach(BaseModel):
    """Bridge coach with ranking"""
    rank: int
    name: str
    bridge_score: float


class BetweennessCentralityResponse(BaseModel):
    """Top bridge coaches"""
    bridge_coaches: List[RankedBridgeCoach]


# ==================== Challenge Models ====================

class ChallengeResponse(BaseModel):
    """Challenge generation response"""
    start_coach: str = Field(..., description="Starting coach for the challenge")
    end_coach: str = Field(..., description="Ending coach for the challenge")
    steps: int = Field(..., description="Actual number of steps in guaranteed path")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard, impossible")
    hint: str = Field(..., description="Hint about the challenge")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_coach": "Nick Saban",
                "end_coach": "Dan Lanning",
                "steps": 3,
                "difficulty": "medium",
                "hint": "There is a path with 3 connection(s) between these coaches"
            }
        }


# ==================== Status Models ====================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="'healthy' or error description")


class StatusResponse(BaseModel):
    """API status response"""
    api_status: str = Field(..., description="'online' or 'offline'")
    database_status: str = Field(..., description="'connected', 'error', or 'not_initialized'")
    version: str = Field(..., description="API version")


class RootResponse(BaseModel):
    """Root endpoint response"""
    name: str
    version: str
    description: str
    docs: str
    endpoints: Dict[str, str]


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = None
    status_code: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Coach not found",
                "detail": "Coach 'Invalid Name' does not exist in the network",
                "status_code": 404
            }
        }
