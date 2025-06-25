from basic_graph_generation import create_nx_graph
import networkx as nx            
import dash_cytoscape as cyto    
import dash                      
from dash import dcc, html
import itertools

import base64
import io
import pandas as pd
from dash.dependencies import Input, Output, State

def nx_to_cytoscape(G):
    elements = []

    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'label': str(node)}})

    for idx, (source, target, data) in enumerate(G.edges(data=True)):
        # Only include edges where visualization_tracker == 1
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

def generate_color(index, total):
    # Generates a color evenly spaced around the color wheel
    hue = int(360 * index / total)
    return f"hsl({hue}, 70%, 50%)"

app = dash.Dash('Test Run')

app.layout = html.Div([
    dcc.ConfirmDialog(
        id='empty-parameter-warning',
        message="Please select an option for all parameters. Use the 'All' option if unsure what to select"
    ),
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
        layout={'name': 'circle'
                },
        stylesheet=[
            {'selector': 'node', 'style': {
                'label': 'data(label)',
                'height': 10,
                'width': 10,
                'font-size': 5
                }},
            {'selector': 'node', 'style': {
                'label': 'data(label)',
                'height': 10,
                'width': 10,
                'font-size': 5
                }},
            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'width': 1
            }}
        ],
        style={'width': '100%', 'height': '600px'}
    ),
    dcc.Dropdown(
        options= [],
        multi= True,
        placeholder= 'Select some teams',
        id='team_select'
    ),
    dcc.Dropdown(
        options= [],
        multi= True,
        placeholder= 'Select some years',
        id='year_select'
    ),
    html.Button("Update Parameters", id='update_button', n_clicks=0),
    html.Div(id='legend-container')
])

@app.callback(
    Output('cytoscape', 'elements'),
    Output('team_select', 'options'),
    Output('year_select', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def generate_graph(contents, filename):
    if contents is None:
        return [], [], []
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try: 
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            team_list = ['All'] + sorted(df['Team'].unique().tolist())
            year_list = ['All'] + sorted(df['Starting Season'].unique().tolist())
            G = create_nx_graph(df)
            return nx_to_cytoscape(G), team_list, year_list 
        else: return [], [], []
    except Exception as e:
        print(e)
        return [], [], []

@app.callback(
    Output('cytoscape', 'stylesheet'),
    Output('empty-parameter-warning', 'displayed'),
    Output('legend-container', 'children'),
    Input('update_button', 'n_clicks'),
    State('team_select', 'value'),
    State('year_select', 'value'),
    State('cytoscape', 'elements'),
    State('team_select', 'options'),
    State('year_select', 'options')
)
def update_graph(n_clicks, team_values, year_values, elements, team_options, year_options):    
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
        return unselected_stylesheet, False, dash.no_update

    color_palette = [
        'blue', 'red', 'green', 'orange', 'purple', 'brown', 'teal', 'magenta', 'gold', 'black'
    ]
    highlight_styles = []

    if not team_values or not year_values:
        return unselected_stylesheet, True, dash.no_update

    team_list =  team_options
    year_list = year_options

    if not isinstance(team_values, list):
        team_values = [team_values]
    if not isinstance(year_values, list):
        year_values = [year_values]

    if "All" in year_values:
        year_values = year_list[1:]
    if "All" in team_values:
        team_values = team_list[1:]

    combinations = list(itertools.product(team_values, year_values))
    total = len(combinations)

    legend_items = []
    for i, team_tuple in enumerate(combinations):
        color = generate_color(i, total)
        highlighted_edges = set()
        highlighted_nodes = set()
        team, year = team_tuple
        
        # Find connected nodes
        for el in elements:
            data = el.get('data', {})
            if data.get('team_of_connection') == team and (year in data.get('years_of_connection')):
                highlighted_edges.add(data.get('id'))
                highlighted_nodes.add(data.get('source'))
                highlighted_nodes.add(data.get('target'))
        # Highlight edges
        for edge_id in highlighted_edges:
            highlight_styles.append({
            'selector': f'[id = "{edge_id}"]',
            'style': {'line-color': color, 'opacity': 1},
        })
        # Highlight nodes
        for node_id in highlighted_nodes:
            highlight_styles.append({
                'selector': f'node[id = "{node_id}"]',
                'style': {f'background-color': color, 'border-width': 1, 'border-color': 'black'}
            })

        legend_items.append(
            html.Div([
                html.Span(style={
                    'display': 'inline-block',
                    'width': '20px',
                    'height': '20px',
                    'backgroundColor': color,
                    'marginRight': '10px',
                    'border': '1px solid #333'
                }),
                f"{team} - {year}"
            ], style={'marginBottom': '5px'})
        )

    legend = html.Div(legend_items, style={'padding': '10px', 'border': '1px solid #ccc', 'display': 'inline-block'})

    return unselected_stylesheet + highlight_styles, False, legend

if __name__ == '__main__':
    app.run(debug=True)