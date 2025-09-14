import networkx as nx
from coach_lca_alg import *


test_graph = nx.MultiDiGraph()

test_graph.add_edge("A", "B", 0, team_of_connection= "Test Team", years_of_connection=[2015,2016,2017], mentor_status= "Mentor")
test_graph.add_edge("E", "B", 0, team_of_connection= "Test Team", years_of_connection=[2017], mentor_status= "Mentor")
test_graph.add_edge("B", "C", 0, team_of_connection= "Test Team", years_of_connection=[2023,2024], mentor_status= "Mentor")
test_graph.add_edge("A", "D", 0, team_of_connection= "Test Team", years_of_connection=[2025], mentor_status= "Mentor")

for u, v, k, data in test_graph.edges(keys=True, data=True):
    print(f"{u} to {v}")
    print(data)


closest, min_dist = find_lowest_common_ancestor(test_graph, "C", "D")

print(closest)
print(min_dist)