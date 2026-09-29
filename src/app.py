import hashlib
import os
import sys

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="PETRO-CORE // DPR AI Synthesis",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


try:
    from ui.styles import COMMAND_CSS
    st.markdown(COMMAND_CSS, unsafe_allow_html=True)
except Exception:
    COMMAND_CSS = ""

try:
    from input_validation import read_reports_csv
    from pipeline import analyze_reports
    from risk_scoring import apply_risk_scoring
    from pattern_analysis import analyze_patterns
    from ui.metrics import compute_metrics
    from ui.views import render_page, render_sidebar, render_topbar

    IMPORT_SUCCESS = True
except Exception as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)


if not IMPORT_SUCCESS:
    st.error("Unable to load the SIF analysis pipeline.")
    st.code(IMPORT_ERROR, language="text")
    st.stop()


DEFAULT_DATASET = os.path.join(ROOT_DIR, "data", "synthetic_reports.csv")

st.sidebar.markdown('<div class="pc-kicker">Data Source</div>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload safety reports CSV", type=["csv"])


@st.cache_data(show_spinner=False)
def run_pipeline(csv_bytes: bytes, signature: str):
    reports = read_reports_csv(csv_bytes)
    return analyze_reports(reports)


if uploaded_file is not None:
    pipeline_bytes = uploaded_file.getvalue()
    signature = hashlib.sha256(pipeline_bytes).hexdigest()
    data_note = f"Uploaded safety reports ({uploaded_file.name})"
else:
    if not os.path.exists(DEFAULT_DATASET):
        st.error("Default dataset not found: " + DEFAULT_DATASET)
        st.stop()

    with open(DEFAULT_DATASET, "rb") as dataset_file:
        pipeline_bytes = dataset_file.read()

    signature = hashlib.sha256(pipeline_bytes).hexdigest()
    data_note = "Using data/synthetic_reports.csv"

try:
    with st.spinner("Running SIF precursor pipeline…"):
       df, patterns = run_pipeline(pipeline_bytes, signature)
except Exception as e:
    st.error("Error while processing reports.")
    st.exception(e)
    st.stop()


metrics = compute_metrics(df)
page = render_sidebar(metrics, data_note)
df_view = render_topbar(df, metrics)
metrics_view = compute_metrics(df_view)
patterns_view = analyze_patterns(df_view)
render_page(page, df_view, patterns_view, metrics_view)