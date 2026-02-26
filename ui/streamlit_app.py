"""
streamlit_app.py — MedGraphRAG Chat UI

Run with:
    streamlit run ui/streamlit_app.py
"""

import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
os.chdir(_project_root)

import streamlit as st

try:
    from rag.pipeline import graph_rag_pipeline
    _import_error = None
except Exception as _e:
    _import_error = str(_e)

# Page config
st.set_page_config(
    page_title="MedGraphRAG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Sidebar
with st.sidebar:
    st.title("MedGraphRAG")
    st.caption("Graph-powered medical Q&A — 100% local & free")
    st.divider()

    top_k = st.slider(
        "Seed nodes (top_k)",
        min_value=1,
        max_value=5,
        value=3,
        help="Number of most-similar graph nodes to use as starting points for traversal.",
    )

    st.divider()
    st.markdown("**Example queries:**")
    example_queries = [
        "What drugs treat Type 2 Diabetes?",
        "What are the drug interactions between metformin and aspirin?",
        "What diseases are associated with chest pain and shortness of breath?",
        "What is the treatment for atrial fibrillation?",
        "What are the dangers of combining warfarin and ibuprofen?",
        "What genes are associated with hypertension?",
        "What diseases commonly co-occur with Type 2 Diabetes?",
    ]
    for eq in example_queries:
        if st.button(eq, use_container_width=True):
            st.session_state["prefill_query"] = eq

    st.divider()
    st.warning(
        "**Disclaimer:** This tool is for educational purposes only. "
        "Never use this for real clinical decisions. Always consult a licensed clinician."
    )

# Main area
st.title("🏥 MedGraphRAG")
st.markdown(
    "Ask clinical questions and get answers grounded in a **medical knowledge graph** "
    "(diseases, drugs, symptoms, interactions, genes)."
)

# Show import error prominently if modules failed to load
if _import_error:
    st.error(f"❌ Import error — pipeline could not be loaded:\n\n{_import_error}")
    st.stop()

# Pre-fill from sidebar button click
if "prefill_query" in st.session_state:
    st.session_state["query_input"] = st.session_state.pop("prefill_query")

# Use a form so text input + button work together correctly
with st.form(key="query_form", clear_on_submit=False):
    query = st.text_input(
        "Your question:",
        key="query_input",
        placeholder="e.g. What are the drug interactions between warfarin and aspirin?",
    )
    run = st.form_submit_button("Ask", type="primary")

if run and query.strip():
    with st.spinner("Searching knowledge graph and generating answer..."):
        try:
            answer, subgraph = graph_rag_pipeline(query.strip(), top_k=top_k)
            st.session_state["last_answer"] = answer
            st.session_state["last_subgraph"] = subgraph
            st.session_state["last_query"] = query.strip()
        except Exception as exc:
            import traceback
            st.error(f"Pipeline error: {exc}")

# Display results
if "last_answer" in st.session_state:
    answer = st.session_state["last_answer"]
    subgraph = st.session_state["last_subgraph"]
    last_query = st.session_state["last_query"]

    st.divider()

    # --- Answer ---
    st.markdown("### Answer")
    st.markdown(answer)

    st.divider()

    # --- Seed nodes ---
    seeds = subgraph.get("seed_nodes", {})
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Seed Diseases retrieved:**")
        if seeds.get("diseases"):
            for d in seeds["diseases"]:
                st.markdown(f"- {d}")
        else:
            st.caption("None")
    with col2:
        st.markdown("**Seed Drugs retrieved:**")
        if seeds.get("drugs"):
            for d in seeds["drugs"]:
                st.markdown(f"- {d}")
        else:
            st.caption("None")

    st.divider()

    # --- Disease context cards ---
    disease_ctx = subgraph.get("disease_contexts", [])
    if disease_ctx:
        st.markdown("### Disease Contexts from Graph")
        for ctx in disease_ctx:
            with st.expander(f"{ctx['disease']} (ICD: {ctx.get('icd_code', 'N/A')})"):
                st.markdown(f"**Category:** {ctx.get('category', 'N/A')}")
                st.markdown(f"**Description:** {ctx.get('description', 'N/A')}")

                symptoms = ctx.get("symptoms", [])
                if symptoms:
                    st.markdown(f"**Symptoms:** {', '.join(symptoms)}")

                treatments = ctx.get("treatments", [])
                if treatments:
                    st.markdown("**Treatments:**")
                    for t in treatments:
                        st.markdown(f"  - {t['drug']} *(evidence: {t.get('evidence', 'N/A')})*")

                comorbidities = ctx.get("comorbidities", [])
                if comorbidities:
                    st.markdown(f"**Comorbidities:** {', '.join(comorbidities)}")

                genes = ctx.get("genes", [])
                if genes:
                    st.markdown(f"**Associated Genes:** {', '.join(genes)}")

                interactions = ctx.get("drug_interactions", [])
                if interactions:
                    st.markdown("**Drug Interactions:**")
                    for ix in interactions:
                        severity = ix.get("severity", "?")
                        color = {"Major": "red", "Moderate": "orange", "Mild": "green"}.get(severity, "grey")
                        st.markdown(
                            f"  - :{color}[**{ix['drug_a']}** ↔ **{ix['drug_b']}** ({severity})]"
                            f": {ix.get('description', '')}"
                        )

    # --- Drug context cards ---
    drug_ctx = subgraph.get("drug_contexts", [])
    if drug_ctx:
        st.markdown("### Drug Contexts from Graph")
        for ctx in drug_ctx:
            with st.expander(f"{ctx['drug']} ({ctx.get('drug_class', 'N/A')})"):
                st.markdown(f"**Mechanism:** {ctx.get('mechanism', 'N/A')}")

                treats = ctx.get("treats", [])
                if treats:
                    st.markdown("**Treats:**")
                    for t in treats:
                        st.markdown(f"  - {t['disease']} *(evidence: {t.get('evidence', 'N/A')})*")

                interactions = ctx.get("interactions", [])
                if interactions:
                    st.markdown("**Interactions:**")
                    for ix in interactions:
                        severity = ix.get("severity", "?")
                        color = {"Major": "red", "Moderate": "orange", "Mild": "green"}.get(severity, "grey")
                        st.markdown(
                            f"  - :{color}[**{ix['drug']}** ({severity})]"
                            f": {ix.get('description', '')}"
                        )

    # --- Raw JSON (for debugging) ---
    with st.expander("Raw subgraph JSON (debug)"):
        st.json(subgraph)
