import streamlit as st
import pandas as pd
from pathlib import Path

CSV_FILE = Path(__file__).parent / "results.csv"

st.set_page_config(page_title="BVS Team Summary", page_icon="📊")
st.title("BVS Team Strengths Summary")

if not CSV_FILE.exists():
    st.warning("No results yet. Have the team take the survey first!")
    st.stop()

df = pd.read_csv(CSV_FILE)

if df.empty:
    st.warning("No results yet. Have the team take the survey first!")
    st.stop()

st.metric("Total Responses", len(df))

st.subheader("Archetype Distribution")
archetype_counts = df["archetype"].value_counts()
st.bar_chart(archetype_counts)

st.subheader("Letter Score Totals Across the Team")
letter_totals = df[["A", "B", "C", "D", "E"]].sum()
st.bar_chart(letter_totals)

st.subheader("Individual Results")
st.dataframe(df, use_container_width=True, hide_index=True)
