import streamlit as st

def apply_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');
        
        /* Global Background & Font */
        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            font-family: 'Outfit', sans-serif;
            color: white;
        }

        /* Hero Typography */
        .hero-title {
            font-size: 4.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0px;
            background: -webkit-linear-gradient(#60a5fa, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -2px;
        }

        .hero-subtitle {
            font-size: 1.4rem;
            text-align: center;
            color: #94a3b8;
            margin-bottom: 40px;
            font-weight: 300;
        }

        /* Glass Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 30px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }

        /* Premium Uploader */
        .stFileUploader section {
            background-color: rgba(59, 130, 246, 0.05) !important;
            border: 2px dashed #3b82f6 !important;
            border-radius: 20px !important;
            padding: 40px !important;
        }

        /* Animated Button */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            border-radius: 15px;
            color: white;
            padding: 15px 30px;
            font-weight: 700;
            font-size: 1.1rem;
            transition: 0.4s ease;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }
        div.stButton > button:first-child:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.5);
        }
        </style>
    """, unsafe_allow_html=True)