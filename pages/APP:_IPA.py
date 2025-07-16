import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="IPA Typing Tool", layout="wide")

st.markdown("## 🍊 [fənɛɾɪks]: IPA TypeIt Tool (Embedded)")
st.markdown("You can use the full IPA keyboard below to input phonetic transcriptions.")

# Embed the external IPA tool
components.iframe("https://ipa.typeit.org/full/", height=700, scrolling=True)
