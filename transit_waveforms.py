# transit_waveforms.py

import os
import plotly.graph_objects as go
from datetime import timedelta
import natal_chart

planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune", "Pluto",
           "Saturn", "Sun", "Uranus", "Venus"]
aspects = {
    "Conjunction": 0,
    "Opposition": 180,
    "Trine": 120,
    "Square": 90,
    "Sextile": 60
}
orb = {
    "Conjunction": 8,
    "Opposition": 8,
    "Trine": 8,
    "Square": 8,
    "Sextile": 6
}

def calculate_transit_waveforms(natal_positions, start_date, end_date,
                                transiting_planets, selected_aspects):
    current_date = start_date
    transits = []

    while current_date <= end_date:
        for planet in transiting_planets:
            transit_position = natal_chart.get_transit_position(current_date, planet)
            for natal_planet, natal_position in natal_positions.items():
                for aspect_name in selected_aspects:
                    exact_angle = aspects[aspect_name]
                    angle_diff = abs((transit_position - natal_position - exact_angle) % 360)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff

                    if angle_diff <= orb[aspect_name]:
                        intensity = 1 - angle_diff / orb[aspect_name]
                        transits.append({
                            'date': current_date,
                            'transiting_planet': planet,
                            'natal_planet': natal_planet,
                            'aspect': aspect_name,
                            'intensity': intensity,
                        })
        current_date += timedelta(days=1)

    return transits

def build_waveform_figure_dict(transits, start_date, end_date, template="plotly_dark"):
    """
    Build a Plotly figure dictionary (data + layout)
    that the frontend can consume to do Plotly.newPlot(...).
    """
    # Create a day list
    day_count = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(day_count)]

    # Map "label" -> intensities
    intensity_map = {}
    for t in transits:
        label = f"{t['transiting_planet']} {t['aspect']} {t['natal_planet']}"
        if label not in intensity_map:
            intensity_map[label] = [0]*day_count
        idx = (t['date'] - start_date).days
        intensity_map[label][idx] = t['intensity']

    fig = go.Figure()
    for label, intensities in intensity_map.items():
        fig.add_trace(go.Scatter(
            x=[d.strftime("%Y-%m-%d") for d in dates],
            y=intensities,
            mode='lines',
            name=label
        ))

    fig.update_layout(
        title='Interactive Transit Waveforms',
        xaxis_title='Date',
        yaxis_title='Intensity',
        hovermode='x',
        template=template
    )

    return {
        "data": [trace.to_plotly_json() for trace in fig.data],
        "layout": fig.layout.to_plotly_json()
    }
