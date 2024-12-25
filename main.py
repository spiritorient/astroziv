import os
import platform
import re
from datetime import datetime

import plotly.graph_objects as go
import numpy as np
from flask import Flask, jsonify, render_template, request

import natal_chart
import transit_waveforms

# If you have any platform-specific logic:
if platform.system() == "Darwin":  # macOS
    pass
else:
    pass

app = Flask(__name__)

# Define the planets and zodiac signs
planets = ["Jupiter", "Mars", "Mercury", "Moon", "Neptune",
           "Pluto", "Saturn", "Sun", "Uranus", "Venus"]
zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Planet symbols in Unicode
planet_symbols = {
    "Jupiter": "♃",
    "Mars": "♂",
    "Mercury": "☿",
    "Moon": "☾",
    "Neptune": "♆",
    "Pluto": "♇",
    "Saturn": "♄",
    "Sun": "☉",
    "Uranus": "♅",
    "Venus": "♀"
}

# Define major aspects with their allowable orb (in degrees)
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

aspect_colors = {
    "Conjunction": "white",
    "Opposition": "red",
    "Trine": "green",
    "Square": "blue",
    "Sextile": "purple"
}

@app.route("/")
def index():
    # Render index.html with aspect and planet data
    return render_template("index.html", planets=planets, aspects=aspects.keys())

@app.route("/calculate_natal_chart", methods=["POST"])
def calculate_chart():
    """
    Calculate natal chart positions based on date/time of birth and lat/lon.
    """
    data = request.json
    if data is None:
        return jsonify({"error": "Missing or invalid JSON data"}), 400

    dob = data.get("dob")
    tob = data.get("tob")
    chart_name = data.get("chartName")

    if "lat" in data and "lon" in data:
        lat = float(data["lat"])
        lon = float(data["lon"])
    else:
        return jsonify({"error": "Missing geographic information"}), 400

    try:
        chart = natal_chart.calculate_natal_chart(dob, tob, lat, lon)
        return jsonify({"success": True, "chart": chart, "chartName": chart_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_plot", methods=["POST"])
def generate_plot():
    """
    Convert planetary positions to degrees, then generate only ONE plot:
     - The Aspect Chart (in polar form, but effectively a "cartesian" aspect wheel).
    Returns the path to the HTML file so the front end can display it.
    """
    try:
        data = request.json
        positions = data.get("positions")
        selected_aspects = data.get("aspects", [])

        # Convert position strings to decimal degrees
        for planet, pos_str in positions.items():
            positions[planet] = convert_to_degrees(pos_str)

        # Generate the aspect wheel chart
        aspect_plot_url = generate_aspect_plot(positions, selected_aspects)

        # Return only the aspect_plot_url
        return jsonify({"plot_url": aspect_plot_url})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/transit_waveforms", methods=["POST"])
def transit_waveforms_route():
    """
    Generate transit waveforms over a specified date range, 
    for chosen transiting planets/aspects relative to a natal chart.
    Returns a Plotly HTML to be loaded in an <iframe>.
    """
    try:
        data = request.json
        natal_chart_positions = data.get("natal_chart")
        start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")
        end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d")
        selected_transiting_planets = data.get("transiting_planets")
        selected_aspects = data.get("aspects")

        # Validate
        if (not natal_chart_positions or not start_date or not end_date 
            or not selected_transiting_planets or not selected_aspects):
            return jsonify({"error": "Invalid input data"}), 400

        # Convert natal chart positions from strings to degrees
        natal_positions = {}
        for planet, pos_str in natal_chart_positions.items():
            natal_positions[planet] = convert_to_degrees(pos_str)

        # Calculate waveforms
        transits = transit_waveforms.calculate_transit_waveforms(
            natal_positions, start_date, end_date, 
            selected_transiting_planets, selected_aspects
        )

        plot_url = transit_waveforms.generate_interactive_transit_waveform_plot(
            transits, start_date, end_date
        )

        return jsonify({
            "plot_url": plot_url,
            "transits": [
                {
                    "date": t["date"].strftime("%Y-%m-%d"),
                    "transiting_planet": t["transiting_planet"],
                    "natal_planet": t["natal_planet"],
                    "aspect": t["aspect"],
                    "intensity": round(t["intensity"], 3)
                }
                for t in transits
            ]
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def convert_to_degrees(position):
    """
    Convert a string like '20° 26' 27.06" Aries' into decimal degrees [0..359].
    """
    pattern = r"""
        (\d+\.?\d*)        # Degrees
        °\s*
        (?:(\d+\.?\d*)')?  # Optional minutes
        \s*
        (?:(\d+\.?\d*)")?  # Optional seconds
        \s*
        ([A-Za-z]+)        # Zodiac sign
    """
    match = re.match(pattern, position.strip(), re.VERBOSE)
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2)) if match.group(2) else 0.0
        seconds = float(match.group(3)) if match.group(3) else 0.0
        sign = match.group(4).capitalize()
        total_degrees = degrees + minutes / 60 + seconds / 3600

        # Find sign index
        if sign not in zodiac_signs:
            raise ValueError(f"Invalid zodiac sign: '{sign}' in '{position}'")
        sign_index = zodiac_signs.index(sign)
        sign_offset = sign_index * 30

        return total_degrees + sign_offset
    else:
        raise ValueError(f"Invalid position format: '{position}'")

def generate_aspect_plot(positions, selected_aspects):
    """
    Generate a single aspect chart (the "cartesian" aspect wheel) in polar form
    but with lines for aspects. Writes HTML to static/aspect_plot.html.
    Returns the path to the resulting file.
    """
    fig = go.Figure()

    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    sign_angles = [(i * degrees_per_sign + degrees_per_sign / 2) for i in range(num_signs)]

    def degrees_to_zodiac_sign_position(deg):
        sign_index = int(deg // 30) % 12
        sign = zodiac_signs[sign_index]
        pos_in_sign = deg % 30
        d = int(pos_in_sign)
        m = int((pos_in_sign - d) * 60)
        s = (pos_in_sign - d - m / 60) * 3600
        return f"{d}° {m}' {s:.2f}\" {sign}"

    # Add zodiac boundaries
    for i in range(num_signs):
        boundary_angle = i * 30
        fig.add_trace(go.Scatterpolar(
            r=[0, 1.2],
            theta=[boundary_angle, boundary_angle],
            mode="lines",
            line=dict(color="gray", width=1, dash="dot"),
            showlegend=False,
            hoverinfo="none"
        ))

    # Add zodiac labels
    for angle, sign in zip(sign_angles, zodiac_signs):
        fig.add_trace(go.Scatterpolar(
            r=[1.15],
            theta=[angle],
            mode="text",
            text=[sign],
            textfont=dict(size=12),
            showlegend=False,
            hoverinfo="none"
        ))

    # Plot planets
    planet_r = []
    planet_theta = []
    planet_text = []
    planet_hover = []
    for planet, degree in positions.items():
        planet_r.append(1.0)
        planet_theta.append(degree)
        planet_text.append(planet_symbols[planet])
        hover_str = degrees_to_zodiac_sign_position(degree)
        planet_hover.append(f"{planet} {hover_str}")

    fig.add_trace(go.Scatterpolar(
        r=planet_r,
        theta=planet_theta,
        mode="markers+text",
        text=planet_text,
        textposition="middle center",
        marker=dict(size=15, color="#636363"),
        textfont=dict(size=11),
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=planet_hover,
        showlegend=False
    ))

    # Draw aspect lines
    for planet1, angle1 in positions.items():
        for planet2, angle2 in positions.items():
            if planet1 < planet2:
                difference = abs(angle1 - angle2)
                if difference > 180:
                    difference = 360 - difference
                for aspect_name in selected_aspects:
                    aspect_angle = aspects[aspect_name]
                    if abs(difference - aspect_angle) <= orb[aspect_name]:
                        color = aspect_colors.get(aspect_name, "cyan")
                        fig.add_trace(go.Scatterpolar(
                            r=[0.98, 0.98],
                            theta=[angle1, angle2],
                            mode="lines",
                            line=dict(color=color, width=2),
                            name=f"{planet1}-{aspect_name}-{planet2}",
                            hoverinfo="skip"
                        ))

    fig.update_layout(
        template="plotly_dark",
        polar=dict(
            angularaxis=dict(
                showgrid=True,
                linecolor="#03002C",
                gridcolor="gray",
                linewidth=1,
                showline=True,
                tickmode="array",
                tickvals=[],
                ticktext=[]
            ),
            radialaxis=dict(visible=False)
        ),
        dragmode="pan",
        margin=dict(t=40, b=40, l=40, r=40),
        annotations=[
            dict(
                text="Use scroll/box zoom to explore, drag to rotate",
                x=0.5, y=-0.1,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=12, color="gray")
            )
        ]
    )

    html_path = "static/aspect_plot.html"
    fig.write_html(
        html_path,
        full_html=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": [],
            "modeBarButtonsToAdd": [
                "zoomIn2d", 
                "zoomOut2d", 
                "resetScale2d",
                "pan2d"
            ]
        }
    )
    return f"/{html_path}"

if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(debug=True)