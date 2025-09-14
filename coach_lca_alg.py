import pickle
import networkx as nx
import pandas as pd
from basic_graph_generation import *
import ast

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

def is_promotion(connection_years: set, edge_data) -> bool:
    if not connection_years:
        return False
    edge_final_year = max(edge_data.get("years_of_connection"))
    edge_first_year = min(edge_data.get("years_of_connection"))
    tracked_min_year = min(connection_years)
    tracked_max_year = max(connection_years)
    if (edge_final_year + 1 == tracked_min_year or
        edge_first_year - 1 == tracked_max_year):
        return True
    else:
        return False

def remove_edges_of_last_job(graph: nx.MultiDiGraph, team: str,  coach: str, last_valid_year: int) -> nx.MultiDiGraph: # Fix to collect before removal. Add keys
    hc_coach_connection_years = set()
    for u, v, k, edge_data in graph.edges(data=True, keys=True):
        if (1 in edge_data.get("encoded_connection") and
            (v == coach or u == coach) and edge_data.get("team_of_connection") == team and 
            (last_valid_year in edge_data.get("years_of_connection") or is_promotion(hc_coach_connection_years, edge_data))
            ): 
            # Issue: some people get promoted, creating a seperate edge (last valid year not in new edge) but should still be removed.
            # Solution? If lowest number in coach_connection_years is 1 less than a year in this edge, this represents a promotion
            hc_coach_edge_data = edge_data
            hc_coach_connection_years.update(edge_data.get("years_of_connection"))

    edges_to_remove = []
    for u, v, k, edge_data in graph.edges(data=True, keys= True):
        edge_years = edge_data.get("years_of_connection")
        edge_team = edge_data.get("team_of_connection")
        if any(y in edge_years for y in hc_coach_connection_years) and edge_team == team: # Make sure paths aren't drawn through edges formed while coach was already under current head coach
            edges_to_remove.append((u, v, k))
    for u, v, k in edges_to_remove:
        graph.remove_edge(u, v, k)
    return graph


def clean_graph(graph: nx.MultiDiGraph, team: str, coach: str, last_valid_year: int) -> nx.MultiDiGraph:
    # print(G.number_of_edges())
    new_graph = graph.copy()
    keep_only_mentorship_true_edges(new_graph)
    remove_future_edges(new_graph, last_valid_year)
    remove_edges_of_last_job(new_graph, team, coach, last_valid_year)
    # print(G.number_of_edges())
    return new_graph

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
                        queue.append(new_path)
        explored.update(newly_explored)  
    return None                


def find_lowest_common_ancestor(cleaned_graph: nx.MultiDiGraph, head_coach: str, coach2: str):
    min_dist = float('inf')
    closest = None
    is_direct_path = False
    direct_path_dist = None
    min_hc_path = None
    min_c2_path = None 
    direct_path = None

    head_coach_ancestors = nx.ancestors(cleaned_graph, head_coach)
    coach2_ancestors = nx.ancestors(cleaned_graph, coach2)

    if head_coach in coach2_ancestors:
        direct_path = chronologic_sentsitive_bfs_shortest_path_length(cleaned_graph, coach2, head_coach)
        if not direct_path == None:
            direct_path_dist = len(direct_path) - 1

    shared_ancestors = head_coach_ancestors & coach2_ancestors

    if shared_ancestors == None:
        print("Error: no shared ancestors")
        return None, float("inf"), False

    for ancestor in shared_ancestors:
        hc_to_ancestor_path = chronologic_sentsitive_bfs_shortest_path_length(cleaned_graph, head_coach, ancestor)
        coach2_to_ancestor_path = chronologic_sentsitive_bfs_shortest_path_length(cleaned_graph, coach2, ancestor)
        if hc_to_ancestor_path == None or coach2_to_ancestor_path == None:
            continue
        dist1 = len(hc_to_ancestor_path) - 1
        dist2 = len(coach2_to_ancestor_path) - 1
        total_dist = dist1 + dist2
        if total_dist < min_dist:
            min_hc_path = hc_to_ancestor_path
            min_c2_path = coach2_to_ancestor_path
            min_dist = total_dist
            closest = ancestor

    if direct_path_dist:
        if direct_path_dist < min_dist:
            min_dist = direct_path_dist
            min_hc_path = None
            min_c2_path = None
            closest = head_coach
            is_direct_path = True

    if closest == None:
        closest = "None" # Done for formatting the csv

    return closest, min_dist, is_direct_path, direct_path, min_hc_path, min_c2_path

def list_distance_scores(graph: nx.MultiDiGraph, team: str, year: int) -> list:
    relevant_coaches = set()
    head_coach = None
    for u, v, k, edge_data in graph.edges(data=True, keys= True):
        edge_years = edge_data.get("years_of_connection")
        edge_team = edge_data.get("team_of_connection")
        if year in edge_years and edge_team == team:
            if edge_data.get("source_position", "") == "Head Coach":
                head_coach = u
                relevant_coaches.add((v, edge_data.get("target_position")))
            elif edge_data.get("target_position", "") == "Head Coach":
                head_coach = v
                relevant_coaches.add((u, edge_data.get("source_position")))
            else:
                relevant_coaches.add((u, edge_data.get("source_position")))
                relevant_coaches.add((v, edge_data.get("target_position")))
    if head_coach == None:
        print(f"{team} in {year} does not have a head coach in data set")
        return None
    # print(relevant_coaches)
    # print(head_coach)
    distance_list = []

    for coach2, coach2_position in relevant_coaches:

        indiv_coach_graph = clean_graph(graph, team, coach2, year)

        distance_list.append({
            "Queried Coach": coach2,
            "Queried Coach Position": coach2_position,
            "Pathing Info": find_lowest_common_ancestor(indiv_coach_graph, head_coach, coach2)
            }) 
    return distance_list

if __name__ == "__main__":
    with open("data/clean_sorted_coach_jobs.csv", "r") as f:
        coach_jobs = pd.read_csv(f)

    # Convert the string list to a int list
    coach_jobs['Seasons at Position'] = coach_jobs['Seasons at Position'].apply(ast.literal_eval)

    for year in range(2020, 2026):
        teams_for_year_df = coach_jobs[coach_jobs['Seasons at Position'].apply(lambda x: year in x)]
        teams_for_year = teams_for_year_df["Team"].unique()

        all_rows = []

        for team in teams_for_year:

            team_dist_list = list_distance_scores(G, team, year)

            row_dict = {}
            if team_dist_list:
                for item in team_dist_list:
                    coach2 = item["Queried Coach"]
                    coach2_pos = item["Queried Coach Position"]
                    lca_path_info = item["Pathing Info"]
                    if lca_path_info[3] is not None:
                        direct_path = lca_path_info[3]
                        most_recent_year = year
                        least_recent_year = max(direct_path[-1][2].get("years_of_connection"))
                        years_between_mentorship = abs(most_recent_year - least_recent_year)

                    elif lca_path_info[5] is not None:
                        direct_path = lca_path_info[5]
                        most_recent_year = year
                        least_recent_year = max(direct_path[-1][2].get("years_of_connection"))
                        years_between_mentorship = abs(most_recent_year - least_recent_year)

                    else:
                        years_between_mentorship = None

                    all_rows.append({
                        "Team": team,
                        "Year": year,                        
                        "Queried Coach": coach2,
                        "Queried Coach Position": coach2_pos,
                        "Shared Mentor": lca_path_info[0],
                        "Combined Distance": lca_path_info[1],
                        "Years Between Mentorship": years_between_mentorship,
                        "Direct Path": lca_path_info[2],
                        # "Queried Coach to HC Pathing": lca_path_info[3],
                        # "HC to Shared Mentor Pathing": lca_path_info[4],
                        # "Queried Coach to Shared Mentor Pathing": lca_path_info[5]
                    })
            if not team_dist_list:
                continue
            
            print(f"{year} {team} completed!")

        team_df = pd.DataFrame(all_rows)
        team_df.index.name = "Queried Coach"

        team_df.to_csv(f"data/LCAs/{year}_distances.csv", index=False)
