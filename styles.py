import streamlit as st

def apply_vox_theme():
    st.markdown("""
        <style>
        .main {
            background-color: #111111;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        h1, h2, h3 {
            color: #FFFFFF;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        /* Style Streamlit Metric Cards for High Contrast */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            padding: 20px 24px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            border-left: 5px solid #FF3366;
            border-top: 1px solid #E5E5EA;
            border-right: 1px solid #E5E5EA;
            border-bottom: 1px solid #E5E5EA;
        }
        /* Metric Label (e.g., Filtered Cohort Size) */
        div[data-testid="stMetric"] label {
            color: #666666 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        /* Metric Value Number (e.g., 160,000 / $169.81) */
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #111111 !important;
            font-size: 32px !important;
            font-weight: 800 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #141414;
            color: #FFFFFF;
        }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stMarkdown {
            color: #E5E5EA !important;
        }
        </style>
    """, unsafe_allow_html=True)