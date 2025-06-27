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
import json
from dash import callback_context

cyto.load_extra_layouts

def nx_to_cytoscape(G):
    elements = []
    print(len(G.nodes))
    print(len(G.edges))
    for node in G.nodes:
        elements.append({'data': {'id': str(node), 'label': str(node)}})

    for idx, (source, target, data) in enumerate(G.edges(data=True)):
        # Only include edges where visualization_tracker == 1
        # if data.get('visualization_tracker', 0) == 1:
            edge_data = {
                'id': f'edge-{idx}',
                'description': f'{source} -> {target}',
                'source': str(source),
                'target': str(target),
                **data
            }
            elements.append({'data': edge_data})
    print(elements[2000])

    return elements

def generate_color(index, total):
    # Generates a color evenly spaced around the color wheel
    hue = int(360 * index / total)
    return f"hsl({hue}, 70%, 50%)"

default_stylesheet=[
    {'selector': 'node', 'style': {
        'label': 'data(label)',
        'height': 10,
        'width': 10,
        'font-size': 5,
        'opacity': 1
        }},

    {'selector': 'edge', 'style': {
        'line-color': '#aaa',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'width': 1,
        'opacity': .1
    }}
]

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
    html.Button("Load graph from JSON updated 6/26/25", id="JSON-direct-load-button", n_clicks=0),
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
                'font-size': 5,
                'opacity': 1
                }},

            {'selector': 'edge', 'style': {
                'line-color': '#aaa',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'width': 1,
                'opacity': .1
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
    html.Button("Clear Parameters", id='clear_params', n_clicks=0),
    html.Div(id='legend-container'),
    html.Div(className='row', children=[
        html.Div([
            dcc.Markdown("""
                **Hover Data**
                
                Mouse over values in the graph
            """),
            html.Pre(id='coach-name-hover', style= {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }),
            html.Pre(id='coach-teams-hover', style= {
                'border': 'thin lightgrey solid',
                'overflowX': 'scroll'
            }),
        ], className='three columns')
    ])
])

@app.callback(
    Output('cytoscape', 'elements'),
    Output('team_select', 'options'),
    Output('year_select', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    Input('JSON-direct-load-button', 'n_clicks'),
)
def generate_graph(contents, filename, json_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return [], [], []
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'upload-data' and contents is not None:
        # CSV logic
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                team_list = ['All'] + sorted(df['Team'].unique().tolist(), reverse=True)
                years_list = set()
                for _, row in df.iterrows():
                    years_worked = row['Seasons at Position']
                    if isinstance(years_worked, list):
                        years_list.update(years_worked)
                    elif years_worked:
                        years_list.add(years_worked)
                years_list = ['All'] + sorted(years_list, reverse=True)
                G = create_nx_graph(df)
                return nx_to_cytoscape(G), team_list, years_list
            else:
                return [], [], []
        except Exception as e:
            print(e)
            return [], [], []
    elif trigger_id == 'JSON-direct-load-button':
        # JSON logic
        with open('visualization_elements_dump.json') as f:
            elements = json.load(f)
        teams = set()
        years = set()
        for el in elements:
            data = el.get('data', {})
            team = data.get('team_of_connection')
            years_of_connection = data.get('years_of_connection')
            if team:
                teams.add(team)
            if isinstance(years_of_connection, list):
                years.update(years_of_connection)
            elif years_of_connection:
                years.add(years_of_connection)
        teams_list = ['All'] + sorted(teams, reverse=False)
        years_list = ['All'] + sorted(years, reverse=True)
        return elements, teams_list, years_list
    else:
        return [], [], []


@app.callback(
    Output('cytoscape', 'layout'),
    Output('cytoscape', 'stylesheet'),
    Output('empty-parameter-warning', 'displayed'),
    Output('legend-container', 'children'),
    Input('update_button', 'n_clicks'),
    Input('clear_params', 'n_clicks'),
    State('team_select', 'value'),
    State('year_select', 'value'),
    State('cytoscape', 'elements'),
    State('cytoscape', 'stylesheet'),
    State('team_select', 'options'),
    State('year_select', 'options')
)
def update_graph(update_n_clicks, clear_n_clicks, team_values, year_values, elements, intro_stylesheet, team_options, year_options):    
    unselected_stylesheet = [
        {'selector': 'node', 'style': {
            'label': 'data(label)',
            'height': 10,
            'width': 10,
            'font-size': 5,
            'opacity': 0
        }},
        {'selector': 'edge', 'style': {
            'line-color': '#aaa',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'width': 1,
            'opacity': 0
        }}
    ]
    ctx = callback_context
    if not callback_context:
        return dash.no_update, dash.no_update, False, dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "clear_params":
        layout = {'name': 'circle'}
        return layout, default_stylesheet, False, None
    
    elif trigger_id == "update_button":
        highlight_styles = []

        if not team_values and not year_values:
            layout = {'name': 'circle'}
            return layout, default_stylesheet, False, None

        if not team_values or not year_values:
            return dash.no_update, dash.no_update, True, dash.no_update

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
                    'style': {f'background-color': color, 'border-width': 1, 'border-color': 'black', 'opacity': 1}
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
        layout = {'name': 'random'}
        
        return layout, unselected_stylesheet + highlight_styles, False, legend
    
    else:
        return dash.no_update, dash.no_update, False, None

@app.callback(
    Output('coach-name-hover', 'children'),
    Output('coach-teams-hover', 'children'),
    Input('cytoscape', 'mouseoverNodeData'),
    Input('cytoscape', 'elements')
)
def display_hover_data(hoverData, elements):
    if hoverData and 'label' in hoverData:
        years_coached = []
        coached_sentences = []
        for el in elements:
            data = el.get('data', {})
            # Check if the hovered coach is involved in this edge
            if data.get('source', "") == hoverData['label'] or data.get('target', "") == hoverData['label']:
                # Determine role
                is_source = data.get('source', "") == hoverData['label']
                is_target = data.get('target', "") == hoverData['label']
                team = data.get('team_of_connection')
                for year in data.get('years_of_connection', []):
                    if year not in years_coached:
                        years_coached.append(year)
                        if is_source:
                            coached_sentences.append(f"{hoverData['label']} coached for {team} as the {data['source_position']} in {year}")
                        if is_target:
                            coached_sentences.append(f"{hoverData['label']} coached for {team} as the {data['target_position']} in {year}")
        coached_sentences.sort(key=lambda s: s.split()[-1], reverse=True)
        return f"You are hovering over {hoverData['label']}", '\n'.join(coached_sentences)
    else:
        return "Hover over a node", "The teams a coach has worked for will be shown here"

if __name__ == '__main__':
    app.run(debug=True)