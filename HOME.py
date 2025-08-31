import streamlit as st


st.markdown("### English Phonetics")

img = "https://github.com/MK316/english-phonetics/raw/main/pages/images/bg02.png"  # e.g., "images/figure.png" or a PIL Image

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(img, use_container_width=True)  # or: width=400

