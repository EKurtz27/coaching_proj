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
    
    print(elements[2000])

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
        layout={'name': 'circle'
                },
        stylesheet=[
            {'selector': 'node', 'style': {
                'label': 'data(label)',
                'height': 10,
                'width': 10,
                'font-size': 5
                }},
            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'width': 1
            }}
        ],
        style={'width': '100%', 'height': '600px'}
    ),
    dcc.Dropdown(
        options=['Louisville', 'Alabama'],
        multi= True,
        placeholder= 'Select some teams',
        id='team_select'
    ),
    html.Button("Update Parameters", id='update_button', n_clicks=0)
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


@app.callback(
    Output('cytoscape', 'stylesheet'),
    Input('update_button', 'n_clicks'),
    State('team_select', 'value')
)
def update_graph(n_clicks, value):
    unselected_stylesheet = [
        {'selector': 'node', 'style': {
            'label': 'data(label)',
            'height': 10,
            'width': 10,
            'font-size': 5
        }},
        {'selector': 'edge', 'style': {
            'line-color': '#aaa',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#aaa',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'width': 1,
            'opacity': .1
        }}
    ]
    if n_clicks == 0:
        return unselected_stylesheet
    # Defined color palette (expand as needed)
    color_palette = [
        'blue', 'red', 'green', 'orange', 'purple', 'brown', 'teal', 'magenta', 'gold', 'black'
    ]
    if value:
        if isinstance(value, list):
            highlight_styles = []
            for i, team in enumerate(value):
                color = color_palette[i % len(color_palette)]
                highlight_styles.append({
                    'selector': f'[team_of_connection = "{team}"]',
                    'style': {'line-color': color,
                              'opacity': 1},
                })
        else:
            highlight_styles = [{
                'selector': f'[team_of_connection = "{value}"]',
                'style': {'line-color': color_palette[0],
                          'opacity': 1},
            }]
        return unselected_stylesheet + highlight_styles
    return unselected_stylesheet

if __name__ == '__main__':
    app.run(debug=True)