from flask import Flask, render_template, request
import requests  # type: ignore[import]
import random
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

# ==========================================
# API KEYS
# ==========================================
import os
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ORS_API_KEY = os.getenv("ORS_API_KEY")

@app.route("/chat", methods=["POST"])
def chat():
    return {"reply": "Hello"}
# ==========================================
# WEATHER API
# ==========================================

def get_weather(lat, lon):

    if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
        return {
            "temperature": 28.0,
            "condition": "Clear",
            "humidity": 55,
            "risk": "Low"
        }

    try:

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}"
            f"&appid={OPENWEATHER_API_KEY}"
            f"&units=metric"
        )

        response = requests.get(url, timeout=10)

        if response.status_code != 200:

            return {
                "temperature": "N/A",
                "condition": "Unknown",
                "humidity": "N/A",
                "risk": "Unknown"
            }

        data = response.json()

        condition = data["weather"][0]["main"]

        risk_map = {
            "Clear": "Low",
            "Clouds": "Low",
            "Rain": "Medium",
            "Thunderstorm": "High",
            "Drizzle": "Medium",
            "Snow": "Medium"
        }

        return {

            "temperature":
                round(data["main"]["temp"], 1),

            "condition":
                condition,

            "humidity":
                data["main"]["humidity"],

            "risk":
                risk_map.get(
                    condition,
                    "Medium"
                )
        }

    except Exception as error:
        print("Weather lookup failed:", error)
        return {
            "temperature": "N/A",
            "condition": "Unknown",
            "humidity": "N/A",
            "risk": "Unknown"
        }

# ==========================================
# HAVERSINE DISTANCE
# ==========================================

def distance(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c

# ==========================================
# REVERSE GEOCODING
# ==========================================

def get_location_name(lat, lon):

    try:

        url = (
            "https://nominatim.openstreetmap.org/reverse"
        )

        params = {

            "lat": lat,
            "lon": lon,

            "format": "json"
        }

        headers = {
            "User-Agent":
            "LifeLineAI"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        data = response.json()

        return data.get(
            "display_name",
            "Location Unavailable"
        )

    except Exception as error:
        print("Reverse geocode failed:", error)
        return "Location Unavailable"

# ==========================================
# HOSPITAL DISCOVERY
# ==========================================

def get_hospitals(lat, lon):

    overpass_url = (
        "https://overpass-api.de/api/interpreter"
    )

    query = f"""
    [out:json];
    (
      node["amenity"="hospital"]
      (around:10000,{lat},{lon});
    );
    out;
    """

    hospitals = []

    try:

        response = requests.get(

            overpass_url,

            params={
                "data": query
            },

            timeout=20
        )

        data = response.json()

        for item in data["elements"]:

            hospital_name = (
                item.get("tags", {})
                .get("name", "Hospital")
            )

            hospitals.append({

                "name":
                    hospital_name,

                "lat":
                    item["lat"],

                "lon":
                    item["lon"],

                "beds":
                    random.randint(
                        5,
                        60
                    ),

                "score":
                    random.randint(
                        85,
                        99
                    )
            })

    except Exception as error:
        print("Hospital discovery failed:", error)

    return hospitals

# ==========================================
# ROUTE API
# ==========================================

def get_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    if ORS_API_KEY == "YOUR_OPENROUTESERVICE_API_KEY":
        driving_distance = distance(start_lat, start_lon, end_lat, end_lon)
        estimated_duration = round(driving_distance / 50 * 60)
        return {
            "distance": round(driving_distance, 2),
            "duration": max(5, estimated_duration)
        }

    try:

        url = (
            "https://api.openrouteservice.org"
            "/v2/directions/driving-car"
        )

        headers = {

            "Authorization":
                ORS_API_KEY,

            "Content-Type":
                "application/json"
        }

        body = {

            "coordinates": [

                [start_lon, start_lat],

                [end_lon, end_lat]
            ]
        }

        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:

            return {
                "distance": 0,
                "duration": 0
            }

        route = response.json()

        summary = (
            route["routes"][0]
            ["summary"]
        )

        return {

            "distance":
                round(
                    summary["distance"] / 1000,
                    2
                ),

            "duration":
                round(
                    summary["duration"] / 60
                )
        }

    except Exception as error:
        print("Route lookup failed:", error)
        return {

            "distance": 0,

            "duration": 0
        }

# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )
# ==========================================
# EMERGENCY ANALYSIS
# ==========================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        # --------------------------
        # FORM DATA
        # --------------------------

        name = request.form.get("name", "Unknown")

        emergency = request.form.get("emergency", "General Emergency")

        try:
            latitude = float(request.form.get("latitude", ""))
            longitude = float(request.form.get("longitude", ""))
        except ValueError:
            latitude = 17.3850
            longitude = 78.4867

        if latitude == 0 or longitude == 0:
            latitude = 17.3850
            longitude = 78.4867

        # --------------------------
        # LOCATION
        # --------------------------

        location_name = get_location_name(
            latitude,
            longitude
        )

        # --------------------------
        # WEATHER
        # --------------------------

        weather = get_weather(
            latitude,
            longitude
        )

        # --------------------------
        # HOSPITALS
        # --------------------------

        hospitals = get_hospitals(
            latitude,
            longitude
        )

        if len(hospitals) == 0:

            nearest_hospital = {

                "name":
                    "Apollo Hospital",

                "lat":
                    17.4435,

                "lon":
                    78.3772,

                "beds":
                    35,

                "score":
                    95
            }

            top_hospitals = [
                nearest_hospital
            ]

        else:

            hospitals = sorted(

                hospitals,

                key=lambda x:
                distance(

                    latitude,
                    longitude,

                    x["lat"],
                    x["lon"]
                )
            )

            nearest_hospital = hospitals[0]

            top_hospitals = hospitals[:10]

        # --------------------------
        # ROUTE
        # --------------------------

        route = get_route(

            latitude,
            longitude,

            nearest_hospital["lat"],
            nearest_hospital["lon"]
        )

        # --------------------------
        # AMBULANCES
        # --------------------------

        ambulances = []

        for i in range(1, 8):

            ambulances.append({

                "id":
                    f"AMB-{100+i}",

                "lat":
                    latitude +
                    random.uniform(
                        -0.02,
                        0.02
                    ),

                "lon":
                    longitude +
                    random.uniform(
                        -0.02,
                        0.02
                    ),

                "eta":
                    random.randint(
                        3,
                        10
                    ),

                "status":
                    "Available"
            })

        nearest_ambulance = min(

            ambulances,

            key=lambda x:
            x["eta"]
        )

        # --------------------------
        # PRIORITY ENGINE
        # --------------------------

        priorities = {

            "Heart Attack":
                "CRITICAL",

            "Stroke":
                "CRITICAL",

            "Accident":
                "HIGH",

            "Burn Injury":
                "HIGH",

            "General Emergency":
                "MEDIUM"
        }

        severity_scores = {

            "Heart Attack": 100,

            "Stroke": 95,

            "Accident": 85,

            "Burn Injury": 80,

            "General Emergency": 60
        }

        priority = priorities.get(
            emergency,
            "MEDIUM"
        )

        severity = severity_scores.get(
            emergency,
            50
        )

        # --------------------------
        # SOS ID
        # --------------------------

        sos_id = (

            "SOS-IND-"

            +

            str(

                random.randint(
                    100000,
                    999999
                )
            )
        )

        # --------------------------
        # READINESS SCORE
        # --------------------------

        readiness_score = min(

            100,

            severity +

            random.randint(
                -8,
                5
            )
        )

        # --------------------------
        # HOSPITAL SCORE
        # --------------------------

        hospital_score = (
            nearest_hospital["score"]
        )

        # --------------------------
        # AI COPILOT
        # --------------------------

        ai_guidance = {

            "Heart Attack": [

                "Call emergency services immediately",

                "Keep patient seated",

                "Loosen tight clothing",

                "Monitor breathing",

                "Share GPS location"
            ],

            "Stroke": [

                "Keep patient calm",

                "Avoid food or water",

                "Monitor symptoms",

                "Call emergency services"
            ],

            "Accident": [

                "Control bleeding",

                "Do not move patient",

                "Keep airway clear",

                "Wait for ambulance"
            ],

            "Burn Injury": [

                "Cool affected area",

                "Avoid applying ice",

                "Cover burn gently",

                "Seek medical help"
            ],

            "General Emergency": [

                "Stay calm",

                "Contact nearest healthcare provider"
            ]
        }

        guidance = ai_guidance.get(
            emergency,
            []
        )

        # --------------------------
        # TIMELINE
        # --------------------------

        timeline = [

            "SOS Request Generated",

            "GPS Location Identified",

            "Hospitals Retrieved",

            "Ambulance Assigned",

            "Route Calculated",

            "Emergency Response Active"
        ]

        # --------------------------
        # NATIONAL METRICS
        # --------------------------

        hospitals_connected = "50,000+"

        ambulances_connected = "3,200+"

        states_covered = "28"

    # --------------------------
    # RENDER
    # --------------------------

        return render_template(

            "result.html",

            name=name,

            emergency=emergency,

            location_name=location_name,

            priority=priority,

            severity=severity,

            sos_id=sos_id,

            weather=weather,

            route=route,

            hospital=nearest_hospital,

            hospital_score=hospital_score,

            top_hospitals=top_hospitals,

            ambulances=ambulances,

            ambulance=nearest_ambulance,

            readiness_score=readiness_score,

            guidance=guidance,

            timeline=timeline,

            hospitals_connected=
                hospitals_connected,

            ambulances_connected=
                ambulances_connected,

            states_covered=
                states_covered,

            user_lat=latitude,

            user_lon=longitude
        )

    except Exception as error:
        print("Predict function error:", error)
        return render_template(
            "result.html",
            name="Emergency",
            emergency="General Emergency",
            location_name="Location Unavailable",
            priority="MEDIUM",
            severity=50,
            sos_id="SOS-IND-ERROR",
            weather={"temperature": "N/A", "condition": "Unknown", "humidity": "N/A", "risk": "Unknown"},
            route={"distance": 0, "duration": 0},
            hospital={"name": "Nearest Hospital", "lat": 17.3850, "lon": 78.4867, "beds": 0, "score": 0},
            hospital_score=0,
            top_hospitals=[],
            ambulances=[],
            ambulance={"id": "AMB-ERROR", "eta": 0, "status": "Unavailable"},
            readiness_score=0,
            guidance=[],
            timeline=[],
            hospitals_connected="N/A",
            ambulances_connected="N/A",
            states_covered="N/A",
            user_lat=17.3850,
            user_lon=78.4867
        ), 500

# ==========================================
# RUN APP
# ==========================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000
    )