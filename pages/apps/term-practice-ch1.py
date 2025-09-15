import streamlit as st
import pandas as pd
import random
from gtts import gTTS
from io import BytesIO

# Load data
sheet_url = "https://raw.githubusercontent.com/MK316/classmaterial/main/Phonetics/ch01_glossary.csv"
df = pd.read_csv(sheet_url)

# App title
st.title("🧠 Term Practice App")

# Initialize session state
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None
if "show_meaning" not in st.session_state:
    st.session_state.show_meaning = False
if "selected_term" not in st.session_state:
    st.session_state.selected_term = None
if "term_list" not in st.session_state:
    st.session_state.term_list = []

# Tab1: Term list display with filters
tab1, tab2, tab3 = st.tabs(["Term List", "Practice Mode", "Quiz Mode"])

with tab1:
    st.write("This is the Term List tab")

with tab2:
    st.write("This is the Practice Mode tab")

with tab3:
    st.write("This is the Quiz Mode tab")

# Tab2: Random term practice
with st.tab("Random Practice"):
    st.subheader("🎲 Practice Random Term")

    def pick_random_term():
        st.session_state.selected_row = df.sample(1).iloc[0]
        st.session_state.show_meaning = False

    st.button("🎯 Pick a Random Term", on_click=pick_random_term)

    if st.session_state.selected_row is not None:
        row = st.session_state.selected_row
        st.markdown(f"### Hint: {row['Hint']}")

        if st.button("Show Meaning"):
            st.session_state.show_meaning = True

        if st.session_state.show_meaning:
            st.markdown(f"**Term:** {row['Term']}")
            st.markdown(f"**Meaning:** {row['Description']}")

# Tab3: Audio quiz
with st.tab("Audio Quiz"):
    st.subheader("🔊 Guess the Term from Description")

    def get_random_term():
        row = df.sample(1).iloc[0]
        st.session_state.selected_term = row

    if st.button("🔁 New Audio" ):
        get_random_term()

    if st.session_state.selected_term is not None:
        text = st.session_state.selected_term["Description"]
        tts = gTTS(text)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp.getvalue(), format="audio/mp3")

        answer = st.text_input("Your Answer:")
        if answer:
            correct = st.session_state.selected_term["Term"].strip().lower()
            if answer.strip().lower() == correct:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. The correct answer is: {correct}")
