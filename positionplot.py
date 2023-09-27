import requests
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import soccerfield3

def load_json(url):
    response = requests.get(url)
    return response.json()

position_id_dict = {'centerback':[3,4,5],
                    'fullback':[2,6,7,8],
                    'midfielder':[9,10,11,13,14,15,18,19,20],
                    'winger':[12,16,17,21],
                    'striker':[22,23,24,25]}

color_dict = {'centerback':'dodgerblue',
              'fullback':'lightseagreen',
              'midfielder':'sandybrown',
              'winger':'lightcoral',
              'striker':'darkred'}

action_dict = {'ball receipt': [42], 'defence':[4,9,10], 'carry': [43], 'pass': [30], 'shot': [16]}

def plot_contour(events, position):
    positin_events = [e for e in events if 'position' in e and 'location' in e
                      and e['position']['id'] in position_id_dict[position]]
    field_layout = soccerfield3.get_layout()
    fig = go.Figure(layout=field_layout)
    fig.update_layout(xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)',
                      margin=dict(l=0, r=10, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} action heatmap<b>',
                                 xanchor="center", x=0.5, y=0.05))
    contour= go.Figure(go.Histogram2dContour(
        x=[e['location'][0] for e in positin_events],
        y=[e['location'][1] for e in positin_events],
        colorscale=['white', color_dict[position]], opacity=0.8, ncontours=10,
        contours=dict(
            showlines=False,
            coloring='fill', showlabels=True
        ),
        showscale = False),

    )
    fig.add_traces(contour.data)
    return fig

with open('json/all_receipt.json', "r") as json_file:
    all_receipt = json.load(json_file)
def plot_ballreceipt(events, position, ax):
    all = all_receipt[position]
    selected = [e for e in events if 'position' in e and 'location' in e
                                     and e['type']['id'] == 42
                                     and e['position']['id'] in position_id_dict[position]]
    if ax == 0:
        max = 120
        ax_name = 'depth'
    elif ax == 1:
        max = 80
        ax_name = 'width'

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} ball receipt {ax_name}<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['location'][ax] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=[e[ax] for e in all], marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['location'][ax] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_xaxes(range=[0, max], row=1, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_xaxes(range=[0, max], row=2, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig

with open('json/all_defence.json', "r") as json_file:
    all_defence = json.load(json_file)
def plot_defence(events, position, ax):
    all = all_defence[position]
    selected = [e for e in events if 'position' in e and 'location' in e
                                     and e['type']['id'] in [4,9,10]
                                     and e['position']['id'] in position_id_dict[position]]
    if ax == 0:
        max = 120
        ax_name = 'depth'
    elif ax == 1:
        max = 80
        ax_name = 'width'

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} defence {ax_name}<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['location'][ax] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=[e[ax] for e in all], marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['location'][ax] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_xaxes(range=[0, max], row=1, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_xaxes(range=[0, max], row=2, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig

with open('json/all_pass.json', "r") as json_file:
    all_pass = json.load(json_file)
def plot_passlength(events, position):
    all = [e for e in all_pass[position]]
    selected = [e for e in events if 'position' in e
                                     and e['position']['id'] in position_id_dict[position]
                                     and e['type']['id'] == 30]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} passing length<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=[p['length'] for p in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['pass']['length'] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=[p['length'] for p in all], marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['pass']['length'] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig

def plot_passangle(events, position):
    all = [e for e in all_pass[position]]
    selected = [e for e in events if 'position' in e
                                     and e['position']['id'] in position_id_dict[position]
                                     and e['type']['id'] == 30]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} passing angle<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=[p['angle'] for p in all],
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['pass']['angle'] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=[p['angle'] for p in all], marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['pass']['angle'] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig

with open('json/all_shot.json', "r") as json_file:
    all_shot = json.load(json_file)
def plot_shot(events, position, ax):
    all = [e for e in all_shot[position]]
    selected = [e for e in events if 'position' in e and 'location' in e
                                     and e['type']['id'] == 16
                                     and e['position']['id'] in position_id_dict[position]]
    if ax == 0:
        max = 120
        ax_name = 'depth'
    elif ax == 1:
        max = 80
        ax_name = 'width'

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} shot {ax_name}<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['location'][ax] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=0.5),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=[e[ax] for e in all], marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['location'][ax] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_xaxes(range=[0, max], row=1, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_xaxes(range=[0, max], row=2, col=1, tickvals=list(range(0, max+1, 40)))
    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig

with open('json/all_carry.json', "r") as json_file:
    all_carry = json.load(json_file)
def plot_carry(events, position):
    all = all_carry[position]
    selected = [e for e in events if 'position' in e
                                     and e['position']['id'] in position_id_dict[position]
                                     and e['type']['id'] == 43]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} carry duration(s)<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.add_trace(go.Histogram(
        x=all,
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='all matches', marker=dict(color='grey')),
        row=1, col=1)
    fig.add_trace(go.Histogram(
        x=[e['duration'] for e in selected],
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='selected match', marker=dict(color=color_dict[position])),
        row=1, col=1)

    fig.add_trace(go.Box(
        x=all, marker=dict(color='grey'),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.add_trace(go.Box(
        x=[e['duration'] for e in selected], marker=dict(color=color_dict[position]),
        showlegend=False, hoverinfo='none'), row=2, col=1)

    fig.update_yaxes(showticklabels=False, row=2, col=1)

    fig.update_layout(barmode='overlay')
    fig.update_traces(opacity=0.45)
    return fig