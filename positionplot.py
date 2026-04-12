import json
from pathlib import Path
from typing import Dict, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import soccerfield3

_BASE_DIR = Path(__file__).resolve().parent
_JSON_DIR = _BASE_DIR / "json"

position_id_dict = {'centerback':[3,4,5],
                    'fullback':[2,6,7,8],
                    'midfielder':[9,10,11,13,14,15,18,19,20],
                    'winger':[12,16,17,21],
                    'striker':[22,23,24,25]}

_PID_TO_ROLE = {
    pid: role for role, ids in position_id_dict.items() for pid in ids
}


def build_role_buckets(events) -> Tuple[Dict[str, List], Dict[str, List]]:
    """One pass over match events: split by tactical role (located vs position-only)."""
    by_role_located: Dict[str, List] = {role: [] for role in position_id_dict}
    by_role_positioned: Dict[str, List] = {role: [] for role in position_id_dict}
    for e in events:
        if 'position' not in e:
            continue
        role = _PID_TO_ROLE.get(e['position']['id'])
        if role is None:
            continue
        by_role_positioned[role].append(e)
        if 'location' in e:
            by_role_located[role].append(e)
    return by_role_located, by_role_positioned

color_dict = {'centerback':'dodgerblue',
              'fullback':'lightseagreen',
              'midfielder':'sandybrown',
              'winger':'lightcoral',
              'striker':'darkred'}

def plot_contour(events, position, *, role_located=None):
    if role_located is not None:
        positin_events = role_located
    else:
        positin_events = [e for e in events if 'position' in e and 'location' in e
                          and e['position']['id'] in position_id_dict[position]]
    field_layout = soccerfield3.get_layout()
    fig = go.Figure(layout=field_layout)
    fig.update_layout(xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False),
                      plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)',
                      margin=dict(l=0, r=10, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} action heatmap<b>',
                                 xanchor="center", x=0.5, y=0.05))
    fig.update_layout(dragmode=False)

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

with (_JSON_DIR / "all_receipt.json").open("r") as json_file:
    all_receipt = json.load(json_file)
def plot_ballreceipt(events, position, ax, *, role_located=None):
    all = all_receipt[position]
    if role_located is not None:
        selected = [e for e in role_located if e['type']['id'] == 42]
    else:
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
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='competition', marker=dict(color='grey')),
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

with (_JSON_DIR / "all_defence.json").open("r") as json_file:
    all_defence = json.load(json_file)
def plot_defence(events, position, ax, *, role_located=None):
    all = all_defence[position]
    if role_located is not None:
        selected = [e for e in role_located if e['type']['id'] in (4, 9, 10)]
    else:
        selected = [e for e in events if 'position' in e and 'location' in e
                                         and e['type']['id'] in [4, 9, 10]
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
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='competition', marker=dict(color='grey')),
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

with (_JSON_DIR / "all_pass.json").open("r") as json_file:
    all_pass = json.load(json_file)
def plot_passlength(events, position, *, role_positioned=None):
    all = [e for e in all_pass[position]]
    if role_positioned is not None:
        selected = [e for e in role_positioned if e['type']['id'] == 30]
    else:
        selected = [e for e in events if 'position' in e
                                         and e['position']['id'] in position_id_dict[position]
                                         and e['type']['id'] == 30]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} passing length<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=[p['length'] for p in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='competition', marker=dict(color='grey')),
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

def plot_passangle(events, position, *, role_positioned=None):
    all = [e for e in all_pass[position]]
    if role_positioned is not None:
        selected = [e for e in role_positioned if e['type']['id'] == 30]
    else:
        selected = [e for e in events if 'position' in e
                                         and e['position']['id'] in position_id_dict[position]
                                         and e['type']['id'] == 30]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} passing angle<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=[p['angle'] for p in all],
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='competition', marker=dict(color='grey')),
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

with (_JSON_DIR / "all_carry.json").open("r") as json_file:
    all_carry = json.load(json_file)
def plot_carry(events, position, *, role_positioned=None):
    all = all_carry[position]
    if role_positioned is not None:
        selected = [e for e in role_positioned if e['type']['id'] == 43]
    else:
        selected = [e for e in events if 'position' in e
                                         and e['position']['id'] in position_id_dict[position]
                                         and e['type']['id'] == 43]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=45), height = 260,
                      title = dict(text=f'<b>{position} carry duration(s)<b>',
                                 xanchor="center", x=0.5, y=0.05),
                      legend=dict(orientation='h', x=0, y=1.15),
                      )
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=all,
        histnorm='percent', xbins=go.histogram.XBins(size=0.1),
        name='competition', marker=dict(color='grey')),
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

with (_JSON_DIR / "all_shot.json").open("r") as json_file:
    all_shot = json.load(json_file)
def plot_shot(events, position, ax, *, role_located=None):
    all = [e for e in all_shot[position]]
    if role_located is not None:
        selected = [e for e in role_located if e['type']['id'] == 16]
    else:
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
    fig.update_layout(dragmode=False)

    fig.add_trace(go.Histogram(
        x=[e[ax] for e in all],
        histnorm='percent', xbins=go.histogram.XBins(size=1),
        name='competition', marker=dict(color='grey')),
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
