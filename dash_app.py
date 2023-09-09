import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input,Output
import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np
import requests

from tacticplot import plot, get_events, formation

def load_json(url):
    response = requests.get(url)
    return response.json()

url_WC_2023 = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/72/107.json'
json_data_2023 = load_json(url_WC_2023)

stage_dict = {}
for match in json_data_2023:
    stage_name = match['competition_stage']['name']
    match_id = str(match['match_id'])
    
    if stage_name not in stage_dict:
        stage_dict[stage_name] = []
    
    stage_dict[stage_name].append(match_id)

stage_dict['Group Stage'] = sorted(stage_dict['Group Stage'])

match_dict = {str(match["match_id"]): 
    f"{match['home_team']['country']['name']} vs. {match['away_team']['country']['name']}"
    for match in json_data_2023}

match_dict = {key: value.replace('Korea\xa0(South)', 'South Korea') for key, value in match_dict.items()}
match_dict = {key: value.replace('United States of America', 'USA') for key, value in match_dict.items()}

match_list = [str(match['match_id']) for match in json_data_2023]

team_dict = {match['match_id']: 
    (match['home_team']['home_team_name'], match['away_team']['away_team_name'])
    for match in json_data_2023}




app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR],
          meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.title = "World Cup 2023 Data Visualization"

#server = app.server
app.config.suppress_callback_exceptions = True


def description_card():
    """

    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description",
        children=[
            html.H5("Statsbomb Open Data Visualization",
                    style = {"width": "100%", "font-weight": "bold", 'color': 'dark-grey'}),
            html.Img(src=app.get_asset_url("statsbomb.png"),
                     style={"width": "60%", "height": "auto", "margin-bottom": "20px",
                            "margin-left": "18px"}),

            html.Div(
                id="intro",
                children="Statsbomb has shared well-structured and specified game data of the "
                         "Women's World Cup 2023. This project visualizes "
                         "part of it with an emphasis on team tactics.",
                style={"font-size": "14px"}

            ),
            html.Img(src=app.get_asset_url("wc2023.jpg"),
                     style={"width": "100%", "height": "auto", "margin-top": "20px",
                            "margin-bottom": "20px"}),
        ],
    )

def game_select_card():

    return html.Div([
        dbc.Accordion(
          [
            dbc.AccordionItem(
                className= "accordion-title",
                children =
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['Group Stage']
                ],
                title="Group Stage"
            ),
            dbc.AccordionItem(
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['Round of 16']
                ],
                title="Round of 16"
            ),
            dbc.AccordionItem(
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['Quarter-finals']
                ],
                title="Quarter-finals"
            ),
            dbc.AccordionItem(
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['Semi-finals']
                ],
                title="Semi-finals"
            ),
            dbc.AccordionItem(
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['3rd Place Final']
                ],
                title="3rd Place Final"
            ),
            dbc.AccordionItem(
                [
                    html.Button(match_dict[match], id=match, style={'width': '46%', 'font-size': '13px',
                                                                    "margin-left": "-13px", "margin-right": "15px"},
                               className="border-0 bg-light font-weight-light my-0")
                    for match in stage_dict['Final']
                ],
                title="Final"
            ),
          ], flush = True,
        ),

        html.Div(id="output-div", style={'display': 'none'}),

    ])

app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            dbc.Col(
                html.Div(id="banner", className="banner", children=[html.H6("Lori")]),
                width={'size':2, 'offset':1}
            )
        ),
        dbc.Row([
            dbc.Col(
                html.Div(
                    id="left-column",
                    children= [
                        html.Div(description_card(), style={"width": "90%"}),
                        html.Div(game_select_card(), style={"width": "90%"})
                    ]
                ), width={'size': 3, 'offset': 1}
            ),
            dbc.Col(
                html.Div(
                    id="mid-column",
                    children=[
                        html.H5('Match Overview',
                                style = {'margin-top': '100px', 'margin-left': '50px', 'margin-right': '30px'}),

                    ]
                ), width='auto', style={"background-color":"RGB(247,247,247)"}
            ),
            dbc.Col(
                html.Div(
                    id="right-column",
                    children=[
                        dbc.Spinner(children = [dcc.Graph(id="team1-plot")],
                                   size="lg", color="primary"),
                        dbc.Spinner(children = [dcc.Graph(id="team2-plot",
                                                          style= {"margin-top": "-80px"})],
                                   size="lg", color="primary"),
                        html.Div(
                            dcc.Graph(id = "team1-formation"),
                            style= {
                                "position": "absolute",
                                "top": "420px",
                                "left": "890px",
                                "z-index": "2",
                            }

                        )
                    ], style={"background-color":"RGB(247,247,247)", "position": "relative"}
                ), width = 6
            )
        ], className="h-100 g-0")
    ])

input_matches = [Input(match, "n_clicks") for match in match_list]
@app.callback(
    Output("output-div", "children"),
    input_matches
)
def get_match(*n_clicks_values):
    clicked_match_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    return clicked_match_id


@app.callback(
    Output('team1-plot', 'figure'),
    Output('team2-plot', 'figure'),
    Output('team1-formation', 'figure'),
    [Input("output-div", 'children')]
)
def update_plot(selected_match):
    if not selected_match:
        match_id = 3906390
    else:
        match_id = int(selected_match)
    team1 = team_dict[match_id][0]
    team2 = team_dict[match_id][1]

    url = f'https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json'
    match_events = load_json(url)

    team1_name = ' '.join(team1.split()[:-1])
    team2_name = ' '.join(team2.split()[:-1])

    team1_events = [event for event in match_events if event['team']['name'] == team1]
    team1_tuples = get_events(team1_events)

    team2_events = [event for event in match_events if event['team']['name'] == team2]
    team2_tuples = get_events(team2_events)

    fig1 = plot(team1_name, team1_tuples, team2_tuples)
    fig2 = plot(team2_name, team2_tuples, team1_tuples)

    fig3 = formation(team1_tuples)

    return fig1, fig2, fig3
    

if __name__ == '__main__':
    app.run_server(debug=True, port=1000)