import streamlit as st
import csv
import os
import io
import base64
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv(Path(__file__).parent / ".env")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "asafasfdc/SFDC_TMT_BVS")
GITHUB_CSV_PATH = "results.csv"
CSV_HEADER = ["name", "A", "B", "C", "D", "E", "archetype"]


def _github_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


def load_results() -> pd.DataFrame:
    if not GITHUB_TOKEN:
        return pd.DataFrame(columns=CSV_HEADER)
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CSV_PATH}",
            headers=_github_headers(),
        )
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"]).decode("utf-8")
            return pd.read_csv(io.StringIO(content))
        return pd.DataFrame(columns=CSV_HEADER)
    except Exception:
        return pd.DataFrame(columns=CSV_HEADER)


def save_results(df: pd.DataFrame):
    if not GITHUB_TOKEN:
        return
    csv_content = df.to_csv(index=False)
    encoded = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CSV_PATH}",
        headers=_github_headers(),
    )
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {"message": "Update survey results", "content": encoded}
    if sha:
        payload["sha"] = sha

    requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CSV_PATH}",
        headers=_github_headers(),
        json=payload,
    )

QUESTIONS = [
    ("Q1", "A", "I love diving into a massive, messy Excel file to find the \"truth.\"",
            "B", "I love the rush of standing in front of a whiteboard and winning over a skeptical CFO."),
    ("Q2", "C", "I'm the one who makes sure the AE, SE, and CSM are all on the same page.",
            "D", "I spend my weekends reading about AI trends and how they'll disrupt TMT in 3 years."),
    ("Q3", "E", "I take a \"To-Do\" list and don't stop until every single item is checked off.",
            "A", "I'd rather spend 4 hours perfecting a financial model than 4 hours doing admin tasks."),
    ("Q4", "B", "I am naturally energized by the challenge of turning a \"No\" into a \"Yes.\"",
            "C", "I get my energy from building deep, long-term trust with my customer champions."),
    ("Q5", "D", "I enjoy connecting dots between different industries that others don't see.",
            "E", "I am the \"engine\"—I keep the deal moving forward when others get distracted."),
    ("Q6", "A", "Accuracy and data-integrity are my highest priorities in a business case.",
            "D", "Innovation and \"the big idea\" are more important than the decimal points."),
    ("Q7", "B", "I enjoy the spotlight of an executive readout.",
            "E", "I prefer being behind the scenes ensuring the project hits its milestones."),
    ("Q8", "C", "I am highly sensitive to the \"politics\" and \"emotions\" in a customer meeting.",
            "A", "I focus primarily on the logic and the financial \"proof\" of the argument."),
    ("Q9", "D", "I am constantly asking \"Why?\" and \"What if?\" during discovery.",
            "B", "I am constantly thinking \"How do I close this?\" and \"How do I sell this?\""),
    ("Q10", "E", "I feel a massive sense of accomplishment just by finishing a deck.",
             "C", "I feel accomplishment when the account team says, \"We couldn't have done this without you.\""),
]

ARCHETYPES = {
    "A": ("The Analytical Engine", "You are the \"Source of Truth.\" You bring the rigor that makes the value case unassailable."),
    "B": ("The Command Presence", "You are the \"Closer.\" You have the gravitas to challenge C-suite thinking and drive a decision."),
    "C": ("The Relational Glue", "You are the \"Trusted Advisor.\" You navigate the human complexity of a deal to ensure buy-in."),
    "D": ("The Strategic Visionary", "You are the \"POV Architect.\" You help customers see a future they haven't imagined yet."),
    "E": ("The High-Output Achiever", "You are the \"Reliability Factor.\" You ensure the BVS engine delivers world-class work on time."),
}

HYBRID_NAMES = {
    ("A", "B"): "Analytical Closer",
    ("A", "C"): "Data-Driven Advisor",
    ("A", "D"): "Strategic Scientist",
    ("A", "E"): "Precision Machine",
    ("B", "C"): "Executive Whisperer",
    ("B", "D"): "Visionary Commander",
    ("B", "E"): "Relentless Closer",
    ("C", "D"): "Empathic Visionary",
    ("C", "E"): "Trusted Workhorse",
    ("D", "E"): "Visionary Executor",
}


def get_hybrid_name(a: str, b: str) -> str:
    key = tuple(sorted([a, b]))
    return HYBRID_NAMES.get(key, f"{a}/{b} Hybrid")


def compute_archetype(counts: dict[str, int]) -> str:
    max_count = max(counts.values())
    top_letters = sorted([k for k, v in counts.items() if v == max_count])
    if len(top_letters) == 1:
        return ARCHETYPES[top_letters[0]][0]
    return f"Hybrid: {get_hybrid_name(top_letters[0], top_letters[1])} ({top_letters[0]}/{top_letters[1]})"


def save_result(name: str, counts: dict[str, int], archetype: str):
    df = load_results()
    new_row = pd.DataFrame([{
        "name": name, "A": counts["A"], "B": counts["B"], "C": counts["C"],
        "D": counts["D"], "E": counts["E"], "archetype": archetype
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_results(df)


def show_admin_view():
    st.title("BVS Admin Dashboard")

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.markdown("Enter the admin password to view team results.")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Access Denied")
        return

    df = load_results()
    if df.empty:
        st.warning("No results yet. Have the team take the survey first!")
        return

    st.metric("Total Responses", len(df))

    st.subheader("Archetype Distribution")
    archetype_counts = df["archetype"].value_counts()
    st.bar_chart(archetype_counts)

    st.subheader("Letter Score Totals Across the Team")
    letter_totals = df[["A", "B", "C", "D", "E"]].sum()
    st.bar_chart(letter_totals)

    st.subheader("Individual Results")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    if st.button("Send Summary to asafa@salesforce.com", type="primary"):
        summary_lines = ["BVS Team Strengths Summary", f"Total Responses: {len(df)}", ""]
        summary_lines.append("Archetype Distribution:")
        for arch, count in archetype_counts.items():
            summary_lines.append(f"  {arch}: {count}")
        summary_lines.append("")
        summary_lines.append("Individual Results:")
        for _, row in df.iterrows():
            summary_lines.append(f"  {row['name']}: {row['archetype']} (A={row['A']} B={row['B']} C={row['C']} D={row['D']} E={row['E']})")

        summary_text = "\n".join(summary_lines)

        st.text_area("Summary Preview", summary_text, height=300)
        st.download_button(
            label="Download Results CSV",
            data=df.to_csv(index=False),
            file_name="bvs_results.csv",
            mime="text/csv",
        )
        st.info("Download the CSV above and email it to asafa@salesforce.com, or copy the summary text.")


def show_intro():
    st.title("Welcome to the BVS StrengthsFinder Assessment")

    name = st.text_input("Your Name", placeholder="Enter your name")

    st.markdown("---")
    st.subheader("The 5 Core Strength Dimensions")
    st.markdown(
        "Every BVS professional has a unique superpower. "
        "This assessment will help you discover yours. Here are the five archetypes:"
    )

    dimensions = [
        ("🔢", "The Analytical Engine",
         'You are the "Source of Truth." You thrive on data, financial models, and finding the truth in complexity. You make the value case unassailable.'),
        ("🎤", "The Command Presence",
         'You are the "Closer." You have natural gravitas and energy in the room. You challenge C-suite thinking and drive decisions.'),
        ("🤝", "The Relational Glue",
         'You are the "Trusted Advisor." You read the room, navigate politics, and build the human trust that makes deals close.'),
        ("💡", "The Strategic Visionary",
         'You are the "POV Architect." You connect dots across industries and help customers see a future they haven\'t imagined yet.'),
        ("⚡", "The High-Output Achiever",
         'You are the "Reliability Factor." You keep the engine running, hit milestones, and ensure world-class work gets delivered on time.'),
    ]
    for emoji, title, desc in dimensions:
        st.markdown(f"**{emoji} {title}**")
        st.markdown(desc)
        st.markdown("")

    st.divider()
    if st.button("Got it, let's go! →", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Please enter your name to continue.")
        else:
            st.session_state.survey_name = name.strip()
            st.session_state.survey_started = True
            st.rerun()


def show_quiz():
    name = st.session_state.survey_name
    st.title("BVS Team Strengths Assessment")
    st.markdown(f"**{name}**, answer each question with the option that feels most like you.")
    st.divider()

    answers = {}
    for q_label, letter1, text1, letter2, text2 in QUESTIONS:
        st.markdown(f"**{q_label}:**")
        choice = st.radio(
            q_label,
            options=[letter1, letter2],
            format_func=lambda x, l1=letter1, t1=text1, l2=letter2, t2=text2: f"{l1}) {t1}" if x == l1 else f"{l2}) {t2}",
            index=None,
            label_visibility="collapsed",
        )
        answers[q_label] = choice

    st.divider()
    submitted = st.button("Submit", type="primary", use_container_width=True)

    if submitted:
        if None in answers.values():
            st.error("Please answer all 10 questions before submitting.")
        else:
            counts = {letter: 0 for letter in "ABCDE"}
            for choice in answers.values():
                counts[choice] += 1

            archetype_label = compute_archetype(counts)
            save_result(name, counts, archetype_label)

            st.balloons()
            st.success(f"Thanks **{name}**, your results have been recorded!")
            st.info("Your archetype will be revealed by your team lead. Stay tuned!")


def show_survey():
    if st.session_state.get("survey_started"):
        show_quiz()
    else:
        show_intro()


st.set_page_config(page_title="BVS Strengths Assessment", page_icon="💪")

query_params = st.query_params
is_admin = query_params.get("admin", "").lower() == "true"

if is_admin:
    show_admin_view()
else:
    show_survey()
