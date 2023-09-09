import requests
import json
import pandas as pd
import urllib.request

import soccerfield

import dash
import plotly.graph_objects as go

def load_json(url):
    response = requests.get(url)
    return response.json()

position_dict = {1:(10, 40),
                 2:(25, 72), 3:(25, 56), 4:(25, 40), 5:(25, 24), 6:(25, 8),
                 7:(42.5, 72), 9:(42.5, 56), 10:(42.5, 40), 11:(42.5, 24), 8:(42.5, 8),
                 12:(60, 72), 13:(60, 56), 14:(60, 40), 15:(60, 24), 16:(60, 8),
                 17:(77.5, 72), 18:(77.5, 56), 19:(77.5, 40), 20:(77.5, 24), 21:(77.5, 8),
                 25:(88.75, 40), 22:(100, 56), 23:(100, 40), 24:(100, 24)}

goal = 'sienna'
no_goal = 'goldenrod'
carry = 'lightgrey'
defense = 'darkgreen'
defense_no = 'yellowgreen'
passes = 'slategrey'

def get_events(events):
    
    goal_events = [e for e in events if e['type']['id'] == 16 and 
            e['shot']['outcome']['name'] == 'Goal']
    no_goal_events = [e for e in events if e['type']['id'] == 16 and 
            e['shot']['outcome']['name'] != 'Goal']    

    goal_seq = {}
    for e in goal_events:        
        before_goal_events = events[events.index(e)-4 : events.index(e)+1]
        before_goal_events = [e for e in before_goal_events if 'location' in e]
        goal_seq[e['index']] = before_goal_events
        
    no_goal_seq = {}
    for e in no_goal_events:
        before_no_goal_events = events[events.index(e)-4 : events.index(e)+1]
        before_no_goal_events= [e for e in before_no_goal_events if 'location' in e]
        no_goal_seq[e['index']] = before_no_goal_events    
    
    carry = [e for e in events if e['type']['id'] == 43 and e['duration'] > 3.5] 

    defense = [e for e in events if e['type']['id'] == 9 or 
                                    (e['type']['id'] == 4 and e['duel']['type']['id'] in [11, 4, 15, 16, 17]) or 
                                    (e['type']['id'] == 10 and e['interception']['outcome']['id'] in [4, 15, 16, 17])]

    defense_no = [e for e in events if (e['type']['id'] == 4 and e['duel']['type']['id'] not in [11, 4, 15, 16, 17]) or
                                       (e['type']['id'] == 10 and e['interception']['outcome']['id'] not in [4, 15, 16, 17])]

    passes_l = [e for e in events if e['type']['id'] == 30 and e['pass']['length'] > 40 and 'outcome' not in e['pass']]

    starting_XI = [e for e in events if e['type']['id'] == 35]
    tactic_shift = [e for e in events if e['type']['id'] == 36]

    return (goal_events, no_goal_events, goal_seq, no_goal_seq, carry, defense,
            defense_no, passes_l, starting_XI, tactic_shift)

def plot(team1_name, team1_tuples, team2_tuples):
    field_layout = soccerfield.get_layout()
    field_layout.update(legend=dict(xanchor="left", x=1, y=0.88))

    fig = go.Figure(layout=field_layout)
    fig.update_layout(title=dict(text=f'{team1_name} Tactic Plot', x=0.41, y=0.93),
                      title_font=dict(size=18, color='black'),
                      width=1080, height=720, paper_bgcolor = "RGB(247,247,247)", plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=0, r=0, t=0, b=0))


    fig.add_trace(go.Scatter(x = [None], y = [None], legendgroup = 'carry', name = 'opponent carry (>3.5s)',
                            mode='lines', line=dict(color=carry, width = 1.6, dash = 'dashdot')))
    for e in team2_tuples[4]:
        fig.add_trace(go.Scatter(
            x = [120-e['location'][0], 120-e['carry']['end_location'][0]],
            y = [80-e['location'][1], 80-e['carry']['end_location'][1]],
            legendgroup = 'carry',
            showlegend = False,
            mode='lines',
            line=dict(color=carry, width = 1.6, dash = 'dashdot')
        ))

    fig.add_trace(go.Scatter(x = [None], y = [None], legendgroup = 'passes', name = 'opponent long pass succeed',
                        mode='lines+markers',
                        marker = dict(symbol = 'circle-open', color = passes, size = 8),
                        line=dict(color=passes, width = 0.4, dash = 'dot')))
    for e in team2_tuples[7]:
        fig.add_trace(go.Scatter(
            x = [120-e['pass']['end_location'][0]],
            y = [80-e['pass']['end_location'][1]],
            legendgroup = 'passes',
            showlegend=False,
            mode='markers', marker=dict(size=6, symbol = 'circle-open', color= passes, opacity=0.6)))
        fig.add_trace(go.Scatter(
            x = [120-e['location'][0]],
            y = [80-e['location'][1]],
            legendgroup = 'passes',
            showlegend = False,
            mode='markers', marker=dict(size=3, symbol = 'circle-open', color= passes, opacity=0.6)))
        fig.add_trace(go.Scatter(
            x = [120-e['location'][0], 120-e['pass']['end_location'][0]],
            y = [80-e['location'][1], 80-e['pass']['end_location'][1]],
            legendgroup = 'passes',
            showlegend = False,
            mode='lines',
            line=dict(color=passes, width = 0.3, dash = 'dot')
        ))

    fig.add_trace(go.Scatter(
        x = [e['location'][0] for e in team1_tuples[1]],
        y = [e['location'][1] for e in team1_tuples[1]],
        legendgroup = 'no goal shots',
        name = 'shots w/ no goal',
        mode='markers',
        marker=dict(size=6 , symbol = 'circle', color=no_goal)))
    
    fig.add_trace(go.Scatter(
        x = [e['location'][0] for e in team1_tuples[0]],
        y = [e['location'][1] for e in team1_tuples[0]],
        legendgroup = 'goal shots',
        name = 'shots w/ goal',
        mode='markers',
        marker=dict(size=9, symbol = 'circle', color=goal)
    ))        

    for key, seq in team1_tuples[3].items():
        fig.add_trace(go.Scatter(
            x = [e['location'][0] for e in seq[:-1]],
            y = [e['location'][1] for e in seq[:-1]],
            legendgroup = 'no goal shots',
            showlegend = False,
            mode='markers',
            marker=dict( size=6, symbol = 'circle', color=no_goal, opacity=0.2)
        ))        
    for key, seq in team1_tuples[3].items():
        fig.add_trace(go.Scatter(
            x=[event['location'][0] for event in seq],  
            y=[event['location'][1] for event in seq], 
            legendgroup = 'no goal shots',
            showlegend = False,
            mode='lines',
            line=dict(color=no_goal, width = 0.6)
        ))      
        
    for key, seq in team1_tuples[2].items():
        fig.add_trace(go.Scatter(
            x = [e['location'][0] for e in seq[:-1]],
            y = [e['location'][1] for e in seq[:-1]],
            legendgroup = 'goal shots',
            showlegend = False,
            mode='markers',
            marker=dict(size=6, symbol = 'circle', color=goal, opacity=0.2)
        ))        
    for key, seq in team1_tuples[2].items():
        fig.add_trace(go.Scatter(
            x=[event['location'][0] for event in seq],  
            y=[event['location'][1] for event in seq], 
            legendgroup = 'goal shots',
            showlegend = False,
            mode='lines',
            line=dict(color=goal, width = 1.2)
        ))
    
    fig.add_trace(go.Scatter(
        x = [e['location'][0] for e in team1_tuples[5]],
        y = [e['location'][1] for e in team1_tuples[5]],
        name = 'defense-success',
        mode='markers',
        marker=dict(size=6, symbol = 'diamond', color=defense, opacity=0.8)
    ))

    fig.add_trace(go.Scatter(
        x = [e['location'][0] for e in team1_tuples[6]],
        y = [e['location'][1] for e in team1_tuples[6]],
        name = 'defense-no success',
        mode='markers',
        marker=dict(size=6, symbol = 'diamond', color=defense_no, opacity=0.8)
    ))
    
    return fig

def formation(team1_tuples):
    field_layout = soccerfield.get_layout()
    field_layout.update(legend=dict(xanchor="left", x=1, y=0.88))

    fig = go.Figure(layout=field_layout)
    fig.update_layout(width=144, height=96, paper_bgcolor = "RGB(242,242,242)", plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=0, r=0, t=0, b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))

    position_ids = [player['position']['id'] for player in team1_tuples[8][0]['tactics']['lineup']]
    fig.add_trace(go.Scatter(
        x = [position_dict[i][0] for i in position_ids],
        y = [position_dict[i][1] for i in position_ids],
        mode='markers',
        name = 'starting XI',
        marker=dict(size=8, symbol = 'circle', color='lightblue',
            line = dict(width = 1, color = 'darkblue')),
    ))

    return fig
