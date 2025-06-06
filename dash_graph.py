from basic_graph_generation import create_nx_graph
import networkx as nx            
import dash_cytoscape as cyto    
import dash                      
from dash import dcc, html

cyto.load_extra_layouts()

def nx_to_cytoscape(G):
    elements = []

    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'label': str(node)}})

    for source, target, data in G.edges(data=True):
        edge_data = {
            'id': f'{source} -> {target}',
            'source': str(source),
            'target': str(target),
            **data
        }
        elements.append({'data': edge_data})
    
    return elements

app = dash.Dash('Test Run')

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a CSV File')
        ]),
        style={
            'width': '98%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    cyto.Cytoscape(
        id='cytoscape',
        elements=[],  # Start empty
        layout={'name': 'fcose',
                'idealEdgeLength': 200},
        stylesheet=[
            {'selector': 'node', 'style': {'label': 'data(label)'}},
            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)'
            }}
        ],
        style={'width': '100%', 'height': '600px'}
    )
])

import base64
import io
import pandas as pd
from dash.dependencies import Input, Output, State

@app.callback(
    Output('cytoscape', 'elements'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)

def update_graph(contents, filename):
    if contents is None:
        return []
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try: 
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            G = create_nx_graph(df)
            return nx_to_cytoscape(G)
        else: return []
    except Exception as e:
        print(e)
        return []

if __name__ == '__main__':
    app.run(debug=True)