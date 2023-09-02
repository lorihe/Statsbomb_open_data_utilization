import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input,Output
import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np
import requests

from tacticplot import plot

def load_json(url):
    response = requests.get(url)
    return response.json()

url_WC_2023 = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/72/107.json'
json_data_2023 = load_json(url_WC_2023)

stage_dict = {}
for match in json_data_2023:
    stage_name = match['competition_stage']['name']
    match_id = match['match_id']
    
    if stage_name not in stage_dict:
        stage_dict[stage_name] = []
    
    stage_dict[stage_name].append(match_id)

app = Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])

server = app.server

app.layout = html.Div([
    # Header and game dropdown
    html.Div([
        html.H3('WC2023'),
        dcc.Dropdown(
            id='stage-dropdown',
            options=[{'label': k, 'value': k} for k in stage_dict.keys()],
            value = 'Group Stage'
        )
    ], style={'width': '40%', 'display': 'inline-block','margin-top': '40px', 'margin-left': '180px'}),
      
      
    dcc.Dropdown(id='match-dropdown', value = 3893806,
                 style={'width': '50%', 'margin-left': '90px'}),  
    
    html.Hr(style={'width': '1px', 'height': '1000px', 'position': 'absolute','display': 'inline-block',
                   'left': '1440px', 'background-color': 'black','vertical-align': 'top'}),
      
    # Plot home team    
    html.Div([
                
        # Pplotting
        html.Div([

            dcc.Graph(id = 'tactic-plot'),

            html.Div(
                html.P('OPPONENT BASKET', style={'transform': 'rotate(-90deg)', 'white-space': 'nowrap'}),
                style={'position': 'absolute', 'top': '620px', 'left': '50px'}
            ),

            html.Div(
                html.P('OWN BASKET', style={'transform': 'rotate(-90deg)', 'white-space': 'nowrap'}),
                style={'position': 'absolute', 'top': '620px', 'left': '1250px'}
            )
        ]),
                
    ], style={'width': '48%', 'display': 'inline-block', 'margin-left': '10px'}),
    
    html.Hr(), 
    
  ])


@app.callback(
    Output('match-dropdown', 'options'),
    [Input('stage-dropdown', 'value')])
def set_match_options(selected_stage):
    return [{'label': i, 'value': i} for i in stage_dict[selected_stage]]

@app.callback(
    Output('tactic-plot', 'figure'),
    [Input('match-dropdown', 'value')]
)
def update_plot(selected_match):
    match_info = [match for match in json_data_2023 if match['match_id'] == selected_match][0]
    team1 = match_info['home_team']['country']['name']
    team2 = match_info['away_team']['country']['name']
    fig = plot(selected_match, team1, team2)
    return fig
    
    

if __name__ == '__main__':
    app.run_server(debug=True, mode='external', port=1020)