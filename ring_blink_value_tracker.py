"""
Ring/Blink Agentforce for Service — Value Realization Tracker
Built for Amazon by Salesforce BVS | Confidential
"""

import streamlit as st
import pandas as pd
import os
import datetime
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px

load_dotenv()

# ── Brand Colors ──────────────────────────────────────────────
SF_BLUE  = "#00A1E0"
SF_NAVY  = "#032D60"
SF_WHITE = "#FFFFFF"

# ── Passwords ─────────────────────────────────────────────────
ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD", "bvs2026")
CLIENT_PASSWORD = os.getenv("CLIENT_PASSWORD", "amazon2026")

# ── Business Case Data ────────────────────────────────────────
STEADY_STATE = {
    "Increase Digitally Resolved Cases": {"Ring Voice":18.0,"Ring Chat":15.0,"Blink Voice":12.0,"Blink Email":0.0,"Total":45.0},
    "Reduce Repeat Contacts":            {"Ring Voice":1.2, "Ring Chat":0.8, "Blink Voice":0.8, "Blink Email":0.4,"Total":3.2},
    "Decrease AHT":                      {"Ring Voice":3.0, "Ring Chat":1.2, "Blink Voice":2.0, "Blink Email":2.5,"Total":8.7},
    "Increase Support Productivity":     {"Ring Voice":0.723,"Ring Chat":0.483,"Blink Voice":0.325,"Blink Email":0.163,"Total":1.7},
    "Reduce Agent Onboarding Time":      {"Ring Voice":0.288,"Ring Chat":0.192,"Blink Voice":0.192,"Blink Email":0.096,"Total":0.768},
    "Increase Supervisor Productivity":  {"Ring Voice":0.866,"Ring Chat":0.578,"Blink Voice":0.413,"Blink Email":0.206,"Total":2.1},
}
TOTAL_STEADY_STATE = 61.5  # $M
YEAR1_TOTAL = 31.5          # $M
YEAR2_TOTAL = 61.5          # $M

ROI = {
    "2-Year Gross Benefits NPV": "$86.4M",
    "2-Year Net Benefits NPV":   "$88.4M",
    "Cumulative 2-Year ROI":     "4,441%",
    "Payback Period":            "0.3 months",
    "Cost of Delay (per month)": "$5.0M",
    "WACC":                      "11.38%",
    "Year 1 Costs":              "$1.0M",
    "Year 2 Costs":              "$1.35M",
}

# ── Feature Attribution Matrix (from Value Matrix sheet) ──────
FEATURES = [
    {"Feature":"Agentforce Voice (Phone)","AI Type":"Agentic","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"✓","FCR":"✓","AHT":"","Support Prod":"","Onboarding":"","Supervisor":"","Retention":"✓","Cross-sell":""},
    {"Feature":"Agentforce Voice (Digital) GA Jan'26","AI Type":"Agentic","Pilot":"","Full Scope":"✓",
     "Case Deflection":"✓","FCR":"✓","AHT":"","Support Prod":"","Onboarding":"","Supervisor":"","Retention":"✓","Cross-sell":""},
    {"Feature":"Agentforce Service Agent (Digital)","AI Type":"Agentic","Pilot":"","Full Scope":"✓",
     "Case Deflection":"✓","FCR":"✓","AHT":"","Support Prod":"","Onboarding":"","Supervisor":"","Retention":"","Cross-sell":""},
    {"Feature":"Case Classification","AI Type":"Predictive","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"","FCR":"✓","AHT":"✓","Support Prod":"","Onboarding":"","Supervisor":"","Retention":"✓","Cross-sell":""},
    {"Feature":"Case Routing","AI Type":"Predictive","Pilot":"","Full Scope":"",
     "Case Deflection":"","FCR":"","AHT":"✓","Support Prod":"","Onboarding":"","Supervisor":"✓","Retention":"✓","Cross-sell":""},
    {"Feature":"Automated Case Wrap-Up","AI Type":"Predictive","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"","FCR":"","AHT":"✓","Support Prod":"✓","Onboarding":"","Supervisor":"✓","Retention":"","Cross-sell":""},
    {"Feature":"Real-Time Next Best Action","AI Type":"Predictive","Pilot":"","Full Scope":"",
     "Case Deflection":"","FCR":"✓","AHT":"✓","Support Prod":"","Onboarding":"✓","Supervisor":"✓","Retention":"","Cross-sell":"✓"},
    {"Feature":"Service Replies","AI Type":"Generative","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"","FCR":"✓","AHT":"✓","Support Prod":"","Onboarding":"","Supervisor":"","Retention":"✓","Cross-sell":""},
    {"Feature":"Work Summaries","AI Type":"Generative","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"✓","FCR":"","AHT":"","Support Prod":"✓","Onboarding":"","Supervisor":"✓","Retention":"","Cross-sell":""},
    {"Feature":"Service Rep Assistant","AI Type":"Generative","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"","FCR":"✓","AHT":"✓","Support Prod":"✓","Onboarding":"✓","Supervisor":"✓","Retention":"","Cross-sell":""},
    {"Feature":"Knowledge Creation","AI Type":"Generative","Pilot":"✓","Full Scope":"✓",
     "Case Deflection":"","FCR":"✓","AHT":"","Support Prod":"✓","Onboarding":"✓","Supervisor":"✓","Retention":"","Cross-sell":""},
    {"Feature":"Real Time Translations","AI Type":"Generative","Pilot":"","Full Scope":"",
     "Case Deflection":"","FCR":"","AHT":"✓","Support Prod":"","Onboarding":"","Supervisor":"✓","Retention":"✓","Cross-sell":""},
    {"Feature":"Customer Signals Intelligence","AI Type":"Analytics","Pilot":"","Full Scope":"✓",
     "Case Deflection":"","FCR":"","AHT":"","Support Prod":"","Onboarding":"","Supervisor":"✓","Retention":"✓","Cross-sell":""},
]

DATA_FILE = "value_tracker_data.csv"

# ── Helpers ───────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Month","Year",
        "Ring_Containment","Ring_FCR","Ring_CSAT","Ring_CallVolume",
        "Ring_AHT","Ring_SupportProd","Ring_Onboarding","Ring_SupervisorProd",
        "Blink_Containment","Blink_FCR","Blink_CSAT","Blink_CallVolume",
        "Blink_AHT","Blink_SupportProd","Blink_Onboarding","Blink_SupervisorProd",
        "Notes"
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def rag_color(actual, target):
    if target == 0: return "🟡"
    pct = actual / target
    if pct >= 0.75: return "🟢"
    if pct >= 0.50: return "🟡"
    return "🔴"

def calc_cumulative_value(df):
    if df.empty: return 0.0
    avg_ring = df["Ring_Containment"].mean() if "Ring_Containment" in df else 0
    avg_blink = df["Blink_Containment"].mean() if "Blink_Containment" in df else 0
    ring_val  = (avg_ring/100) * 24.1  * len(df)
    blink_val = (avg_blink/100) * 15.7 * len(df)
    return round(ring_val + blink_val, 2)

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Agentforce for Service — Value Tracker",
    page_icon="📊",
    layout="wide"
)

st.markdown(f"""
<style>
    .main {{ background-color: {SF_WHITE}; }}
    .block-container {{ padding-top: 1.5rem; }}
    h1, h2, h3 {{ color: {SF_NAVY}; }}
    .stMetric label {{ color: {SF_BLUE} !important; font-weight: 600; }}
    div[data-testid="metric-container"] {{
        background: #f0f8ff;
        border-left: 4px solid {SF_BLUE};
        border-radius: 6px;
        padding: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# LOGIN GATE
# ══════════════════════════════════════════════════════════════
if "role" not in st.session_state:
    st.session_state.role = None

def show_login():
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.image("https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg", width=200)
        st.markdown("")
        st.title("Agentforce for Service — Value Realization Tracker")
        st.caption("Amazon Ring & Blink  |  Confidential")
        st.markdown("---")

        client_pwd = st.text_input("Client Access", type="password", placeholder="Enter client password")
        admin_pwd  = st.text_input("Admin Access", type="password", placeholder="Enter admin password")

        st.markdown("")
        if st.button("Enter", type="primary", use_container_width=True):
            if admin_pwd == ADMIN_PASSWORD:
                st.session_state.role = "admin"
                st.rerun()
            elif client_pwd == CLIENT_PASSWORD:
                st.session_state.role = "client"
                st.rerun()
            else:
                st.error("Access Denied. Please contact your Salesforce BVS team.")

if st.session_state.role is None:
    show_login()
    st.stop()

# ══════════════════════════════════════════════════════════════
# AUTHENTICATED — SIDEBAR & NAVIGATION
# ══════════════════════════════════════════════════════════════
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg", width=160)
st.sidebar.title("Navigation")

role_label = "Admin" if st.session_state.role == "admin" else "Client"
st.sidebar.caption(f"Logged in as: **{role_label}**")

if st.session_state.role == "admin":
    nav_options = [
        "📊 Executive Dashboard",
        "✏️ Metrics Input (Admin)",
        "📈 Value Over Time",
        "📋 Business Case Summary"
    ]
else:
    nav_options = [
        "📊 Executive Dashboard",
        "📈 Value Over Time",
        "📋 Business Case Summary"
    ]

page = st.sidebar.radio("", nav_options)

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Logout"):
    st.session_state.role = None
    st.rerun()

df = load_data()

# ══════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ══════════════════════════════════════════════════════════════
if page == "📊 Executive Dashboard":
    st.title("📊 Agentforce for Service — Value Realization Tracker")
    st.caption("Amazon Ring & Blink  |  Confidential  |  Built by Salesforce BVS")

    st.info("""
    📌 **Attribution Note:** Agentforce Voice directly measures **Case Deflection, FCR & Customer Retention**.
    AHT, Productivity & Onboarding gains are driven by the broader **Agentforce for Service bundle**.
    The $61.5M steady-state target reflects the **full bundle**, not Voice alone.
    """)

    st.divider()
    go_live_ring  = "🔄 In Progress"
    go_live_blink = "✅ Live since Feb 10, 2026 (~10% containment)"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 🔵 Ring")
        st.caption(f"Go-Live Status: {go_live_ring}")
        if not df.empty:
            latest = df.iloc[-1]
            st.metric("AI Containment Rate",    f"{latest.get('Ring_Containment',0):.1f}%",  help="Agentforce Voice KPI")
            st.metric("FCR Rate",               f"{latest.get('Ring_FCR',0):.1f}%",           help="Agentforce Voice KPI")
            st.metric("CSAT Score",             f"{latest.get('Ring_CSAT',0):.1f}",           help="Agentforce Voice KPI")
            st.metric("Monthly Call Volume",    f"{int(latest.get('Ring_CallVolume',0)):,}")
        else:
            st.metric("AI Containment Rate", "No data yet")
            st.metric("FCR Rate",            "No data yet")
            st.metric("CSAT Score",          "No data yet")

    with col2:
        st.markdown(f"### 🟢 Blink")
        st.caption(f"Go-Live Status: {go_live_blink}")
        if not df.empty:
            latest = df.iloc[-1]
            st.metric("AI Containment Rate",    f"{latest.get('Blink_Containment',0):.1f}%", help="Agentforce Voice KPI")
            st.metric("FCR Rate",               f"{latest.get('Blink_FCR',0):.1f}%",          help="Agentforce Voice KPI")
            st.metric("CSAT Score",             f"{latest.get('Blink_CSAT',0):.1f}",          help="Agentforce Voice KPI")
            st.metric("Monthly Call Volume",    f"{int(latest.get('Blink_CallVolume',0)):,}")
        else:
            st.metric("AI Containment Rate", "No data yet")
            st.metric("FCR Rate",            "No data yet")
            st.metric("CSAT Score",          "No data yet")

    st.divider()
    cumulative_value = calc_cumulative_value(df)
    progress_pct     = min(cumulative_value / TOTAL_STEADY_STATE, 1.0)
    rag = rag_color(cumulative_value, TOTAL_STEADY_STATE * 0.5)

    st.markdown(f"### {rag} Progress to ${TOTAL_STEADY_STATE}M Steady State (Full Bundle)")
    st.progress(progress_pct)
    st.caption(f"Estimated Cumulative Value Realized: **${cumulative_value:.1f}M** of **${TOTAL_STEADY_STATE}M**")
    st.caption(f"Last Updated: {datetime.datetime.now().strftime('%B %d, %Y %I:%M %p')}")

# ══════════════════════════════════════════════════════════════
# PAGE 2 — METRICS INPUT (ADMIN ONLY)
# ══════════════════════════════════════════════════════════════
elif page == "✏️ Metrics Input (Admin)":
    st.title("✏️ Monthly Metrics Input")
    st.caption("Admin access only")

    st.success("✅ Access granted")
    st.divider()

    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    col1, col2 = st.columns(2)
    with col1: month = st.selectbox("Month", months, index=datetime.datetime.now().month - 1)
    with col2: year  = st.number_input("Year", min_value=2026, max_value=2030, value=datetime.datetime.now().year)

    st.markdown("---")
    st.markdown("### 🎙️ Section A — Agentforce Voice KPIs _(directly attributable to Voice)_")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ring**")
        r_contain  = st.slider("Ring AI Containment Rate (%)",  0.0, 100.0, 0.0,  step=0.5)
        r_fcr      = st.slider("Ring FCR Rate (%)",             0.0, 100.0, 0.0,  step=0.5)
        r_csat     = st.slider("Ring CSAT Score",               0.0, 10.0,  0.0,  step=0.1)
        r_volume   = st.number_input("Ring Monthly Voice Call Volume", min_value=0, value=0, step=1000)
    with c2:
        st.markdown("**Blink**")
        b_contain  = st.slider("Blink AI Containment Rate (%)", 0.0, 100.0, 10.0, step=0.5)
        b_fcr      = st.slider("Blink FCR Rate (%)",            0.0, 100.0, 0.0,  step=0.5)
        b_csat     = st.slider("Blink CSAT Score",              0.0, 10.0,  0.0,  step=0.1)
        b_volume   = st.number_input("Blink Monthly Voice Call Volume", min_value=0, value=275000, step=1000)

    st.markdown("---")
    st.markdown("### 📦 Section B — Full Bundle Metrics _(AHT, Productivity driven by all Agentforce features)_")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Ring**")
        r_aht      = st.number_input("Ring AHT (seconds)",              min_value=0, value=0)
        r_sprod    = st.slider("Ring Support Productivity Score",        0.0, 10.0, 0.0, step=0.1)
        r_onboard  = st.slider("Ring Agent Onboarding Score",           0.0, 10.0, 0.0, step=0.1)
        r_supvprod = st.slider("Ring Supervisor Productivity Score",     0.0, 10.0, 0.0, step=0.1)
    with c4:
        st.markdown("**Blink**")
        b_aht      = st.number_input("Blink AHT (seconds)",             min_value=0, value=0)
        b_sprod    = st.slider("Blink Support Productivity Score",       0.0, 10.0, 0.0, step=0.1)
        b_onboard  = st.slider("Blink Agent Onboarding Score",          0.0, 10.0, 0.0, step=0.1)
        b_supvprod = st.slider("Blink Supervisor Productivity Score",    0.0, 10.0, 0.0, step=0.1)

    notes = st.text_area("Notes / Comments")

    if st.button("💾 Save Monthly Data", type="primary"):
        new_row = {
            "Month": month, "Year": year,
            "Ring_Containment":  r_contain,  "Ring_FCR":         r_fcr,
            "Ring_CSAT":         r_csat,     "Ring_CallVolume":  r_volume,
            "Ring_AHT":          r_aht,      "Ring_SupportProd": r_sprod,
            "Ring_Onboarding":   r_onboard,  "Ring_SupervisorProd": r_supvprod,
            "Blink_Containment": b_contain,  "Blink_FCR":        b_fcr,
            "Blink_CSAT":        b_csat,     "Blink_CallVolume": b_volume,
            "Blink_AHT":         b_aht,      "Blink_SupportProd":b_sprod,
            "Blink_Onboarding":  b_onboard,  "Blink_SupervisorProd": b_supvprod,
            "Notes": notes
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"✅ Data saved for {month} {year}!")
        st.rerun()

    if not df.empty:
        st.divider()
        st.markdown("### 📋 All Saved Data")
        st.dataframe(df, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 3 — VALUE OVER TIME
# ══════════════════════════════════════════════════════════════
elif page == "📈 Value Over Time":
    st.title("📈 Value Realization Over Time")

    if df.empty:
        st.info("No data yet. Enter monthly metrics in the Admin page.")
        st.stop()

    df["Period"] = df["Month"] + " " + df["Year"].astype(str)

    st.markdown("### 🎙️ Agentforce Voice Impact — Containment & FCR Trends")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["Period"], y=df["Ring_Containment"],  name="Ring Containment %",  line=dict(color=SF_BLUE,  width=2)))
    fig1.add_trace(go.Scatter(x=df["Period"], y=df["Blink_Containment"], name="Blink Containment %", line=dict(color=SF_NAVY,  width=2)))
    fig1.add_trace(go.Scatter(x=df["Period"], y=df["Ring_FCR"],          name="Ring FCR %",          line=dict(color="#66c2ff",width=2,dash="dot")))
    fig1.add_trace(go.Scatter(x=df["Period"], y=df["Blink_FCR"],         name="Blink FCR %",         line=dict(color="#334f6e",width=2,dash="dot")))
    fig1.update_layout(title="Voice KPIs Over Time", yaxis_title="%", xaxis_title="Month", legend=dict(orientation="h"))
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    st.markdown("### 📦 Full Bundle — Projected vs Actual Cumulative Value ($M)")

    months_count  = len(df)
    projected_y1  = [round(YEAR1_TOTAL * (i+1) / 12, 2) for i in range(min(months_count, 12))]
    projected_y2  = [round(YEAR1_TOTAL + (YEAR2_TOTAL - YEAR1_TOTAL) * (i+1) / 12, 2) for i in range(max(0, months_count - 12))]
    projected_cum = projected_y1 + projected_y2

    actual_cum = []
    running = 0
    for _, row in df.iterrows():
        r_val = (row["Ring_Containment"] / 100)  * 24.1
        b_val = (row["Blink_Containment"] / 100) * 15.7
        running += round(r_val + b_val, 2)
        actual_cum.append(running)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["Period"], y=projected_cum, name="Projected ($M)", line=dict(color="#aaa", dash="dash", width=2)))
    fig2.add_trace(go.Scatter(x=df["Period"], y=actual_cum,    name="Actual ($M)",    line=dict(color=SF_BLUE, width=3)))
    fig2.update_layout(title="Cumulative Value: Projected vs Actual", yaxis_title="$M", xaxis_title="Month", legend=dict(orientation="h"))
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("### 📊 Ring vs Blink Monthly Contribution ($M)")
    df["Ring_Val"]  = (df["Ring_Containment"]  / 100) * 24.1
    df["Blink_Val"] = (df["Blink_Containment"] / 100) * 15.7
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=df["Period"], y=df["Ring_Val"],  name="Ring ($M)",  marker_color=SF_BLUE))
    fig3.add_trace(go.Bar(x=df["Period"], y=df["Blink_Val"], name="Blink ($M)", marker_color=SF_NAVY))
    fig3.update_layout(barmode="group", yaxis_title="$M", xaxis_title="Month", legend=dict(orientation="h"))
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.markdown("### 📋 Monthly Actuals vs Projections")
    summary = pd.DataFrame({
        "Period":     df["Period"],
        "Ring Containment %":  df["Ring_Containment"],
        "Blink Containment %": df["Blink_Containment"],
        "Projected ($M)":      projected_cum,
        "Actual ($M)":         actual_cum,
        "Variance ($M)":       [round(a - p, 2) for a, p in zip(actual_cum, projected_cum)],
    })
    st.dataframe(summary, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 4 — BUSINESS CASE SUMMARY
# ══════════════════════════════════════════════════════════════
elif page == "📋 Business Case Summary":
    st.title("📋 Business Case Summary")
    st.caption("Ring / Blink Agentforce for Service | Confidential")

    st.info("""
    📌 **Agentforce Voice directly impacts:** Case Deflection & FCR
    📦 **Full bundle drives:** AHT, Productivity, Onboarding, Retention
    🗓️ **Blink Agentforce Voice:** Live since Feb 10, 2026 | **Ring Voice:** In Progress
    """)

    st.markdown("### 💰 Steady State Benefits ($M)")
    rows = []
    for benefit, vals in STEADY_STATE.items():
        rows.append({
            "Benefit": benefit,
            "Ring Voice ($M)":  vals["Ring Voice"],
            "Ring Chat ($M)":   vals["Ring Chat"],
            "Blink Voice ($M)": vals["Blink Voice"],
            "Blink Email ($M)": vals["Blink Email"],
            "Total ($M)":       vals["Total"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### 📈 Benefit Ramp")
    ramp_df = pd.DataFrame({
        "Channel":     ["Ring Voice","Ring Chat","Blink Voice","Blink Email"],
        "Year 1 Ramp": ["70%","20%","70%","0%"],
        "Year 2 Ramp": ["100%","100%","100%","100%"],
        "Y1 Value ($M)":["$16.9M","$3.7M","$11.0M","$0"],
        "Y2 Value ($M)":["$24.1M","$18.3M","$15.7M","$3.3M"],
    })
    st.dataframe(ramp_df, use_container_width=True, hide_index=True)

    st.markdown("### 📊 ROI Metrics")
    roi_df = pd.DataFrame(list(ROI.items()), columns=["Metric","Value"])
    st.dataframe(roi_df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🗂️ Feature Attribution Matrix")
    st.caption("Which Agentforce features drive which value metrics — from the Value Matrix")
    feat_df = pd.DataFrame(FEATURES)
    st.dataframe(feat_df, use_container_width=True, hide_index=True)

    if not df.empty:
        st.divider()
        st.markdown("### 🔴🟡🟢 Variance: Projected vs Actual (RAG Status)")
        months_count = len(df)
        projected_y1  = [round(YEAR1_TOTAL * (i+1) / 12, 2) for i in range(min(months_count, 12))]
        projected_y2  = [round(YEAR1_TOTAL + (YEAR2_TOTAL - YEAR1_TOTAL) * (i+1) / 12, 2) for i in range(max(0, months_count - 12))]
        projected_cum = projected_y1 + projected_y2
        actual_cum = []
        running = 0
        for _, row in df.iterrows():
            running += (row["Ring_Containment"]/100)*24.1 + (row["Blink_Containment"]/100)*15.7
            actual_cum.append(round(running, 2))
        df["Period"]    = df["Month"] + " " + df["Year"].astype(str)
        df["Projected"] = projected_cum
        df["Actual"]    = actual_cum
        df["Variance"]  = df["Actual"] - df["Projected"]
        df["RAG"] = df.apply(lambda r: rag_color(r["Actual"], r["Projected"]), axis=1)
        st.dataframe(df[["Period","Projected","Actual","Variance","RAG"]], use_container_width=True, hide_index=True)

    st.divider()
    st.caption("_Confidential. Built for Amazon by Salesforce BVS._")
