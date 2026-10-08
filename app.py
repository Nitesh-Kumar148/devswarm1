import streamlit as st
from orchestrator import run_pipeline

st.set_page_config(page_title="DevSwarm", page_icon="🤖", layout="wide")

st.title("🤖 DevSwarm")
st.caption("Autonomous AI Engineering Team — Plan → Build → Test → Fix")

if "logs" not in st.session_state:
    st.session_state.logs = []
if "result" not in st.session_state:
    st.session_state.result = None

requirement = st.text_area(
    "What should DevSwarm build?",
    value="Build a simple To-Do web application with add, delete and complete-task functionality.",
    height=120,
)

if st.button("🚀 Build Application", type="primary"):
    if not requirement.strip():
        st.warning("Please enter a software requirement.")
    else:
        st.session_state.logs = []
        st.session_state.result = None

        def log(message):
            st.session_state.logs.append(message)

        with st.spinner("DevSwarm is working..."):
            try:
                result = run_pipeline(requirement.strip(), log)
                st.session_state.result = result
            except Exception as exc:
                log(f"❌ Pipeline error: {exc}")
                st.session_state.result = {"success": False, "error": str(exc)}

if st.session_state.logs:
    st.subheader("Agent Activity")
    for item in st.session_state.logs:
        st.write(item)

result = st.session_state.result
if result:
    st.divider()
    if result.get("success"):
        st.success("✅ Application is ready!")
        st.write(f"**Attempts:** {result.get('attempts', 1)}")
        st.write(f"**Workspace:** `{result.get('workspace', './workspace')}`")
        st.info("Open the generated `index.html` from the workspace folder in Chrome to demonstrate the application.")
        if result.get("test_output"):
            with st.expander("Final test output"):
                st.code(result["test_output"])
    else:
        st.error("❌ DevSwarm could not complete the build.")
        if result.get("error"):
            st.code(result["error"])
