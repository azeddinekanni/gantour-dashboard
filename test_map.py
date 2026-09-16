import streamlit as st
import style

st.set_page_config(layout="wide")
st.title("Test carte")

sites_data = [
    {"name": "Benguerir", "production": 1000, "cost": 45.5},
    {"name": "Mzinda", "production": 800, "cost": 50.2},
    {"name": "Bouchane", "production": 1200, "cost": 42.1},
]
style.national_value_chain_map(sites_data)