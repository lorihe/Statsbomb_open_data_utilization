import pandas as pd
import numpy as np
import dash
import plotly.graph_objects as go

def get_layout():

    dash_2 = go.layout.Shape(
        type="rect",
        x0=18, y0=18, x1=102, y1=62,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    dash_3 = go.layout.Shape(
        type="rect",
        x0=18, y0=30, x1=102, y1=50,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    dash_4 = go.layout.Shape(
        type="line",
        x0=40, y0=0, x1=40, y1=18,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    dash_5 = go.layout.Shape(
        type="line",
        x0=80, y0=0, x1=80, y1=18,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    dash_6 = go.layout.Shape(
        type="line",
        x0=40, y0=62, x1=40, y1=80,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    dash_7 = go.layout.Shape(
        type="line",
        x0=80, y0=62, x1=80, y1=80,
        line=dict(color='darkgrey', width=1, dash='dash'),
    )

    field_shape = go.layout.Shape(
        type="rect",
        x0=0, y0=0, x1=120, y1=80,
        line=dict(color='black', width=2.5, dash='solid'),
        layer='below'
    )    
    
    center_line = go.layout.Shape(
        type = 'line',
        x0 = 60, y0 = 0, x1 = 60, y1 = 80,
        line=dict(color='darkgrey', width=0.5, dash='solid')
    )
    
    box_left = go.layout.Shape(
        type="rect",
        x0=0, y0=18, x1=18, y1=62,
        line=dict(color='darkgrey', width=1, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_right = go.layout.Shape(
        type="rect",
        x0=102, y0=18, x1=120, y1=62,
        line=dict(color='darkgrey', width=1, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_left_small = go.layout.Shape(
        type="rect",
        x0=0, y0=30, x1=6, y1=50,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_right_small = go.layout.Shape(
        type="rect",
        x0=114, y0=30, x1=120, y1=50,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )    
    
    center_circle = go.layout.Shape(
        type = 'circle',
        x0 = 50, y0 = 30, x1 = 70, y1 = 50,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )

    radius = 10
    theta = np.linspace(np.arccos((18 - 12) / 10), -np.arccos((18 - 12) / 10), 100)
    x_left = 12 + radius * np.cos(theta)
    x_right = 120-x_left   
    y = 40 + radius * np.sin(theta)
    
    arc_left = go.layout.Shape(
        type="path",
        path=f"M {x_left[0]},{y[0]}"
             + " L" + " L".join([f"{x_val},{y_val}" for x_val, y_val in zip(x_left, y)])
             + f" L {x_left[-1]},{y[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    arc_right = go.layout.Shape(
        type="path",
        path=f"M {x_right[0]},{y[0]}"
             + " L" + " L".join([f"{x_val},{y_val}" for x_val, y_val in zip(x_right, y)])
             + f" L {x_right[-1]},{y[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    layout = go.Layout(
        xaxis=dict(range=[0, 120], constrain='domain', dtick=40),
        yaxis=dict(range=[80, 0], constrain='domain', scaleanchor="x", scaleratio=1),
        shapes = [dash_2, dash_3, dash_4, dash_5, dash_6, dash_7, field_shape, center_line, box_left, box_right,
                  box_left_small, box_right_small, center_circle, arc_left, arc_right]
    )
    return layout