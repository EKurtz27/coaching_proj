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
#print(team)

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

def chronologic_sentsitive_bfs_shortest_path_length(graph: nx.MultiDiGraph, start_node: str, end_node: str) -> int:
    explored = set()
    queue = [[(start_node, None, None)]] # None as the previous edge
    distance_dict = {}
    distance_dict[start_node] = 0
    if start_node == end_node:
        print("Same node")
        return distance_dict[end_node], queue
    while queue:
        newly_explored = set()
        considered_path = queue.pop(0)
        considered_node, previous_edge_key, previous_edge_data = considered_path[-1] # How to best log keys? [u, k, v]? Then pull last 3 values?
        current_distance = distance_dict[considered_node]
        if previous_edge_data == None:
            previous_year = float("inf") # Any year will be valid
        else:
            previous_year = min(previous_edge_data.get("years_of_connection")) # Every new connection should have taken place before the previous
        preds = graph.pred[considered_node] # [(Coach, edge_data), (coach, edge_data)]?

        for coach_node, edges in preds.items():
            if coach_node not in explored:    
                for edge_key, edge_data in edges.items():
                    # need to collect coaches and add to list at end of neighbor adding
                    # so code can consider multiple edges from a coach but not circle back to them later
                    years_of_connection = edge_data.get("years_of_connection")
                    if all(y <= previous_year for y in years_of_connection): # Every new connection should have taken place before the previous
                        newly_explored.add(coach_node)
                        distance_dict[coach_node] = current_distance + 1
                        new_path = list(considered_path)
                        new_path.append( (coach_node, edge_key, edge_data) )
                        if coach_node == end_node:
                            return new_path
        explored.update(newly_explored)  
    return None                


def find_lowest_common_ancestor(cleaned_graph: nx.MultiDiGraph, coach1: str, coach2: str):
    coach1_ancestors = nx.ancestors(cleaned_graph, coach1)
    coach2_ancestors = nx.ancestors(cleaned_graph, coach2)

    shared_ancestors = coach1_ancestors & coach2_ancestors

    if shared_ancestors == None:
        print("Error: no shared ancestors")
    min_c1_path = None
    min_c2_path = None
    min_dist = float('inf')
    closest = None
    rev_graph = cleaned_graph.reverse(copy=True)
    for ancestor in shared_ancestors:
        coach1_to_ancestor_path = chronologic_sentsitive_bfs_shortest_path_length(cleaned_graph, coach1, ancestor)
        coach2_to_ancestor_path = chronologic_sentsitive_bfs_shortest_path_length(cleaned_graph, coach2, ancestor)
        if coach1_to_ancestor_path == None or coach2_to_ancestor_path == None:
            continue
        dist1 = len(coach1_to_ancestor_path) - 1
        dist2 = len(coach2_to_ancestor_path) - 1
        total_dist = dist1 + dist2
        if total_dist < min_dist:
            min_c1_path = coach1_to_ancestor_path
            min_c2_path = coach2_to_ancestor_path
            min_dist = total_dist
            closest = ancestor

    # Current status: works (kinda)! Issue is that connections are drawn with no respect for year
    # Example: **Dan Lanning -> Brad Sherrod -> Justin Burke <- **Will Stein
    # Brad Sherrod did coach under Justin Burke in 2022/2023, but that is **after** Dan Lanning coached under Brad Sherrod in 2014
    # This doesn't accurately represent the passing down of coaching theory
    # Possible solution: custom BFS search that takes year into account after finding shared descendents
    print(f"c1: {min_c1_path}")
    print(f"c2: {min_c2_path}")
    return closest, min_dist

# first_edge = next(iter(G.edges(data=True)))
# print(first_edge)

clean_graph(G, "Dan Lanning", 2025)
closest, min_dist = find_lowest_common_ancestor(G, "Dan Lanning", "Will Stein")
print(closest)
print(min_dist) 

# Lanning_preds = G.pred["Dan Lanning"]
# for coach, edge_dict in Lanning_preds.items():
#     for edge_key, edge_data in edge_dict.items():
#         print(f"{coach}: {edge_data.get("team_of_connection")}") #.get does work at this stage