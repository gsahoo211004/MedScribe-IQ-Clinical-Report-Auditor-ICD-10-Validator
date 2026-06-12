import streamlit as st
import time
import sys
import os

sys.path.append(os.path.dirname(__file__))

from src.nlp.extractor import extract_entities
from src.icd.validator import validate_entities
from src.llm.summarizer import generate_audit_summary
from src.mlops.tracker import log_pipeline_run

st.set_page_config(
    page_title="MedScribe-IQ",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MedScribe-IQ — Clinical Report Auditor")
st.markdown("AI-powered NLP pipeline for ICD-10 validation and billing compliance audit.")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Pipeline stages:**
    1. NLP entity extraction
    2. Negation detection
    3. ICD-10 validation
    4. LLM audit summary
    5. MLflow run logging
    """)
    st.divider()
    st.markdown("Built with spaCy, Gemini, MLflow, Evidently AI")

# Input
st.subheader("1. Input Clinical Report")
sample = (
    "Patient presents with hypertension and tachycardia. "
    "No signs of diabetes. Denies fever or headache. "
    "Currently on metformin and aspirin. "
    "History of asthma but no recent episodes."
)
clinical_text = st.text_area(
    "Paste discharge summary below:",
    value=sample,
    height=150
)

if st.button("Run Audit Pipeline", type="primary"):
    start_time = time.time()

    # Stage 1: NLP extraction
    with st.spinner("Stage 1/4 — Extracting clinical entities..."):
        entities = extract_entities(clinical_text)
        time.sleep(0.3)

    # Stage 2: ICD-10 validation
    with st.spinner("Stage 2/4 — Validating ICD-10 codes..."):
        audit_results = validate_entities(entities)
        time.sleep(0.3)

    # Stage 3: LLM summary
    with st.spinner("Stage 3/4 — Generating LLM audit summary..."):
        llm_summary = generate_audit_summary(clinical_text, audit_results)

    # Stage 4: MLflow logging
    with st.spinner("Stage 4/4 — Logging pipeline run to MLflow..."):
        processing_time = round(time.time() - start_time, 3)
        log_pipeline_run(clinical_text, entities, audit_results, processing_time)

    st.success(f"Pipeline completed in {processing_time}s")

    # Results
    st.divider()
    st.subheader("2. Extracted Entities")

    col1, col2, col3, col4 = st.columns(4)
    validated = [r for r in audit_results if r["status"] in ["VALIDATED", "VALIDATED_VIA_API"]]
    negated = [r for r in audit_results if r["status"] == "NEGATED"]
    flagged = [r for r in audit_results if r["status"] == "FLAGGED"]

    col1.metric("Total Entities", len(entities))
    col2.metric("Validated", len(validated))
    col3.metric("Negated", len(negated))
    col4.metric("Flagged", len(flagged))

    # Entity table
    import pandas as pd
    entity_df = pd.DataFrame(entities)
    if not entity_df.empty:
        st.dataframe(entity_df, use_container_width=True)

    # ICD-10 results
    st.divider()
    st.subheader("3. ICD-10 Validation Results")

    def color_status(val):
        colors = {
            "VALIDATED": "background-color: #1a472a; color: white",
            "VALIDATED_VIA_API": "background-color: #1a472a; color: white",
            "NEGATED": "background-color: #2d2d00; color: white",
            "FLAGGED": "background-color: #4a0000; color: white",
        }
        return colors.get(val, "")

    audit_df = pd.DataFrame(audit_results)
    if not audit_df.empty:
        styled = audit_df.style.map(color_status, subset=["status"])
        st.dataframe(styled, use_container_width=True)

    # LLM Summary
    st.divider()
    st.subheader("4. LLM Audit Summary")
    st.info(llm_summary)

    # MLflow link
    st.divider()
    st.caption("Pipeline run logged to MLflow. To view: run `mlflow ui --backend-store-uri sqlite:///mlflow.db`")