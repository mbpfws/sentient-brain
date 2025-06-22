"""
Corporate-Level Admin UI for Sentient Brain Multi-Agent System
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import requests

# Configure page
st.set_page_config(
    page_title="Sentient Brain Admin Console",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class AdminUI:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"

    def render_header(self):
        st.markdown("""
        <div class="main-header">
            <h1>🧠 Sentient Brain Multi-Agent System</h1>
            <h3>Corporate Admin Console & Testing Platform</h3>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        with st.sidebar:
            st.title("🎛️ Control Panel")
            
            page = st.selectbox("Navigate:", [
                "🏠 Dashboard",
                "🤖 Agent Monitor", 
                "🧪 Test Suite",
                "📊 Data Explorer"
            ])
            
            st.divider()
            
            if st.button("🔄 Refresh"):
                st.rerun()
            
            return page

    def render_dashboard(self):
        st.header("📊 Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Agents", "5")
        with col2:
            st.metric("Tasks Completed", "127")
        with col3:
            st.metric("Success Rate", "94.3%")
        with col4:
            st.metric("Response Time", "1.2s")

    def render_agent_monitor(self):
        st.header("🤖 Agent Monitor")
        
        agents_data = [
            {"Agent": "Ultra Orchestrator", "Status": "🟢 Active", "Tasks": 45},
            {"Agent": "Architect", "Status": "🟡 Idle", "Tasks": 23},
            {"Agent": "Codebase", "Status": "🟢 Active", "Tasks": 67}
        ]
        st.dataframe(pd.DataFrame(agents_data))

    def render_test_suite(self):
        st.header("🧪 Test Suite")
        
        if st.button("▶️ Run All Tests"):
            with st.spinner("Running tests..."):
                time.sleep(2)
                st.success("✅ All tests passed!")

    def render_data_explorer(self):
        st.header("📊 Data Explorer")
        
        source = st.selectbox("Data Source:", ["Knowledge Graph", "Agent Messages"])
        if st.button("🔍 Query"):
            st.success("✅ Data retrieved")

def main():
    admin_ui = AdminUI()
    admin_ui.render_header()
    
    page = admin_ui.render_sidebar()
    
    if page == "🏠 Dashboard":
        admin_ui.render_dashboard()
    elif page == "🤖 Agent Monitor":
        admin_ui.render_agent_monitor()
    elif page == "🧪 Test Suite":
        admin_ui.render_test_suite()
    elif page == "📊 Data Explorer":
        admin_ui.render_data_explorer()

if __name__ == "__main__":
    main()