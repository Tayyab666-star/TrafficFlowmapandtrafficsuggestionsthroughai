import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json

# Pre-configured API key
GROQ_API_KEY = "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"

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize session state for user input
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

# Page configuration
st.set_page_config(
    page_title="TrafficWise Urban Planner",
    page_icon="🚦",
    layout="wide"
)

# Sidebar configuration
st.sidebar.title("🚦 TrafficWise Urban Planner")
st.sidebar.markdown("Your AI Assistant for Traffic & Urban Planning")

# Temperature slider
temperature = st.sidebar.slider(
    "AI Response Variation:",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.1,
    help="Higher values provide more varied suggestions, lower values offer more consistent advice"
)

# Map toggle
show_map = st.sidebar.checkbox("Show Traffic Map")

# Define the map function
def generate_traffic_map():
    m = folium.Map(location=[30.3753, 69.3451], zoom_start=6)
    
    # List of major cities in Pakistan with simulated traffic congestion
    traffic_points = [
        {"city": "Lahore", "lat": 31.5204, "lon": 74.3587, "color": "red"},
        {"city": "Karachi", "lat": 24.8607, "lon": 67.0011, "color": "blue"},
        {"city": "Islamabad", "lat": 33.6844, "lon": 73.0479, "color": "green"},
        {"city": "Peshawar", "lat": 34.0151, "lon": 71.5249, "color": "orange"},
        {"city": "Faisalabad", "lat": 31.4504, "lon": 73.1350, "color": "purple"},
    ]
    
    for point in traffic_points:
        folium.Marker(
            [point["lat"], point["lon"]],
            tooltip=f"{point['city']} Traffic",
            icon=folium.Icon(color=point["color"])
        ).add_to(m)
    
    return m

if show_map:
    st.sidebar.subheader("Live Traffic Map")
    folium_static(generate_traffic_map())

# Main chat interface
st.title("🚦 TrafficWise Urban Planner")
st.markdown("""
### Your AI Assistant for:
- 🚗 Traffic Route Optimization
- 🌆 Urban Congestion Solutions
- 🚦 Traffic Flow Analysis
- 🛣️ Infrastructure Planning
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
    st.markdown(f"**👤 You:** {content}" if role == "user" else f"**🚦 TrafficWise:** {content}")
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

if st.button("🗑️ Clear Chat"):
    clear_chat()

st.sidebar.markdown("""
### 🚗 Traffic Guidelines:
1. 🕒 **Peak Hours**
   - Morning: 7-9 AM
   - Evening: 4-7 PM

2. 🚸 **Safety First**
   - Follow speed limits
   - Watch for pedestrians

3. 🌍 **Eco-Friendly Options**
   - Consider public transport
   - Use carpooling

4. 🚦 **Smart Route Planning**
   - Check traffic updates
   - Use alternative routes

5. 📱 **Stay Informed**
   - Monitor traffic alerts
   - Check weather conditions
""")
