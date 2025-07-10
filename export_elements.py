import json
from dash_graph import nx_to_cytoscape
from basic_graph_generation import create_nx_graph
import pandas as pd
import networkx as nx

# Load your data (adjust the path and filename as needed)
df = pd.read_csv(r"data\clean_sorted_coach_jobs.csv")
G = create_nx_graph(df)

def export_elements(G, full_elements):
    '''
    Exports a networkx graph's data as  JSON file for faster loading into a Dash graph.

    full_elements == True will generate a JSON will edges (coach1, coach2) and (coach2, coach1), edges are not parallel for graph exploration purposes \n
    full_elements == False will generate only the edge (coach1, coach2) for each connection. The result is a Dash graph that communicates the same
    information while only needing to process half the edges.

    Use Guide: full_elements == False should be used if you only plan on using the Dash graph, full_elements == True should be used if doing graph exploration
    '''
    elements = []

    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'coach_name': str(node)}})

    for idx, (source, target, data) in enumerate(G.edges(data=True)):
        if full_elements == True:
            edge_data = {
                'id': f'edge-{idx}',
                'description': f'{source} -> {target}',
                'source': str(source),
                'target': str(target),
                **data
            }
            elements.append({'data': edge_data})    
        
        
        # Only include edges where visualization_tracker == 1   
        if full_elements == False:    
            if data.get('visualization_tracker', 0) == 1:
                edge_data = {
                    'id': f'edge-{idx}',
                    'description': f'{source} -> {target}',
                    'source': str(source),
                    'target': str(target),
                    **data
                }
                elements.append({'data': edge_data})

    return elements



elements = export_elements(G, full_elements=True)

with open('full_elements_dump.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(elements, ensure_ascii=False, indent=2))