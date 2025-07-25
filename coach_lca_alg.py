import pickle
import networkx as nx
from basic_graph_generation import *

# input_file_name = input("Please enter the path to the CSV file you wish to read: ").strip()
# with open(f"{input_file_name}", "r") as coach_jobs_csv:
#     coach_jobs_df = pd.read_csv(coach_jobs_csv)
# position_encoding(coach_jobs_df)
# G = create_nx_graph(coach_jobs_df)

# pickle.dump(G, open('data/full_coach_network.pickle', 'wb'))


G = pickle.load(open('data/full_coach_network.pickle', 'rb'))

test_subject = "Dan Lanning"
test_year = 2024


def find_team_of_coach_year(graph: nx.MultiDiGraph, coach: str, year: int) -> str:
    possible_edges = graph.in_edges(coach)
    for node1, node2 in possible_edges:
        for k, edge in graph[node1][node2].items():
            years = edge.get('years_of_connection')
            if years != None and year in years: # If years exists, and year is in it
                return edge.get("team_of_connection")
        
team = find_team_of_coach_year(G, "Dan Lanning", 2024)
print(team)

def keep_only_mentorship_true_edges(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    edges_to_remove = []
    for u, v, k, edge_data in graph.edges(data=True, keys=True):
        mentorship_status = edge_data.get("mentor_status", "")
        if mentorship_status not in ("Mentor", "Equal Standing"):
            edges_to_remove.append((u, v, k))
    for u, v, k in edges_to_remove:
        graph.remove_edge(u, v, k)
    return graph

def remove_future_edges(graph:nx.MultiDiGraph, last_valid_year: str) -> nx.MultiDiGraph: # Fix to collect before removal. Add keys
    edges_to_remove = []
    for u, v, k, edge_data in graph.edges(data=True, keys=True):
        years = edge_data.get("years_of_connection")
        if all(y > last_valid_year for y in years):
            edges_to_remove.append((u, v, k))
    for u, v, k in edges_to_remove:
        graph.remove_edge(u, v, k)
    return graph

def remove_edges_of_current_staff(graph: nx.MultiDiGraph, coach: str,  year: int) -> nx.MultiDiGraph: # Fix to collect before removal. Add keys
    edges_to_remove = []
    for u, v, k, edge_data in graph.edges(data=True, keys= True):
        years = edge_data.get("years_of_connection")
        team = edge_data.get("team_of_connection")
        if test_year in years and team == find_team_of_coach_year(G, "Dan Lanning", 2024):
            edges_to_remove.append((u, v, k))
    for u, v, k in edges_to_remove:
        graph.remove_edge(u, v, k)
    return graph


def clean_graph(graph: nx.MultiDiGraph, coach: str, last_valid_year: int) -> nx.MultiDiGraph:
    # print(G.number_of_edges())
    keep_only_mentorship_true_edges(graph)
    remove_future_edges(graph, last_valid_year)
    remove_edges_of_current_staff(graph, coach, last_valid_year)
    # print(G.number_of_edges())

def find_lowest_common_ancestor(cleaned_graph: nx.MultiDiGraph, coach1: str, coach2: str):
    coach1_ancestors = nx.ancestors(cleaned_graph, coach1)
    coach2_ancestors = nx.ancestors(cleaned_graph, coach2)

    shared_ancestors = coach1_ancestors & coach2_ancestors

    if shared_ancestors == None:
        print("Error: no shared ancestors")
    min_dist = float('inf')
    closest = None
    rev_graph = cleaned_graph.reverse(copy=True)
    for ancestor in shared_ancestors:
        dist1 = nx.shortest_path_length(rev_graph, coach1, ancestor)
        dist2 = nx.shortest_path_length(rev_graph, coach2, ancestor)
        total_dist = dist1 + dist2
        if total_dist < min_dist:
            min_dist = total_dist
            closest = ancestor
    # # Get the list of nodes in the shortest path, debugging check
    sp1 = nx.shortest_path(cleaned_graph, coach1, closest)
    print(f"sp1: {sp1}")
    sp2 = nx.shortest_path(cleaned_graph, coach2, closest)
    print(f"sp2: {sp2}")
    # Current status: works (kinda)! Issue is that connections are drawn with no respect for year
    # Example: **Dan Lanning -> Brad Sherrod -> Justin Burke <- **Will Stein
    # Brad Sherrod did coach under Justin Burke in 2022/2023, but that is **after** Dan Lanning coached under Brad Sherrod in 2014
    # This doesn't accurately represent the passing down of coaching theory
    # Possible solution: custom BFS search that takes year into account after finding shared descendents
    return closest, min_dist

first_edge = next(iter(G.edges(data=True)))
print(first_edge)

clean_graph(G, "Dan Lanning", 2025)
closest, min_dist = find_lowest_common_ancestor(G, "Dan Lanning", "Will Stein")
print(closest)
print(min_dist) 