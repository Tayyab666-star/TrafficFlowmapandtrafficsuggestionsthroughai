import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json
from datetime import datetime

# API Keys
GROQ_API_KEY = "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"
HERE_API_KEY = "Z-INy7MKiZwfH6mAchEr0QPFaYuuo5QKqGxSnHxcKTY"

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'location_history' not in st.session_state:
    st.session_state.location_history = []
if 'current_map' not in st.session_state:
    st.session_state.current_map = None

# Page configuration
st.set_page_config(
    page_title="TrafficWise AI Planner",
    page_icon="🚦",
    layout="wide"
)

def geocode_address(address):
    """Convert address to coordinates using HERE Geocoding API"""
    url = f"https://geocode.search.hereapi.com/v1/geocode"
    params = {
        'q': address,
        'apiKey': HERE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['items']:
            position = data['items'][0]['position']
            address_label = data['items'][0].get('address', {}).get('label', address)
            return position['lat'], position['lng'], address_label
        return None, None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None, None

def get_traffic_incidents(lat, lon, radius=1000):
    """Fetch traffic incidents from HERE API"""
    url = "https://data.traffic.hereapi.com/v7/incidents"
    params = {
        'apiKey': HERE_API_KEY,
        'in': f"circle:{lat},{lon};r={radius}",
        'locationReferencing': 'polyline'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # st.warning(f"Note: Traffic data may be limited in this area")
        return None

def generate_traffic_map(center_lat=30.3753, center_lng=69.3451):
    """Generate map with traffic data"""
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
    
    # Add marker for searched location
    folium.Marker(
        [center_lat, center_lng],
        popup="Selected Location",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add traffic incidents if available
    incidents = get_traffic_incidents(center_lat, center_lng)
    if incidents and 'results' in incidents:
        for incident in incidents['results']:
            try:
                # Get incident details
                description = incident.get('description', {}).get('value', 'Traffic Incident')
                severity = incident.get('severity', {}).get('value', 'minor')
                
                # Color based on severity
                color = {
                    'minor': 'green',
                    'moderate': 'orange',
                    'major': 'red'
                }.get(severity, 'blue')
                
                # Get location
                location = incident.get('location', {})
                if 'polyline' in location:
                    coordinates = []
                    points = location['polyline'].get('points', [])
                    for point in points:
                        lat = point.get('lat')
                        lng = point.get('lng')
                        if lat and lng:
                            coordinates.append([lat, lng])
                    
                    if coordinates:
                        # Add incident to map
                        folium.PolyLine(
                            coordinates,
                            color=color,
                            weight=4,
                            opacity=0.8,
                            tooltip=description
                        ).add_to(m)
                        
                        # Add marker at start of incident
                        folium.CircleMarker(
                            coordinates[0],
                            radius=8,
                            color=color,
                            fill=True,
                            popup=description
                        ).add_to(m)
                
            except Exception as e:
                continue
    
    return m

# Sidebar configuration
st.sidebar.title("🚦 TrafficWise AI Planner")
st.sidebar.markdown("Your AI Assistant for Traffic & Urban Planning")

# Previous locations section
if st.session_state.location_history:
    st.sidebar.subheader("Recent Searches")
    for idx, (loc, timestamp) in enumerate(reversed(st.session_state.location_history[-5:])):
        if st.sidebar.button(f"📍 {loc} ({timestamp})", key=f"prev_loc_{idx}"):
            coordinates = geocode_address(loc)
            if coordinates[0]:
                st.session_state.current_map = generate_traffic_map(coordinates[0], coordinates[1])

# Location input
st.sidebar.subheader("Search Location")
location_input = st.sidebar.text_input(
    "Enter city or address:",
    key="location_input",
    placeholder="e.g., London, New York, Tokyo"
)

# Map container
map_container = st.sidebar.container()
map_container.subheader("Traffic Map")

if location_input:
    lat, lng, address_label = geocode_address(location_input)
    if lat and lng:
        # Update location history
        timestamp = datetime.now().strftime("%H:%M")
        if address_label not in [loc for loc, _ in st.session_state.location_history]:
            st.session_state.location_history.append((address_label, timestamp))
        # Generate and store map
        st.session_state.current_map = generate_traffic_map(lat, lng)
        st.sidebar.success(f"📍 Showing Map for: {address_label}")
    else:
        st.sidebar.error("Location not found. Please try another address.")

# Display current map
with map_container:
    if st.session_state.current_map:
        folium_static(st.session_state.current_map, width=300, height=400)
    else:
        folium_static(generate_traffic_map(), width=300, height=400)

# Temperature slider
temperature = st.sidebar.slider(
    "AI Response Variation:",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.1,
    help="Higher values provide more varied suggestions, lower values offer more consistent advice"
)

# Main chat interface
st.title("🚦 TrafficWise AI Planner")
st.markdown("""
### Your AI Assistant for:
- 🚗 Traffic Route Optimization
- 🌆 Urban Congestion Solutions
- 🚦 Traffic Flow Analysis
- 🛣 Infrastructure Planning
""")

def chat_with_traffic_planner(user_message, temperature):
    """Send a message to Groq API's model and return the response."""
    enhanced_prompt = f"""As a traffic and urban planning expert, help with the following question 
    about traffic routes, urban congestion, or city planning: {user_message}
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": enhanced_prompt}],
        "temperature": temperature
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to connect to the API - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def clear_chat():
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    st.markdown(f"👤 You:** {content}" if role == "user" else f"🚦 TrafficWise:** {content}")
    st.markdown("---")

def submit_message():
    if st.session_state.user_input:
        user_message = st.session_state.user_input
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        with st.spinner('Analyzing traffic patterns...'):
            bot_response = chat_with_traffic_planner(user_message, temperature)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        st.session_state.user_input = ""

st.text_input(
    "Ask about traffic routes, urban planning, or congestion solutions...",
    key="user_input",
    on_change=submit_message,
    placeholder="Example: What are the best routes to reduce congestion during peak hours?"
)

if st.button("🗑 Clear Chat"):
    clear_chat()

st.sidebar.markdown("""
### 🚗 Traffic Guidelines:
1. 🕒 Peak Hours
   - Morning: 7-9 AM
   - Evening: 4-7 PM

2. 🚸 Safety First
   - Follow speed limits
   - Watch for pedestrians

3. 🌍 Eco-Friendly Options
   - Consider public transport
   - Use carpooling

4. 🚦 Smart Route Planning
   - Check traffic updates
   - Use alternative routes

5. 📱 Stay Informed
   - Monitor traffic alerts
   - Check weather conditions
""")
