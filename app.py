import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.express as px
import json
import re
from supabase import create_client, Client
from style import apply_custom_style


# ---------------- CONFIG ---------------- #

st.set_page_config(
    page_title="Health Guardian Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_custom_style()


# ---------------- CLOUD SETUP ---------------- #

SUPABASE_URL = "https://ftiodsdwwcgpowcwpvrz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ0aW9kc2R3d2NncG93Y3dwdnJ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyOTUxMTAsImV4cCI6MjA4ODg3MTExMH0.Eci7aNLoxtgMwn2fOP_Cpm1yLJCpDarrG6Q7hELNCyQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------- AI SETUP ---------------- #

genai.configure(api_key="AIzaSyBb-oRhu8w0oMEUVBbmcwe9f2ux_OU3FdE")
model = genai.GenerativeModel("gemini-3-flash-preview")
# --- NLP PARSER PROMPT ---
CLINICAL_PARSER_PROMPT = """
You are a clinical data extraction AI.
Given a natural language health log entry, extract structured data.
User input: {user_text}

Return ONLY valid JSON. No preamble. No explanation. No markdown.
{{
  "intake": [
    {{
      "item_type": "food or hydration or caffeine or alcohol or meds",
      "item_name": "name of the item",
      "quantity_g": null,
      "calories": null,
      "carbs_g": null,
      "protein_g": null,
      "fats_g": null,
      "sodium_mg": null,
      "caffeine_mg": null
    }}
  ],
  "symptoms": [
        {{
      "symptom_type": "name of symptom",
      "severity_estimate": null,
      "notes": "any extra context"
    }}
  ],
  "confidence": "high or medium or low",
  "clarification_needed": null
}}
"""




# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------------- HELPER FUNCTIONS ---------------- #

def log_to_supabase(username, nutrient_data):
    try:
        data = {
            "username": username,
            "nutrient_data": nutrient_data
        }
        supabase.table("consumption_logs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Cloud Sync Error: {e}")
        return False
def parse_health_log(user_text):
    prompt = CLINICAL_PARSER_PROMPT.format(user_text=user_text)
    response = model.generate_content(prompt)
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return None


def analyze_food_label(image):
    prompt = """
    Analyze this food label.

    Use a candid and direct tone.
    Avoid technical jargon.

    Format:
    1. The Verdict (2 sentences)
    2. Red Flags
    3. Healthier Alternative

    Provide nutrient data exactly like:

    DATA: {"Carbs":40,"Protein":20,"Fats":40,"Context":"Nearly half your daily sugar limit."}
    """

    response = model.generate_content([prompt, image])
    full_text = response.text

    match = re.search(r'DATA:\s*({.*?})', full_text, re.DOTALL)

    if match:
        data = json.loads(match.group(1))
        clean_text = full_text.split("DATA:")[0]
        return clean_text, data

    return full_text, None


def create_nutrient_chart(data):

    df = pd.DataFrame([
        {"Nutrient": "Carbs", "Value": data["Carbs"]},
        {"Nutrient": "Protein", "Value": data["Protein"]},
        {"Nutrient": "Fats", "Value": data["Fats"]}
    ])

    fig = px.pie(
        df,
        values="Value",
        names="Nutrient",
        hole=0.5,
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )

    fig.update_traces(
        pull=[0.1, 0.1, 0.1],
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Value: %{value}%<br><i>" + data["Context"] + "</i>"
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=30, b=30, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)"
    )

    return fig


# ---------------- AUTH ---------------- #

if not st.session_state.logged_in:

    st.markdown("<h1 style='text-align:center;'>Health Guardian</h1>", unsafe_allow_html=True)

    auth_mode = st.radio("Access Level", ["Login", "Sign Up"], horizontal=True)

    with st.columns([1,1,1])[1]:
        with st.form("auth_form"):

            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Proceed")

            if submit:

                if auth_mode == "Sign Up":

                    existing = supabase.table("users").select("*").eq("username", username).execute()

                    if len(existing.data) > 0:
                        st.error("Username already taken")

                    else:
                        supabase.table("users").insert({
                            "username": username,
                            "password": password
                        }).execute()

                        st.success("Account created. Switch to login.")

                else:

                    res = supabase.table("users")\
                        .select("*")\
                        .eq("username", username)\
                        .eq("password", password)\
                        .execute()

                    if len(res.data) > 0:

                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()

                    else:
                        st.error("Invalid credentials")

    st.stop()


# ---------------- MAIN APP ---------------- #

tab1, tab2, tab3 = st.tabs(["🔍 AI Scanner", "📝 Log by Text", "📊 Health Dashboard"])


# -------- SCANNER -------- #

with tab1:

    st.markdown(f"### User: {st.session_state.username}")

    col1, col2 = st.columns([1,1.2], gap="large")

    with col1:

        uploaded_file = st.file_uploader(
            "Upload food label",
            type=["jpg","jpeg","png"]
        )

        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, use_container_width=True)

    with col2:

        if uploaded_file:

            with st.spinner("Analyzing label..."):

                try:

                    text, data = analyze_food_label(img)

                    st.markdown(
                        f"""
                        <div style="
                        background: rgba(255,255,255,0.05);
                        padding:25px;
                        border-radius:15px;
                        border-left:5px solid #3b82f6;">
                        {text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if data:

                        fig = create_nutrient_chart(data)
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("---")

                        if st.button("Log this to profile"):

                            if log_to_supabase(st.session_state.username, data):
                                st.success("Log saved")
                                st.balloons()

                except Exception:
                    st.error("Analysis failed")


# -------- DASHBOARD -------- #

with tab2:
    st.markdown("### 📝 Log Your Intake by Text")
    st.markdown("Describe what you ate, drank, or how you feel in plain language.")
    
    user_log_input = st.text_area(
        "What did you eat or drink? How do you feel?",
        placeholder="e.g. Had 2 parathas with butter and a strong espresso. Feeling a bit bloated and jittery.",
        height=120
    )
    
    if st.button("🧠 Parse & Preview"):
        if user_log_input.strip():
            with st.spinner("Extracting clinical data..."):
                parsed = parse_health_log(user_log_input)
                if parsed:
                    st.session_state['nlp_parsed'] = parsed
                                        st.markdown("**Extracted Intake:**")
                    for item in parsed.get('intake', []):
                        st.markdown(f"- **{item['item_name']}** ({item['item_type']})")
                    if parsed.get('symptoms'):
                        st.markdown("**Detected Symptoms:**")
                        for s in parsed['symptoms']:
                            st.markdown(f"- {s['symptom_type']} — severity ~{s['severity_estimate']}/10")
                    st.info(f"Confidence: {parsed.get('confidence', 'unknown')}")
                    if parsed.get('clarification_needed'):
                        st.warning(f"AI needs clarification: {parsed['clarification_needed']}")
                else:
                    st.error("Could not extract data. Try rephrasing.")
        else:
            st.warning("Please type something first.")
    
    if 'nlp_parsed' in st.session_state and st.session_state['nlp_parsed']:
        if st.button("✅ Confirm and Save to Database"):
            parsed = st.session_state['nlp_parsed']
            saved = 0
            for item in parsed.get('intake', []):
                try:
                    supabase.table("clinical_intake").insert({
                        "username": st.session_state.username,
                        "item_type": item.get('item_type'),
                        "item_name": item.get('item_name'),
                        "quantity_g": item.get('quantity_g'),
                        "calories": item.get('calories'),
                        "carbs_g": item.get('carbs_g'),
                        "protein_g": item.get('protein_g'),
                        "fats_g": item.get('fats_g'),
                        "sodium_mg": item.get('sodium_mg'),
                        "caffeine_mg": item.get('caffeine_mg'),
                    }).execute()
                    saved += 1
                except Exception as e:
                    st.error(f"Error saving item: {e}")
            for symptom in parsed.get('symptoms', []):
                try:
                    supabase.table("symptom_logs").insert({
                        "username": st.session_state.username,
                        "symptom_type": symptom.get('symptom_type'),
                        "severity": symptom.get('severity_estimate'),
                        "notes": symptom.get('notes'),
                    }).execute()
                except Exception as e:
                    st.error(f"Error saving symptom: {e}")
            st.balloons()
            st.success(f"Saved {saved} intake item(s) and {len(parsed.get('symptoms',[]))} symptom(s).")
            st.session_state['nlp_parsed'] = None


with tab3:
    st.markdown(f"## {st.session_state.username}'s Consumption History")
    # (this is your old tab2 content — move it here in the next step)
          

    except Exception:
        st.warning("Dashboard sync failed")