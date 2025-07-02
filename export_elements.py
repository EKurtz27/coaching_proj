import json
from dash_graph import nx_to_cytoscape
from basic_graph_generation import create_nx_graph
import pandas as pd
import networkx as nx

# Load your data (adjust the path and filename as needed)
df = pd.read_csv(r"data\clean_sorted_coach_jobs.csv")
G = create_nx_graph(df)

elements = nx_to_cytoscape(G)

with open('full_elements_dump.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(elements, ensure_ascii=False, indent=2))