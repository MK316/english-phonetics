import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="🎵 Pop Song Transcription Project", layout="centered")
st.title("🎵 Group Project: Pop Song Transcription")
st.markdown("Select a song from the dropdown to watch and transcribe it.")
st.write("Submit to Padlet by midnight on 11/7 (Thursday)")
# ---------------- Song list ----------------
songs = {
    "Lemon tree (G1)": "https://youtu.be/XAFS43NKFag?si=r-2uDkTIS4PJ0tV-",
    "Top of the world (G2)": "https://youtu.be/9BgNVW4T1eo?si=KisjV1uQo3XLkzYV",
    "Let it be": "https://youtu.be/QDYfEBY9NM4?si=q71fkO1Sf09ThjG1",
    "Itsy Bitsy Teenie Weenie Yellow Polka Dot Bikini": "https://youtu.be/lpv-RGZJjP0?si=6jGak4n6QbWvJYrY",
    "You are my sunshine (G3)": "https://youtu.be/5TUzB2fBUpY?si=WNnRAo2Z-nFTkkam",
    "Yesterday once more": "https://youtu.be/pteksK4GtCE?si=liQDKZ9TGE7nVfKt",
    "Let it go (G5)": "https://www.youtube.com/embed/HV6Rg2SKDfg?si=QmV6uScQV-UQDlta",
    "Golden (G4)": "https://www.youtube.com/embed/66ypgOAMGpU?si=ih5gMtgnk8lBokjE"
}

# Replace with your shared Google Sheet link
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EtXckbP8BtkeoHEqUc0KFv5xarUgegm8rJ-Ri0rloQo/edit?usp=sharing"

# ---------------- Dropdown ----------------
song_choice = st.selectbox("🎶 Choose a song", ["-- Select a song --"] + list(songs.keys()))

# ---------------- Display video ----------------
if song_choice != "-- Select a song --":
    st.video(songs[song_choice], format="video/mp4", start_time=0)

    st.markdown("✏️ **Instructions**: Notify when your group decides which one to pick (by 9/23).")

    # ---------------- Google Sheet Button ----------------
    st.link_button("📑 Open Group Transcription Sheet", GOOGLE_SHEET_URL)
