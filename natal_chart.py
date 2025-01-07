# natal_chart.py
import swisseph as swe
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder

def degrees_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = (deg - d - m/60) * 3600
    return f"{d}° {m}' {s:.4f}\""

def degrees_to_zodiac(deg):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = int(deg // 30) % 12
    sign = signs[sign_index]
    pos_in_sign = deg % 30
    return f"{degrees_to_dms(pos_in_sign)} {sign}"

def get_local_timezone(lat, lon):
    """
    Attempt to find the local time zone based on lat/lon using TimezoneFinder.
    If you don't want to do this, skip this step.
    """
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=lat, lng=lon)
    if not tz_str:
        # fallback if time zone isn't found
        return "UTC"
    return tz_str

def calculate_natal_chart(dob, tob, lat, lon):
    """
    1) Convert local date/time to UTC using lat/lon-based time zone
    2) Convert that UTC time to Julian day
    3) Use swe.set_topo(lon, lat, alt=0) for topocentric
    4) Return planet positions in ecliptic longitudes as text
    """
    # 0) parse input date/time as a naive datetime
    dt_str = f"{dob} {tob}"  # e.g. "2024-05-10 13:30"
    local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    # 1) Figure out time zone from lat/lon
    tz_str = get_local_timezone(lat, lon)
    local_tz = pytz.timezone(tz_str)
    # 2) localize
    local_dt = local_tz.localize(local_dt)
    # 3) convert to UTC
    utc_dt = local_dt.astimezone(pytz.utc)

    # 4) compute Julian day from the UTC datetime
    julday = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                        utc_dt.hour + utc_dt.minute/60.0)

    # 5) topocentric
    swe.set_topo(lon, lat, 0)

    # 6) compute planet positions
    bodies = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
        'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN,
        'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO
    }

    positions = {}
    for name, code in bodies.items():
        pos, _ = swe.calc_ut(julday, code)
        positions[name] = degrees_to_zodiac(pos[0])

    return positions

def get_transit_position(date, planet_name, lat=None, lon=None):
    """
    Return planet ecliptic longitude in degrees for a given date.
    Optionally can do topocentric if lat/lon are provided.
    If you also need local time -> UTC, do it outside or within this function.
    """
    planet_mapping = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
        "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
        "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    if planet_name not in planet_mapping:
        raise ValueError("Unknown planet: " + planet_name)

    # If we want topocentric, set it
    if lat is not None and lon is not None:
        swe.set_topo(lon, lat, 0)

    # If `date` is local, you might want to do a time zone conversion here
    # For simplicity, assume date is UTC
    jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)
    pos, _ = swe.calc_ut(jd, planet_mapping[planet_name])
    return pos[0]
