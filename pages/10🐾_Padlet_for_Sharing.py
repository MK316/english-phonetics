import streamlit as st
st.set_page_config(page_title="Class Padlet Wall", layout="wide")

st.header("🐾 Q & As: on Padlet")
st.write("This Padlet serves as a dynamic hub for Q & As regarding the course. Personal inquiries can be directred via E-mail at mirankim@gnu.ac.kr")
st.components.v1.iframe("https://padlet.com/mirankim316/engphonetics", width=700, height=600)
