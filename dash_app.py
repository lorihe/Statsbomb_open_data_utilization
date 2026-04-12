from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import os
from typing import OrderedDict as OrderedDictType, Tuple

import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from data_loader import get_match_events, load_json_from_url

from tacticplot import plot, plot2, get_events, formation, formation2
from positionplot import (build_role_buckets, plot_contour, plot_ballreceipt, plot_defence,
                          plot_passlength, plot_passangle, plot_shot, plot_carry)

# Load the URL of match data for World Cup 2023 from Statsbomb
url_WC_2023 = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/72/107.json'
json_data_2023 = load_json_from_url(url_WC_2023)

# Sort stage group for user to select match
stage_dict = {}
for match in json_data_2023:
    stage_name = match['competition_stage']['name']
    match_id = str(match['match_id'])
    
    if stage_name not in stage_dict:
        stage_dict[stage_name] = []
    stage_dict[stage_name].append(match_id)

stage_dict['Group Stage'] = sorted(stage_dict['Group Stage'])

# Pair match id and match name for user to select match
match_dict = {str(match["match_id"]): 
    f"{match['home_team']['country']['name']} vs. {match['away_team']['country']['name']}"
    for match in json_data_2023}

match_dict = {key: value.replace('Korea\xa0(South)', 'South Korea') for key, value in match_dict.items()}
match_dict = {key: value.replace('United States of America', 'USA') for key, value in match_dict.items()}

# Get a dictionary with match ids as keys and a tuple of both teams in that match as value
team_dict = {match['match_id']: 
    (match['home_team']['home_team_name'], match['away_team']['away_team_name'])
    for match in json_data_2023}

# Memoize position-matrix DOM per (match, tab); building ~30 Plotly figures is the main cost.
_POSITION_MATRIX_CACHE_MAX = 24
_position_matrix_cache: OrderedDictType[Tuple[int, str], html.Div] = OrderedDict()

# Dropdowns for stages with many matches; 3rd Place Final and Final each have one game (buttons).
_STAGE_MATCH_DROPDOWNS = [
    ("Group Stage", "dd-match-group"),
    ("Round of 16", "dd-match-r16"),
    ("Quarter-finals", "dd-match-qf"),
    ("Semi-finals", "dd-match-sf"),
]
_SINGLE_MATCH_3RD = int(stage_dict["3rd Place Final"][0])
_SINGLE_MATCH_FINAL = int(stage_dict["Final"][0])
_BTN_STYLE = {"width": "96%", "font-size": "13px", "margin-left": "-8px", "text-align": "left"}

# Build the app
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN],
          meta_tags=[{"name": "viewport", "content": "width=device-width,"
                      "initial-scale=1, maximum-scale=1"}])

app.title = "World Cup 2023 Data Visualization"

server = app.server
app.config.suppress_callback_exceptions = True

def description_card():
    '''
    :return: An HTML Div element introducing the app.
    :rtype: dash_html_components.Div
    '''
    return html.Div(
        id="description",
        children=[
            html.H5("Statsbomb Open Data Visualization", className="text-dark",
                    style = {"font-size": "24px", "font-weight": "bold", "margin-left": "18px"}),
            html.Img(src=app.get_asset_url("statsbomb.png"),
                     style={"width": "60%", "height": "auto", "margin-bottom": "20px",
                            "margin-left": "18px"}),

            html.Div(
                id="intro",
                children="Great appreciation towards Statsbomb for sharing valuable data of the "
                         "Women's World Cup 2023, as part of their commitment to support women's soccer. "
                         "This project visualizes the data with an emphasis on team tactics.",
                style={"font-size": "14px"}

            ),
            html.Img(src=app.get_asset_url("wc2023.jpg"),
                     style={"width": "100%", "height": "auto", "margin-top": "20px",
                            "margin-bottom": "20px"}),
        ],
    )

def game_select_card():
    '''
    :return: An HTML Div element providing accordion menu for match selection.
    :rtype: dash_html_components.Div
    '''
    accordion_items = []
    for stage_title, dd_id in _STAGE_MATCH_DROPDOWNS:
        opts = [
            {"label": match_dict[mid], "value": mid}
            for mid in stage_dict[stage_title]
        ]
        accordion_items.append(
            dbc.AccordionItem(
                dcc.Dropdown(
                    id=dd_id,
                    options=opts,
                    placeholder="Select match…",
                    clearable=False,
                    style={"font-size": "13px", "margin-left": "-8px", "max-width": "100%"},
                ),
                title=stage_title,
                className="accordion-title",
            )
        )
    mid_3rd = str(_SINGLE_MATCH_3RD)
    mid_fin = str(_SINGLE_MATCH_FINAL)
    accordion_items.append(
        dbc.AccordionItem(
            html.Button(
                match_dict[mid_3rd],
                id="btn-match-3rd",
                n_clicks=0,
                style=_BTN_STYLE,
                className="border-0 bg-light font-weight-light my-0",
            ),
            title="3rd Place Final",
            className="accordion-title",
        )
    )
    accordion_items.append(
        dbc.AccordionItem(
            html.Button(
                match_dict[mid_fin],
                id="btn-match-final",
                n_clicks=0,
                style=_BTN_STYLE,
                className="border-0 bg-light font-weight-light my-0",
            ),
            title="Final",
            className="accordion-title",
        )
    )
    return html.Div([
        dbc.Accordion(accordion_items, flush=True),
        # Default match id so dependent callbacks run on load without a click.
        html.Div(id="output-div", style={"display": "none"}, children=3906390),
    ])

_GRAPH_CFG = {'displayModeBar': False}
_COL = {'size': 12}

# Order must match layout below.
_POSITION_MATRIX_TASKS = [
    ('contour', 'centerback'),
    ('defence', 'centerback', 0),
    ('defence', 'centerback', 1),
    ('ballreceipt', 'centerback', 0),
    ('ballreceipt', 'centerback', 1),
    ('passlength', 'centerback'),
    ('contour', 'fullback'),
    ('defence', 'fullback', 0),
    ('defence', 'fullback', 1),
    ('ballreceipt', 'fullback', 0),
    ('ballreceipt', 'fullback', 1),
    ('passangle', 'fullback'),
    ('contour', 'midfielder'),
    ('defence', 'midfielder', 0),
    ('defence', 'midfielder', 1),
    ('ballreceipt', 'midfielder', 0),
    ('carry', 'midfielder'),
    ('shot', 'midfielder', 0),
    ('contour', 'winger'),
    ('defence', 'winger', 0),
    ('ballreceipt', 'winger', 0),
    ('passangle', 'winger'),
    ('carry', 'winger'),
    ('shot', 'winger', 0),
    ('contour', 'striker'),
    ('ballreceipt', 'striker', 0),
    ('ballreceipt', 'striker', 1),
    ('carry', 'striker'),
    ('shot', 'striker', 1),
    ('shot', 'striker', 0),
]

_PM_WORKERS = min(8, max(4, (os.cpu_count() or 4) * 2))


def _build_pm_figure(task, by_loc, by_pos):
    kind = task[0]
    pos = task[1]
    if kind == 'contour':
        return plot_contour(None, pos, role_located=by_loc[pos])
    if kind == 'defence':
        return plot_defence(None, pos, task[2], role_located=by_loc[pos])
    if kind == 'ballreceipt':
        return plot_ballreceipt(None, pos, task[2], role_located=by_loc[pos])
    if kind == 'passlength':
        return plot_passlength(None, pos, role_positioned=by_pos[pos])
    if kind == 'passangle':
        return plot_passangle(None, pos, role_positioned=by_pos[pos])
    if kind == 'carry':
        return plot_carry(None, pos, role_positioned=by_pos[pos])
    if kind == 'shot':
        return plot_shot(None, pos, task[2], role_located=by_loc[pos])
    raise ValueError(task)


def position_matrix(events):
    by_loc, by_pos = build_role_buckets(events)
    with ThreadPoolExecutor(max_workers=_PM_WORKERS) as pool:
        figures = list(pool.map(
            lambda t: _build_pm_figure(t, by_loc, by_pos),
            _POSITION_MATRIX_TASKS,
        ))
    i = 0

    def next_fig():
        nonlocal i
        f = figures[i]
        i += 1
        return f

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
        ], style={'margin-top': '20px'}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
        ], style={'margin-top': '20px'}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
        ], style={'margin-top': '20px'}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
        ], style={'margin-top': '20px'}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
            dbc.Col(dcc.Graph(figure=next_fig(), config=_GRAPH_CFG), xs=_COL, sm=_COL, md=_COL, lg=_COL, xl={'size': 2}),
        ], style={'margin-top': '20px'}),
    ], style={'margin-bottom': '40px'})

# App layout
app.layout = dbc.Container(
    fluid=True,
    children=[
        # First row is the banner
        dbc.Row(
            html.Div([
                html.Div(id="banner1", className="banner",
                         children=[
                             html.Img(src=app.get_asset_url("github.JPG"),
                                      style={"height": "24px", "margin-top": "3px", 'margin-left': '73px'})
                         ]),
                html.Div(id="banner2", className="banner",
                         children=[
                             dbc.NavLink("by Lori He",
                                         href="https://github.com/lorihe/Statsbomb_open_data_utilization",
                                     style={'margin-left': '105px', 'margin-top': '-25px', 'color': 'honeydew'})
                         ]),
            ]),
            style={"height": "30px", "background-color": "black", 'margin-bottom': '10px',
                   "z-index": "2",},
        ),

        # Second row is content
        dbc.Row([
            # First column is app description and match selection menu
            dbc.Col(
                html.Div(
                    children= [
                        html.Div(description_card(), style={"width": "90%"}),
                        html.Div(game_select_card(), style={"width": "90%"})
                    ], style = {'margin-left': '20px', 'margin-bottom': '20px'}
                ), xs={'size': 12}, sm={'size': 12}, md={'size': 12},
                   lg={'size': 3}, xl={'size': 3},
            ),

            # Second column shows match overview information
            dbc.Col(
                html.Div(
                    id = 'column',
                    children=[
                        html.H6('a',
                                style={'margin-left': '-20px',
                                       'color': 'RGB(180,238,180)', 'backgroundColor': 'RGB(180,238,180)'}),
                        html.H5('Match Overview', className="text-dark",
                                style={'margin-top': '100px'}),
                        html.Div([
                            html.P('Match Date:',
                                   style={'margin-top': '30px', 'font-size': '17px', 'font-weight': 'bold'}),
                            html.P(id = 'time',
                                   style={'margin-top': '-10px', 'color':'forestgreen'}),
                            html.P('Match Result:',
                                   style={'margin-top': '20px', 'font-size': '17px', 'font-weight': 'bold'}),
                            html.P('(Regular and extra time)',
                                   style={'margin-top': '-20px', 'font-size': '16px'}),
                            html.P(id = 'team1_string',
                                   style={'margin-top': '-10px', 'color':'forestgreen'}),
                            html.P(id = 'team2_string',
                                   style={'margin-top': '-10px', 'color':'forestgreen'}),
                            html.P('Managers:',
                                   style={'margin-top': '20px', 'font-size': '17px', 'font-weight': 'bold'}),
                            html.P(id='team1_manager_string',
                                   style={'margin-top': '-10px'}),
                            html.P(id='team1_manager',
                                   style={'margin-top': '-10px', 'color': 'forestgreen'}),
                            html.P(id='team2_manager_string',
                                   style={'margin-top': '-10px'}),
                            html.P(id='team2_manager',
                                   style={'margin-top': '-10px', 'color': 'forestgreen'}),

                            ]
                        )], style = {'margin-left': '20px', 'margin-right': '20px'}
                ),
                xs=12, sm=12, md=12, lg=1, xl = 1,
                style={"background-color":"RGB(250,248,247)", 'margin-top': '-10px',
                       'margin-left': '-10px', 'height': '1210px'},
            ),

            # Third column shows the plots
            dbc.Col(
                html.Div(
                    children=[
                        dbc.Spinner(children = [
                                        dcc.Graph(id="team1-plot",
                                          config={'displayModeBar': False},
                                          style= {"margin-top": "-40px", "margin-left": "30px"}),
                                        dcc.Graph(id = "team1-formation",
                                                  config = {'displayModeBar': False},
                                        style= {
                                            "width": "180px", "height" : "270px",
                                            "position": "absolute",
                                            "top": "335px",
                                            "left": "945px",
                                            "z-index": "2",
                                        })
                                   ],
                                    size="lg", color="lightgreen", delay_show=0),

                        dbc.Spinner(children = [
                                    dcc.Graph(id="team2-plot",
                                      config={'displayModeBar': False},
                                      style= {"margin-top": "-110px", "margin-left": "30px",
                                              'margin-bottom':'-200px'}),
                                    dcc.Graph(id="team2-formation",
                                      config={'displayModeBar': False},
                                      style={
                                          "width": "180px", "height": "270px",
                                          "position": "absolute",
                                          "top": "900px",
                                          "left": "945px",
                                          "z-index": "2",
                                      })
                                    ],
                                    size="lg", color="lightgreen", delay_show=0),

                    ]
                ), xs=12, sm=12, md=12, lg=6, xl=6,
                   style={"background-color": "RGB(250,248,247)", "position": "relative",
                       'height': '1210px', 'margin-top': '-10px', "overflow-x": "auto"}
            ),

            # Forth columns shows the notes
            dbc.Col(
                html.Div(
                    children=[
                        html.H6('a',
                                style={'color': 'RGB(180,238,180)', 'backgroundColor': 'RGB(180,238,180)'}),
                        html.P('Tactic Plot Notes',
                                style={'margin-top': '10px', 'text-decoration': 'underline'}),
                        html.Div([
                            html.P('Plot direction:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P("The upper plot attacks from left to right, the lower attacks right to left.",
                                   style={ 'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Opponent long pass:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P("Opponent players successfully pass and receive the ball over 40 yards."
                                   " Larger circle indicates receiver location, smaller circle indicates sender location.",
                                   style={'font-size': '14px', 'margin-top': '-15px', }),
                            html.P('Shots (w/ and w/o goal):',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P("Larger dots indicate location of shots, smaller dots and line indicate recent "
                                   "ball trajectory before the shot.",
                                   style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Defense (success and no success):',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P("Indicates active defense actions, which were classified as 'clearance', 'duel'"
                                   " or 'interception' in Statsbomb.",
                                   style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Formation:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P("Only tactical shifts which resulted with formation change were plotted. Click legends to "
                                   "turn layer on or off. Double-click turns on all layers. Double-click again isolates the selected layer.",
                                   style={'font-size': '14px', 'margin-top': '-15px'}),
                        ]),
                        html.P('Position Matrix Notes (scroll down to view plots)',
                               style={'margin-top': '40px', 'text-decoration': 'underline'}),
                        html.Div([
                            html.P('Competition:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P(
                                "Grey area in plots shows distribution of selected action executed by selected position"
                                " across the competition in World Cup 2023.",
                                style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Plot direction:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P(
                                "All heatmaps have the attacking direction left to right",
                                style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Depth & Width:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P(
                                "Depth shows the action coordinate on X axis, x = 0 as the start line, x = 120 as the end line."
                                " Width shows the action coordinate on Y axis, y = 0 as the side line on goalie's left hand side, y = 80 as "
                                "the side line on goalie's right hand side",
                                style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P('Passing Angle:',
                                   style={'margin-top': '10px', 'font-size': '14px', 'font-weight': 'bold'}),
                            html.P(
                                "Angle range is [-π, π], positive values between 0 and π indicating an angle clockwise, "
                                "and negative values between 0 and -π indicating an angle anti-clockwise.",
                                style={'font-size': '14px', 'margin-top': '-15px'}),
                            html.P("| The usage of this data is for non-profit educational purpose only. |",
                                   style={'font-size': '13px', 'margin-top': '48px',
                                          'margin-right': "5px"}),
                        ]),
                    ], style = {'height': '100%',
                                'margin-left':'6%','margin-right':'10%',"overflow-y": "auto"}
                ),
                xs=12, sm=12, md=12, lg=2, xl=2,
                style={'margin-top': '-10px', 'margin-bottom': '10px', 'height': '1200px'},
            )
        ], className="h-100 gx-0 mx-0 px-0"),

        dbc.Row([
            dbc.Col(
                html.Div(
                    dbc.Spinner(
                        children = [
                        dbc.Tabs(id="tabs-output", active_tab="tab-1"),
                        html.Div(id="tabs-content"),
                        html.Div(id="team1_position_string", style={"display": "none"}),
                        html.Div(id="team2_position_string", style={"display": "none"}),
                ], size="lg", color="lightgreen", delay_show=0)
              )
            ),
        ],
        className="h-100 g-0 m-0"),


    ])

_MATCH_SELECT_INPUTS = (
    [Input(dd_id, "value") for _, dd_id in _STAGE_MATCH_DROPDOWNS]
    + [Input("btn-match-3rd", "n_clicks"), Input("btn-match-final", "n_clicks")]
)


@app.callback(
    Output("output-div", "children"),
    _MATCH_SELECT_INPUTS,
    prevent_initial_call=True,
)
def get_match_from_select(v_group, v_r16, v_qf, v_sf, n_clicks_3rd, n_clicks_final):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    pid = ctx.triggered[0]["prop_id"].split(".")[0]
    if pid == "btn-match-3rd":
        return _SINGLE_MATCH_3RD
    if pid == "btn-match-final":
        return _SINGLE_MATCH_FINAL
    val_by_id = {
        "dd-match-group": v_group,
        "dd-match-r16": v_r16,
        "dd-match-qf": v_qf,
        "dd-match-sf": v_sf,
    }
    raw = val_by_id.get(pid)
    if raw is None:
        return dash.no_update
    return int(raw)

# Callback 2: Input - match id from callback 1. Output - a bunch of strings displayed in match overview.
@app.callback(
    Output('time', 'children'),
    Output('team1_string', 'children'),
    Output('team2_string', 'children'),
    Output('team1_manager_string', 'children'),
    Output('team2_manager_string', 'children'),
    Output('team1_manager', 'children'),
    Output('team2_manager', 'children'),
    Output('team1_position_string', 'children'),
    Output('team2_position_string', 'children'),
    [Input("output-div", 'children')]
)
def get_info(selected_match):
    '''
    :param selected_match: match id from callback 1
    :return: a bunch of strings
    '''
    match_info = next(m for m in json_data_2023 if m["match_id"] == selected_match)
    time = match_info['match_date']
    team1_score = match_info['home_score']
    team2_score = match_info['away_score']
    team1_manager = match_info['home_team']['managers'][0]['name']
    team2_manager = match_info['away_team']['managers'][0]['name']

    team1 = team_dict[selected_match][0]
    team2 = team_dict[selected_match][1]

    team1_name = ' '.join(team1.split()[:-1])
    team2_name = ' '.join(team2.split()[:-1])

    team1_string = f"{team1_name} score: {team1_score}"
    team2_string = f"{team2_name} score: {team2_score}"

    team1_manager_string = f"{team1_name} manager:"
    team2_manager_string = f"{team2_name} manager:"

    team1_position_string = f"{team1_name} Position Metrics"
    team2_position_string = f"{team2_name} Position Metrics"

    return (time, team1_string, team2_string, team1_manager_string, team2_manager_string,
            team1_manager, team2_manager, team1_position_string, team2_position_string)

# Callback 3: Input - match id from callback 1. Output - tactic plot and formation plot for both teams
@app.callback(
    Output('team1-plot', 'figure'),
    Output('team2-plot', 'figure'),
    Output('team1-formation', 'figure'),
    Output('team2-formation', 'figure'),
    [Input("output-div", 'children')]
)
def update_plot(selected_match):
    '''
    :param selected_match: match id from callback 1
    :return: A tuple containing four plot figures.
    '''
    match_id = int(selected_match)
    team1 = team_dict[match_id][0]
    team2 = team_dict[match_id][1]

    team1_name = ' '.join(team1.split()[:-1])
    team2_name = ' '.join(team2.split()[:-1])

    match_events = get_match_events(match_id)

    # Get tuples of team actions using imported local module
    team1_events = [event for event in match_events if event['team']['name'] == team1]
    team1_tuples = get_events(team1_events)

    team2_events = [event for event in match_events if event['team']['name'] == team2]
    team2_tuples = get_events(team2_events)

    with ThreadPoolExecutor(max_workers=4) as pool:
        f1 = pool.submit(plot, team1_name, team1_tuples, team2_tuples)
        f2 = pool.submit(plot2, team2_name, team2_tuples, team1_tuples)
        f3 = pool.submit(formation, team1_name, team1_tuples)
        f4 = pool.submit(formation2, team2_name, team2_tuples)
        fig1, fig2, fig3, fig4 = f1.result(), f2.result(), f3.result(), f4.result()

    return fig1, fig2, fig3, fig4
    
@app.callback(
    Output("tabs-output", "children"),
    [Input("team1_position_string", "children"),
    Input("team2_position_string", "children")]
)
def update_tab_labels(team1_position_string, team2_position_string):
    tabs = [
        dbc.Tab(label=team1_position_string, tab_id="tab-1"),
        dbc.Tab(label=team2_position_string, tab_id="tab-2"),
    ]
    return tabs

@app.callback(
    Output("tabs-content", "children"),
    [Input("tabs-output", "active_tab"),
    Input("output-div", 'children')]
)
def render_content(active_tab, selected_match):
    active_tab = active_tab or "tab-1"
    if active_tab not in ("tab-1", "tab-2"):
        active_tab = "tab-1"

    match_id = int(selected_match)
    cache_key = (match_id, active_tab)
    if cache_key in _position_matrix_cache:
        _position_matrix_cache.move_to_end(cache_key)
        return _position_matrix_cache[cache_key]

    team1 = team_dict[match_id][0]
    team2 = team_dict[match_id][1]

    match_events = get_match_events(match_id)

    if active_tab == "tab-1":
        events = [event for event in match_events if event["team"]["name"] == team1]
    else:
        events = [event for event in match_events if event["team"]["name"] == team2]

    div = html.Div(position_matrix(events))
    _position_matrix_cache[cache_key] = div
    _position_matrix_cache.move_to_end(cache_key)
    while len(_position_matrix_cache) > _POSITION_MATRIX_CACHE_MAX:
        _position_matrix_cache.popitem(last=False)
    return div

if __name__ == '__main__':
    port = int(os.getenv("PORT", "1080"))
    debug = os.getenv("DASH_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)