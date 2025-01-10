import os
import platform
import re
from datetime import datetime

from flask import Flask, jsonify, render_template, request
import plotly.graph_objects as go

import natal_chart
import transit_waveforms
import openaiApi #gpt implemented

app = Flask(__name__)

# -----------------------------------------------------------
#   Planets, Signs, Aspects
# -----------------------------------------------------------
planets = [
    "Jupiter", "Mars", "Mercury", "Moon", "Neptune",
    "Pluto", "Saturn", "Sun", "Uranus", "Venus"
]
zodiac_signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

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

# -----------------------------------------------------------
#   Home / Index
# -----------------------------------------------------------
@app.route("/")
def index():
    """
    Renders the main page (templates/index.html).
    """
    return render_template("index.html", planets=planets, aspects=aspects.keys())

# -----------------------------------------------------------
#   Natal Chart
# -----------------------------------------------------------
@app.route("/calculate_natal_chart", methods=["POST"])
def calculate_chart():
    data = request.json
    if not data:
        return jsonify({"error": "Missing or invalid JSON data"}), 400

    dob = data.get("dob")
    tob = data.get("tob")
    chart_name = data.get("chartName")

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "Missing geographic information"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
        chart = natal_chart.calculate_natal_chart(dob, tob, lat, lon)
        return jsonify({"success": True, "chart": chart, "chartName": chart_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
#   Aspect Plot (Natal, writes HTML for <iframe>)
# -----------------------------------------------------------
@app.route("/generate_plot", methods=["POST"])
def generate_plot():
    """
    Creates a static HTML file with the aspect wheel for natal positions.
    The front-end places it in an <iframe>, keeping your old design.
    """
    try:
        data = request.json
        positions = data.get("positions")
        selected_aspects = data.get("aspects", [])

        # Convert position strings to decimal degrees
        for planet, pos_str in positions.items():
            positions[planet] = convert_to_degrees(pos_str)

        # Generate the aspect wheel chart as an HTML file
        aspect_plot_url = generate_aspect_plot(positions, selected_aspects)

        return jsonify({"plot_url": aspect_plot_url})
    except Exception as e:
        print(f"Error in /generate_plot: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
#   Waveforms (No Iframe) -> Return Plotly Figure JSON
# -----------------------------------------------------------
@app.route("/generate_waveforms_data", methods=["POST"])
def generate_waveforms_data():
    """
    Returns JSON for Plotly (data + layout) plus the raw transits list.
    The front-end will embed it in a <div> via Plotly.newPlot(...).
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        natal_chart_positions = data.get("natal_chart")
        start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")
        end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d")
        selected_transiting_planets = data.get("transiting_planets", [])
        selected_aspects = data.get("aspects", [])
        template = data.get("template", "plotly_dark")

        # Convert natal chart positions from strings to degrees
        natal_positions = {}
        for planet, pos_str in natal_chart_positions.items():
            natal_positions[planet] = convert_to_degrees(pos_str)

        # Calculate waveforms
        transits = transit_waveforms.calculate_transit_waveforms(
            natal_positions, start_date, end_date,
            selected_transiting_planets, selected_aspects
        )

        # Build a figure dict for direct Plotly usage
        fig_dict = transit_waveforms.build_waveform_figure_dict(
            transits, start_date, end_date, template
        )

        return jsonify({
            "figure": fig_dict,  # { "data": [...], "layout": {...} }
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
        print(f"Error in /generate_waveforms_data: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
#   Single-Date Aspect Snapshot (No Iframe) -> Return JSON
# -----------------------------------------------------------
@app.route("/snapshot_aspect_chart_data", methods=["POST"])
def snapshot_aspect_chart_data():
    """
    Generates an aspect wheel for a single date/time (at noon).
    On a waveforms click, we show the same "old design" in a modal,
    but returned as JSON for direct Plotly usage.
    """
    try:
        data = request.json
        if not data or "date" not in data:
            return jsonify({"error": "Missing 'date'"}), 400

        date_str = data["date"]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Arbitrary time: noon
        dt = dt.replace(hour=12, minute=0)

        # Compute positions in degrees
        positions_deg = {}
        for p in planets:
            positions_deg[p] = natal_chart.get_transit_position(dt, p)

        # Build the aspect wheel figure in JSON, but with your original radial design
        # -> We'll use the same style from generate_aspect_plot, just returning JSON instead of HTML.
        fig_data = build_aspect_wheel_figure_dict(positions_deg, list(aspects.keys()))

        return jsonify({"figure": fig_data})
    except Exception as e:
        print(f"Error in /snapshot_aspect_chart_data: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
#   GPT Analysis Route
# -----------------------------------------------------------
@app.route("/analyze_waveforms", methods=["POST"])
def analyze_waveforms():
    """
    Receives waveforms (or any other data) from the frontend,
    calls GPT for an analysis, and returns the analysis text.
    """
    try:
        data = request.json
        if not data or "waveforms_text" not in data:
            return jsonify({"error": "No 'waveforms_text' field provided."}), 400

        waveforms_text = data["waveforms_text"]
        result = openaiApi.analyze_data_with_gpt(waveforms_text)
        print("[/analyze_waveforms] GPT analysis result:", result)
        return jsonify({"analysis": result}), 200
    except Exception as e:
        print("[/analyze_waveforms] Error:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
#   Helper Functions
# -----------------------------------------------------------
def convert_to_degrees(position):
    """
    Convert "20° 30' 10\" Aries" -> decimal degrees.
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
        deg = float(match.group(1))
        minutes = float(match.group(2)) if match.group(2) else 0.0
        seconds = float(match.group(3)) if match.group(3) else 0.0
        sign = match.group(4).capitalize()

        total_deg = deg + minutes/60.0 + seconds/3600.0
        if sign not in zodiac_signs:
            raise ValueError(f"Invalid zodiac sign: '{sign}' in '{position}'")
        sign_index = zodiac_signs.index(sign)
        return total_deg + sign_index*30
    else:
        raise ValueError(f"Invalid position format: '{position}'")

def generate_aspect_plot(positions_deg, selected_aspects):
    """
    This is your old code that writes a static HTML file for 'aspect_plot.html' 
    used by the natal chart <iframe>. 
    (We keep it unchanged so the natal chart has the same design as always.)
    """
    fig = go.Figure()

    # EXACT style logic as your old code:
    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    sign_angles = [(i * degrees_per_sign + degrees_per_sign / 2) for i in range(num_signs)]

    # zodiac boundaries
    for i in range(num_signs):
        boundary_angle = i * 30
        fig.add_trace(go.Scatterpolar(
            r=[0, 1.2],
            theta=[boundary_angle, boundary_angle],
            mode="lines",
            line=dict(color="#333", width=0.6, dash="dot"),
            showlegend=False,
            hoverinfo="none"
        ))

    # zodiac labels
    for angle, sign in zip(sign_angles, zodiac_signs):
        fig.add_trace(go.Scatterpolar(
            r=[1.15],
            theta=[angle],
            mode="text",
            text=[sign],
            textfont=dict(size=12, color="#333"),
            showlegend=False,
            hoverinfo="none"
        ))

    # aspect lines
    for planet1, angle1 in positions_deg.items():
        for planet2, angle2 in positions_deg.items():
            if planet1 < planet2:
                difference = abs(angle1 - angle2)
                if difference > 180:
                    difference = 360 - difference
                for asp_name in selected_aspects:
                    aspect_angle = aspects[asp_name]
                    if abs(difference - aspect_angle) <= orb[asp_name]:
                        color = aspect_colors.get(asp_name, "cyan")
                        fig.add_trace(go.Scatterpolar(
                            r=[1, 1],
                            theta=[angle1, angle2],
                            mode="lines",
                            line=dict(color=color, width=1),
                            name=f"{planet1}-{asp_name}-{planet2}",
                            hoverinfo="skip"
                        ))

    # planet glyphs
    planet_r = []
    planet_theta = []
    planet_text = []
    for planet, deg in positions_deg.items():
        planet_r.append(1.0)
        planet_theta.append(deg)
        planet_text.append(planet_symbols.get(planet, planet))

    fig.add_trace(go.Scatterpolar(
        r=planet_r,
        theta=planet_theta,
        mode="markers+text",
        text=planet_text,
        textposition="middle center",
        marker=dict(size=18, color="black", line=dict(color='#ffdead', width=1)),
        textfont=dict(size=12, color="#ffdead"),
        showlegend=False
    ))

    fig.update_layout(
        template="plotly_dark",
        polar=dict(
            angularaxis=dict(
                showgrid=True,
                linecolor="#333",
                gridcolor="gray",
                linewidth=0.5,
                showline=True,
                tickmode="array",
                tickvals=[],
                ticktext=[]
            ),
            radialaxis=dict(visible=False)
        ),
        margin=dict(t=40, b=40, l=40, r=40),
    )

    if not os.path.exists("static"):
        os.makedirs("static")
    html_path = "static/aspect_plot.html"
    fig.write_html(html_path)
    return f"/{html_path}"




def build_aspect_wheel_figure_dict(positions_deg, selected_aspects):
    """
    Recreates the same radial design as 'generate_aspect_plot', 
    but returns JSON for direct Plotly usage (no <iframe>).
    """
    fig = go.Figure()

    num_signs = len(zodiac_signs)
    degrees_per_sign = 360 / num_signs
    sign_angles = [(i * degrees_per_sign + degrees_per_sign / 2) for i in range(num_signs)]

    # boundaries
    for i in range(num_signs):
        boundary_angle = i * 30
        fig.add_trace(go.Scatterpolar(
            r=[0, 1.2],
            theta=[boundary_angle, boundary_angle],
            mode="lines",
            line=dict(color="#333", width=0.6, dash="dot"),
            showlegend=False,
            hoverinfo="none"
        ))

    # zodiac labels
    for angle, sign in zip(sign_angles, zodiac_signs):
        fig.add_trace(go.Scatterpolar(
            r=[1.15],
            theta=[angle],
            mode="text",
            text=[sign],
            textfont=dict(size=12, color="#333"),
            showlegend=False,
            hoverinfo="none"
        ))

    # aspect lines
    for planet1, angle1 in positions_deg.items():
        for planet2, angle2 in positions_deg.items():
            if planet1 < planet2:
                difference = abs(angle1 - angle2)
                if difference > 180:
                    difference = 360 - difference
                for asp_name in selected_aspects:
                    aspect_angle = aspects[asp_name]
                    if abs(difference - aspect_angle) <= orb[asp_name]:
                        color = aspect_colors.get(asp_name, "cyan")
                        fig.add_trace(go.Scatterpolar(
                            r=[1, 1],
                            theta=[angle1, angle2],
                            mode="lines",
                            line=dict(color=color, width=1),
                            name=f"{planet1}-{asp_name}-{planet2}",
                            hoverinfo="skip"
                        ))

    # planet glyphs
    planet_r = []
    planet_theta = []
    planet_text = []
    for planet, deg in positions_deg.items():
        planet_r.append(1.0)
        planet_theta.append(deg)
        planet_text.append(planet_symbols.get(planet, planet))

    fig.add_trace(go.Scatterpolar(
        r=planet_r,
        theta=planet_theta,
        mode="markers+text",
        text=planet_text,
        textposition="middle center",
        marker=dict(size=18, color="black", line=dict(color='#ffdead', width=1)),
        textfont=dict(size=12, color="#ffdead"),
        showlegend=False
    ))

    fig.update_layout(
        template="plotly_dark",
        polar=dict(
            angularaxis=dict(
                showgrid=True,
                linecolor="#333",
                gridcolor="gray",
                linewidth=0.5,
                showline=True,
                tickmode="array",
                tickvals=[],
                ticktext=[]
            ),
            radialaxis=dict(visible=False)
        ),
        margin=dict(t=40, b=40, l=40, r=40),
    )

    return {
        "data": [trace.to_plotly_json() for trace in fig.data],
        "layout": fig.layout.to_plotly_json()
    }




@app.route("/synastry_aspect_chart_data", methods=["POST"])
def synastry_aspect_chart_data():
    """
    A route that takes:
      { "date": "2025-01-15",
        "natal_chart_text": {"Sun":"20° 12' ... Aries", "Moon":"12° 03' ... Taurus", ...},
        "selected_aspects": ["Conjunction","Opposition","Trine","Square","Sextile"]
      }
    Then re-converts the natal text to degrees, 
    calculates the date positions in degrees,
    and draws only natal↔date lines.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data"}), 400

        date_str = data["date"]
        natal_chart_text = data["natal_chart_text"] 
        selected_aspects = data["selected_aspects"]

        # 1) Convert the natal text to degrees
        natal_positions_deg = {}
        for planet, pos_str in natal_chart_text.items():
            natal_positions_deg[planet] = convert_to_degrees(pos_str)  # reuse your function

        # 2) Convert date_str -> datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(hour=12, minute=0)

        # 3) Calculate the date positions
        date_positions_deg = {}
        for p in planets:
            date_positions_deg[p] = natal_chart.get_transit_position(dt, p)

        # 4) Build synergy chart
        fig_data = build_synastry_wheel(natal_positions_deg, date_positions_deg, selected_aspects)
        return jsonify({"figure": fig_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def build_synastry_wheel(natal_positions, date_positions, selected_aspects):
    """
    Show lines in the legend (one line = one legend item),
    but hide the planet markers from the legend so they're always visible.
    """
    fig = go.Figure()

    # 1) Draw zodiac boundaries (off the legend)
    num_signs = 12
    for i in range(num_signs):
        angle = i * 30
        fig.add_trace(go.Scatterpolar(
            r=[0, 1.2],
            theta=[angle, angle],
            mode="lines",
            line=dict(color="#333", width=0.6, dash="dot"),
            showlegend=False,    # do not include in legend
            hoverinfo="none"
        ))

    # 2) Add aspect lines for natal↔date
    #    Each line is its own legend item, toggled individually.
    for nat_planet, nat_deg in natal_positions.items():
        for date_planet, date_deg in date_positions.items():
            diff = abs(nat_deg - date_deg)
            if diff > 180:
                diff = 360 - diff
            for asp_name in selected_aspects:
                aspect_angle = aspects[asp_name]
                if abs(diff - aspect_angle) <= orb[asp_name]:
                    color = aspect_colors.get(asp_name, "cyan")
                    fig.add_trace(go.Scatterpolar(
                        r=[1, 0.8],               # radius for lines
                        theta=[nat_deg, date_deg],
                        mode="lines",
                        line=dict(color=color, width=1),
                        name=f"{nat_planet} {asp_name} {date_planet}",
                        showlegend=True,         # lines appear in legend
                        hoverinfo="none"
                    ))

    # 3) Plot natal planets (no legend entry -> always visible)
    natal_r = []
    natal_theta = []
    natal_text = []
    for p, deg in natal_positions.items():
        natal_r.append(1.0)
        natal_theta.append(deg)
        natal_text.append(planet_symbols.get(p, p))
    fig.add_trace(go.Scatterpolar(
        r=natal_r,
        theta=natal_theta,
        mode="markers+text",
        text=natal_text,
        textposition="middle center",
        marker=dict(size=18, color="black", line=dict(color="#ffdead", width=1)),
        textfont=dict(size=12, color="#ffdead"),
        showlegend=False,      # hide from legend
        hoverinfo="text"
    ))

    # 4) Plot date planets (no legend entry -> always visible)
    date_r = []
    date_theta = []
    date_text = []
    for p, deg in date_positions.items():
        date_r.append(0.8)
        date_theta.append(deg)
        date_text.append(planet_symbols.get(p, p))
    fig.add_trace(go.Scatterpolar(
        r=date_r,
        theta=date_theta,
        mode="markers+text",
        text=date_text,
        textposition="middle center",
        marker=dict(size=14, color="blue", line=dict(color="#ddd", width=1)),
        textfont=dict(size=12, color="#ffdead"),
        showlegend=False,      # hide from legend
        hoverinfo="text"
    ))

    # 5) Configure legend for "line-by-line" toggling
    fig.update_layout(
        template="plotly_dark",
        showlegend=True,    # We do want lines to appear in the legend
        legend=dict(
            x=1.05,
            y=1.0,
            bordercolor="#666",
            borderwidth=1,
            font=dict(color="#ffdead"),
            # Key: ensures each line toggles individually, not grouped
            groupclick="toggleitem"
        ),
        margin=dict(t=40, b=40, l=40, r=90),
        polar=dict(
            radialaxis=dict(visible=False),
            angularaxis=dict(showgrid=True, gridcolor="#444")
        )
    )

    return {
        "data": [trace.to_plotly_json() for trace in fig.data],
        "layout": fig.layout.to_plotly_json()
    }

if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(debug=True)
