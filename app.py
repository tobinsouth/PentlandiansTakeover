import dash
import dash_cytoscape as cyto
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import random


import networkx as nx
import itertools
with open('data.txt', 'r') as f:
    data = [l.rstrip().split(', ') for l in f.readlines()]
   

# App Layout
app = dash.Dash(__name__, external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://raw.githubusercontent.com/plotly/dash-app-stylesheets/master/dash-hello-world.css'])

# Load extra layouts
cyto.load_extra_layouts()

app.layout = html.Div(children=[
    html.Div(className='row', children=[html.H1('Human Dynamics Takes Over IC2S2')]),
    html.Div(className='row', children=[
        html.Div(className='seven columns', children=[
            html.H2('Networks'),
            html.H3('People'),
            html.Div(id='people-graph'),
            html.H3('Papers'),
            html.Figure(id='paper-graph'),
            html.H3('Bipartite'),
            html.Figure(id='bipartite-graph')
        ]),
        html.Div(className='five columns', children=[
            html.Div(className='row', children=[
                html.H3('Options'),
                # Option to remove Sandy
                dcc.Checklist(id='options-checklist', options=[{'label':k, 'value':k} for k in ['Remove Sandy', 'Remove Posters']], value=[]),
            ]),
            html.Div(className='row', children=[
                html.H3('Papers'),
                html.Div(id='paper-list')
            ]),
            html.Div(className='row', children=[
                html.H3('Centralities'),
                dcc.Graph(id='betweenness'),
                dcc.Graph(id='closeness')
            ])
        ])
    ])
])


# Callbacks to plot things
@app.callback(Output('people-graph', 'children'),
              [Input('options-checklist', 'value')])
def create_people_graph(options):
    include_sandy = False if 'Remove Sandy' in options else True
    include_posters = False if 'Remove Posters' in options else True
    people = list(itertools.chain.from_iterable([d[2:] for d in data if ((d[1] != 'Poster') or include_posters)]))
    people_graph_elements = [{'data': {'id': n, 'label': n}} for n in set(people) if include_sandy or n != 'Sandy']
    for paper in data:
        if (paper[1] != 'Poster') or include_posters:
            for i, a1 in enumerate(paper[2:]):
                for a2 in paper[i+2:]:
                    if a1 != a2:
                        if (include_sandy) or ((a1 != 'Sandy') and (a2 != 'Sandy')):
                            people_graph_elements.append({'data': {'source': a1, 'target': a2, 'label': paper[0] + ' ' + paper[1]}})        

    people_graph = cyto.Cytoscape(
        id='cytoscape-people',
        layout={'name': 'dagre'},
        style={'width': '100%', 'height': '400px'},
        elements=people_graph_elements
    )      
    return people_graph      

# Callbacks to plot things
@app.callback(Output('paper-graph', 'children'),
              [Input('options-checklist', 'value')])
def create_paper_graph(options):
    include_sandy = False if 'Remove Sandy' in options else True
    include_posters = False if 'Remove Posters' in options else True
    paper_graph_elements = [{'data': {'id': d[0], 'label': d[0]}} for d in data if ((d[1] != 'Poster') or include_posters)]
    for i, p1 in enumerate(data):
        for p2 in data[i+1:]:
            if include_posters or ((p1[1] != 'Poster') and (p2[1] != 'Poster')):
                paper_graph_elements.append({'data': {'source': p1[0], 'target': p2[0]}})

    paper_graph = cyto.Cytoscape(
        id='cytoscape-papers',
        layout={'name': 'dagre'},
        # style={'width': '100%', 'height': '400px'},
        elements=paper_graph_elements
    )      
    return paper_graph    


def paper_network(include_posters=True):
    G = nx.DiGraph()
    for i, p1 in enumerate(data):
        for p2 in data[i:]:
            if include_posters or ((p1[1] != 'Poster') and (p2[1] != 'Poster')):
                if G.has_edge(p1[0], p2[0]):
                    G[p1[0]][p2[0]]['weight'] += 1
                else:
                    G.add_edge(p1[0], p2[0], weight=1)
    return G


@app.callback(Output('paper-list', 'children'),
              [Input('options-checklist', 'value')])
def list_posters(options):
    include_sandy = False if 'Remove Sandy' in options else True
    include_posters = False if 'Remove Posters' in options else True
    papers = sorted([d for d in data if ((d[1] != 'Poster') or include_posters)])
    random.shuffle(papers)
    return html.Ul([html.Li(", ".join(p)) for p in papers])


def make_people_graph(options):
    include_sandy = False if 'Remove Sandy' in options else True
    include_posters = False if 'Remove Posters' in options else True
    g = nx.Graph()
    for paper in data:
        if (paper[1] != 'Poster') or include_posters:
            for i, a1 in enumerate(paper[2:]):
                for a2 in paper[i+2:]:
                    if a1 != a2:
                        if (include_sandy) or ((a1 != 'Sandy') and (a2 != 'Sandy')):
                            if g.has_edge(a1, a2):
                                g[a1][a2]['weight'] += 1
                            else:
                                g.add_edge(a1, a2, weight=1)

    return g

@app.callback(Output('betweenness', 'figure'),
              [Input('options-checklist', 'value')])
def create_betweenness(options):
    g =  make_people_graph(options)

    betweenness = nx.betweenness_centrality(g)
    betweenness = [(n,float(b)) for n,b in betweenness.items() if float(b) > 0]

    # Bar chart of betweenness centrality
    fig = go.Figure(data=[go.Bar(x=[b[0] for b in betweenness], y=[b[1] for b in betweenness])])
    fig = fig.update_layout(
        yaxis = dict(title = 'Betweenness Centrality'),
        xaxis = {'title' : 'Person'},
    )

    return fig

@app.callback(Output('closeness', 'figure'),
              [Input('options-checklist', 'value')])
def create_closeness(options):
    g =  make_people_graph(options)

    closeness = nx.closeness_centrality(g)
    closeness = [(n,float(b)) for n,b in closeness.items() if float(b) > 0]

    # Bar chart of closeness centrality
    fig = go.Figure(data=[go.Bar(x=[b[0] for b in closeness], y=[b[1] for b in closeness])])
    fig = fig.update_layout(
        yaxis = dict(title = 'Closeness Centrality'),
        xaxis = {'title' : 'Person'},
    )
    return fig




if __name__ == '__main__':
    app.run_server(debug=True)

server = app.server
