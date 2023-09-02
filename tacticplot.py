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

def plot(match_id, team_nation, opponent_nation):
    url = f'https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json'
    match_events = load_json(url)
    team = f"{team_nation} Women's"
    opponent = f"{opponent_nation} Women's" 
    
    starting_XI = [event for event in match_events if event['team']['name'] == team and event['type']['id'] == 35]
    position_ids = [player['position']['id'] for player in starting_XI[0]['tactics']['lineup']]
    
    tactic_XI = [event for event in match_events if event['team']['name'] == team and event['type']['id'] == 36]
    
    team_events = [event for event in match_events if event['team']['name'] == team]
    
    goal_events = [event for event in match_events if event['type']['id'] == 16 and 
            event['team']['name'] == team and event['shot']['outcome']['name'] == 'Goal']
    no_goal_events = [event for event in match_events if event['type']['id'] == 16 and 
            event['team']['name'] == team and event['shot']['outcome']['name'] != 'Goal']
    
    oppo_goal_events = [event for event in match_events if event['type']['id'] == 16 and 
            event['team']['name'] == opponent and event['shot']['outcome']['name'] == 'Goal']
    oppo_no_goal_events = [event for event in match_events if event['type']['id'] == 16 and 
            event['team']['name'] == opponent and event['shot']['outcome']['name'] != 'Goal']
    
    goal_seq = {}
    for event in goal_events:
        before_goal_events = team_events[team_events.index(event) - 4:team_events.index(event)+1]
        before_goal_events= [e for e in before_goal_events if 'location' in e]
        goal_seq[event['index']] = before_goal_events
        
    no_goal_seq = {}
    for event in no_goal_events:
        before_no_goal_events = team_events[team_events.index(event) - 4:team_events.index(event)+1]
        before_no_goal_events= [e for e in before_no_goal_events if 'location' in e]
        no_goal_seq[event['index']] = before_no_goal_events
    
    team_carry = [event for event in match_events if event['type']['id'] == 43 and
                event['team']['name'] == team and event['duration'] > 3.5]        
            
    dispo_events = [event for event in match_events if event['team']['name'] == opponent and
               event['type']['id'] == 3]
    
    opponent_carry = [event for event in match_events if event['type']['id'] == 43 and
                event['team']['name'] == opponent and event['duration'] > 3.5]
        
    field_layout = soccerfield.get_layout()
    field_layout.update(legend=dict(x=0.85, y=1))

    fig = go.Figure(layout=field_layout)
    fig.update_layout(title = dict(text = f'{team} vs {opponent}', x =0.5, y =0.9), 
                      title_font=dict(size=20, family='Arial', color='black'))

    # Starting lineups
    fig.add_trace(go.Scatter(
        x = [position_dict[i][0] for i in position_ids],
        y = [position_dict[i][1] for i in position_ids],
        mode='markers',
        name = 'starting XI',
        marker=dict(size=8, symbol = 'circle', color='lightblue',
            line = dict(width = 1, color = 'darkblue')),
    ))
    
    # Tactical shifts
    if len(tactic_XI) != 0:
        for tac in tactic_XI:
            time = str(tac['minute']) + ':' + str(tac['second'])
            tac_ids = [player['position']['id'] for player in tac['tactics']['lineup']]
            if tac_ids != position_ids:
                fig.add_trace(go.Scatter(
                    x = [position_dict[i][0] for i in tac_ids],
                    y = [position_dict[i][1] for i in tac_ids],
                    mode='markers',
                    name = f'tactical shit - {time}',
                    marker=dict(size=8, symbol = 'circle', color='lightblue', opacity=0.5,
                        line = dict(width = 1, color = 'steelblue')),
                    showlegend = True, visible='legendonly'
                ))

    # Shot with no goal - team
    fig.add_trace(go.Scatter(
        x = [event['location'][0] for event in no_goal_events],
        y = [event['location'][1] for event in no_goal_events],
        legendgroup = 'no goal shots',
        name = 'team shot w/ no goal',
        mode='markers',
        marker=dict(size=5, symbol = 'circle', color='darkgoldenrod')
    ))

    # Shot with goals - team
    fig.add_trace(go.Scatter(
        x = [event['location'][0] for event in goal_events],
        y = [event['location'][1] for event in goal_events],
        legendgroup = 'goal shots',
        name = 'team shot w/ goal',
        mode='markers',
        marker=dict(size=6, symbol = 'circle', color='purple')
    ))

    # Shot with no goal - oppo
    fig.add_trace(go.Scatter(
        x = [120-event['location'][0] for event in no_goal_events],
        y = [event['location'][1] for event in no_goal_events],
        legendgroup = 'oppo no goal shots', visible='legendonly',
        name = 'opponent shot w/ no goal',
        mode='markers',
        marker=dict(size=5, symbol = 'circle', color='darkgoldenrod')
    ))
    
    # Shot with goals - oppo
    fig.add_trace(go.Scatter(
        x = [120-event['location'][0] for event in oppo_goal_events],
        y = [event['location'][1] for event in oppo_goal_events],
        legendgroup = 'oppo goal shots', visible='legendonly',
        name = 'opponent shot w/ goal',
        mode='markers',
        marker=dict(size=6, symbol = 'circle', color='purple')
    ))

    # Moves before shot with goals
    for key, seq in goal_seq.items():
        fig.add_trace(go.Scatter(
            x = [event['location'][0] for event in seq[:-1]],
            y = [event['location'][1] for event in seq[:-1]],
            legendgroup = 'goal shots',
            showlegend = False,
            mode='markers',
            marker=dict( size=6, symbol = 'circle', color='purple', opacity=0.3)
        ))
    for key, seq in goal_seq.items():
        fig.add_trace(go.Scatter(
            x=[event['location'][0] for event in seq],  
            y=[event['location'][1] for event in seq], 
            legendgroup = 'goal shots',
            showlegend = False,
            mode='lines',
            line=dict(color='purple', width = 0.25)
        ))

    # Moves before shot with no goal
    for key, seq in no_goal_seq.items():
        fig.add_trace(go.Scatter(
            x = [event['location'][0] for event in seq[:-1]],
            y = [event['location'][1] for event in seq[:-1]],
            legendgroup = 'no goal shots',
            showlegend = False,
            mode='markers',
            marker=dict( size=5, symbol = 'circle', color='tan', opacity=0.3)
        ))
    for key, seq in no_goal_seq.items():
        fig.add_trace(go.Scatter(
            x=[event['location'][0] for event in seq],  
            y=[event['location'][1] for event in seq], 
            legendgroup = 'no goal shots',
            showlegend = False,
            mode='lines',
            line=dict(color='tan', width = 0.18)
        ))    

    # Opponent disposession
    fig.add_trace(go.Scatter(
        x = [120-event['location'][0] for event in dispo_events],
        y = [event['location'][1] for event in dispo_events],
        name = 'opponent disposession',
        mode='markers',
        marker=dict(size=6, symbol = 'x', color='darkseagreen', opacity=0.6)
    ))
    
    # Team carry
    fig.add_trace(go.Scatter(x = [None], y = [None], legendgroup = 'team_carry', name = 'team_carry',
                            mode='lines', line=dict(color='orchid', width = 0.4, dash = 'dash'), visible='legendonly'))
    
    for carry in team_carry:
        fig.add_trace(go.Scatter(
            x = [carry['location'][0], carry['carry']['end_location'][0]],
            y = [carry['location'][1], carry['carry']['end_location'][1]],
            legendgroup = 'team_carry',
            showlegend = False, visible='legendonly',
            mode='lines',
            line=dict(color='orchid', width = 0.3, dash = 'dash')
        ))    
        
    # Opponent carry
    fig.add_trace(go.Scatter(x = [None], y = [None], legendgroup = 'opponent_carry', name = 'opponent_carry',
                            mode='lines', line=dict(color='darkgrey', width = 0.4, dash = 'dash')))
    
    for carry in opponent_carry:
        fig.add_trace(go.Scatter(
            x = [120-carry['location'][0], 120-carry['carry']['end_location'][0]],
            y = [carry['location'][1], carry['carry']['end_location'][1]],
            legendgroup = 'opponent_carry',
            showlegend = False,
            mode='lines',
            line=dict(color='darkgrey', width = 0.3, dash = 'dash')
        ))

    return fig