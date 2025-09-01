import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Multi-Apps", page_icon="🌀", layout="wide")
st.markdown("#### 🌀 Multi-Apps for Chapter 1")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["💦 Videos", "💦 Web links", "💦 Download"])

# =========================================================
# TAB 1 — Video links
# =========================================================
with tab1:
    st.subheader("🎬 Useful Videos")

    # Sample video list (replace URLs/titles with yours)
    videos = [
        {"title": "McGurk Effect (BBC)", "url": "https://www.youtube.com/embed/2k8fHR9jKVM?si=bQlOyoMNZEhnQ3Rf"},
        {"title": "How vocal folds work", "url": "https://www.youtube.com/embed/5QhVoaVUGmM?si=XNCbqRnVsG8oh8vS"},
        {"title": "How Does the Human Body Produce Voice and Speech?", "url": "https://www.youtube.com/embed/JF8rlKuSoFM?si=JSoICMOBWxrXdMn2"},
        {"title": "Vocal folds while singing", "url": "https://www.youtube.com/embed/-XGds2GAvGQ?si=a796eZI1vE87kiC3"}
    ]

    titles = [v["title"] for v in videos]
    choice = st.selectbox("Choose a video to play:", titles, key="tab1_video_choice")

    # Get selected video dict
    selected = next(v for v in videos if v["title"] == choice)

    # Control video size
    width = st.slider("Video width (px)", 400, 1000, 700, step=50)
    height = int(width * 9 / 16)  # keep 16:9 ratio

    st.markdown(
        f"""
        <div style="text-align: center;">
            <iframe width="{width}" height="{height}" 
                    src="{selected['url']}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
            </iframe>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"[🔗 Open on YouTube]({selected['url']})")



# =========================================================
# TAB 2 — Web links
# =========================================================
with tab2:
    st.subheader("Web links")
    st.markdown("🐾 [Textbook online](https://linguistics.berkeley.edu/acip/): This is a resource site managed by the Department of Linguistics at UC Berkeley for the textbook A Course in Phonetics. It contains materials related to the illustrations and exercises presented in the book.")
    #st.markdown("🐾 [](): This video was provided by the National Institutes of Health.")
    #st.markdown("🐾 []()")
    #st.markdown("🐾 []()")

# =========================================================
# TAB 3 — Download files
# =========================================================
with tab3:
    st.subheader("File download")
    st.markdown("+ [IPA chart 2015](https://github.com/MK316/classmaterial/raw/main/Phone/IPA_Kiel_2015.pdf): IPA chart")
    st.caption("➡️ This IPA chart contains symbols that were agreed upon to represent the sounds of all the world’s languages. It is not a chart made specifically for English.")
    st.divider()


# ================== Tips ==================
# - Each widget uses a unique key (e.g., app1_text) to avoid conflicts across tabs/pages.
# - Use st.form for groups of inputs you want to submit together.
# - For bigger apps per tab, factor logic into functions and call them inside the tab blocks.
# - You can add a common sidebar for shared settings across all tabs if needed.
