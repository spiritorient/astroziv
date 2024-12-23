import os
import plotly.graph_objects as go
from datetime import timedelta
import natal_chart  # Reuse your natal_chart module for transit position calculations

# Define planets, aspects, and orbs
planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune", "Pluto",
           "Saturn", "Sun", "Uranus", "Venus"]
aspects = {"Conjunction": 0, "Opposition": 180, "Trine": 120,
           "Square": 90, "Sextile": 60}
orb = {"Conjunction": 8, "Opposition": 8, "Trine": 8,
       "Square": 8, "Sextile": 6}

def calculate_transit_waveforms(natal_positions, start_date, end_date, transiting_planets, selected_aspects):
    """
    Calculate transit interactions for a natal chart over a date range.
    """
    print(f"Calculating transit waveforms from {start_date} to {end_date}")
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
                        angle_diff = 360 - angle_diff  # Normalize angle difference

                    if angle_diff <= orb[aspect_name]:  # Within orb
                        intensity = 1 - angle_diff / orb[aspect_name]
                        transits.append({
                            'date': current_date,
                            'transiting_planet': planet,
                            'natal_planet': natal_planet,
                            'aspect': aspect_name,
                            'intensity': intensity,
                        })
                        # Optional: Print transit details for debugging
                        # print(f"Transit: {transits[-1]}")

        current_date += timedelta(days=1)

    print(f"Total transits calculated: {len(transits)}")
    return transits

def generate_interactive_transit_waveform_plot(transits, start_date, end_date):
    """
    Generate an interactive waveform plot using Plotly.
    """
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    intensity_data = {}
    for t in transits:
        key = f"{t['transiting_planet']} {t['aspect']} {t['natal_planet']}"
        if key not in intensity_data:
            intensity_data[key] = [0] * len(dates)
        index = (t['date'] - start_date).days
        intensity_data[key][index] = t['intensity']

    # Create the Plotly figure
    fig = go.Figure()

    # Add each wave to the plot
    for label, intensity in intensity_data.items():
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=intensity,
                mode='lines',
                name=label,
                hoverinfo='name+y',
                line=dict(width=2),  # Adjust line thickness
            )
        )

    # Customize layout
    fig.update_layout(
        title='Interactive Transit Waveforms',
        xaxis_title='Date',
        yaxis_title='Intensity',
        legend_title='Aspects',
        hovermode='x unified',
    )

    # Save as an HTML file for rendering in a browser
    html_path = 'static/transit_waveforms.html'
    fig.write_html(html_path)
    return html_path