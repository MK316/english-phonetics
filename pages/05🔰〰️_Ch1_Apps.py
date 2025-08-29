import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Multi-App Template", page_icon="🧰", layout="wide")
st.title("🧰 Multi-App Template")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["App 1", "App 2", "App 3"])

# =========================================================
# TAB 1 — Template (form + controls + output)
# =========================================================
with tab1:
    st.subheader("App 1")
    left, right = st.columns([1, 2], vertical_alignment="top")

    with left:
        st.markdown("**Controls**")
        # Use a form so the app doesn't rerun on every keystroke
        with st.form("app1_form", clear_on_submit=False):
            text = st.text_input("Your text", key="app1_text")
            choice = st.selectbox("Option", ["A", "B", "C"], key="app1_choice")
            run = st.form_submit_button("Run", use_container_width=True)
    with right:
        st.markdown("**Output**")
        if run:
            st.success("App 1 ran successfully.")
            st.write({"text": text, "choice": choice})
        else:
            st.info("Fill the controls on the left and click **Run**.")

    st.divider()
    st.caption("➡️ Replace this tab's controls and output with your real App 1.")

# =========================================================
# TAB 2 — Template (file uploader + preview)
# =========================================================
with tab2:
    st.subheader("App 2")
    c1, c2 = st.columns([1, 2], vertical_alignment="top")

    with c1:
        uploaded = st.file_uploader(
            "Upload a file (image or text)",
            type=["png", "jpg", "jpeg", "gif", "webp", "txt", "md"],
            key="app2_uploader",
            accept_multiple_files=False
        )
        st.button("Clear", use_container_width=True, key="app2_clear")

    with c2:
        st.markdown("**Preview**")
        if uploaded is None:
            st.info("Upload an image (.png/.jpg/.jpeg/.gif/.webp) or a text file (.txt/.md).")
        else:
            if uploaded.type.startswith("image/"):
                st.image(uploaded, use_container_width=True, caption=uploaded.name)
            else:
                # Text preview (first 2000 chars)
                text = uploaded.read().decode(errors="ignore")
                st.text_area("Text preview", value=text[:2000], height=300, label_visibility="collapsed")

    st.divider()
    st.caption("➡️ Swap this for your real App 2 (e.g., CSV viewer, analyzer, etc.).")

# =========================================================
# TAB 3 — Template (notes + download)
# =========================================================
with tab3:
    st.subheader("App 3")
    notes = st.text_area(
        "Scratchpad / Notes",
        value="Write anything here...\n",
        height=220,
        key="app3_notes"
    )
    st.download_button(
        "Download notes (.txt)",
        data=notes.encode("utf-8"),
        file_name="notes.txt",
        mime="text/plain",
        use_container_width=True,
        key="app3_download"
    )

    st.divider()
    st.caption("➡️ Replace this with your real App 3 (e.g., visualizer, quiz, etc.).")

# ================== Tips ==================
# - Each widget uses a unique key (e.g., app1_text) to avoid conflicts across tabs/pages.
# - Use st.form for groups of inputs you want to submit together.
# - For bigger apps per tab, factor logic into functions and call them inside the tab blocks.
# - You can add a common sidebar for shared settings across all tabs if needed.
