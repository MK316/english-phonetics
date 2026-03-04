import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="📘 16-Week Course Schedule", layout="wide")
st.title("📘 Course Overview")
st.markdown("[Syllabus](https://github.com/MK316/english-phonetics/raw/main/pages/data/fSyllabus_2026S_Phonetics.pdf)")

tab1, tab2, tab3, tab4 = st.tabs(["🐾 Schedule", "🐾 Syllabus", "🐾 Assignments", "🐾 Group Quest"])

# =========================================================
# Tab 1: Schedule (Google Sheet)
# Columns expected: Date, Chapter, Keywords, Assignments, Next time
# =========================================================
with tab1:
    st.header("📅 Course Schedule")
    st.markdown("🔗 [Google Sheet](https://docs.google.com/spreadsheets/d/1DjmI_dUh1a51Wz9Z7_eY228kAteVfF89Mm3pBGVw9m8/edit?usp=sharing)")

    SHEET_ID = "1DjmI_dUh1a51Wz9Z7_eY228kAteVfF89Mm3pBGVw9m8"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

    @st.cache_data(show_spinner=False)
    def load_schedule(csv_url: str) -> pd.DataFrame:
        df = pd.read_csv(csv_url)
        df.columns = [c.strip() for c in df.columns]

        # ✅ Now includes Day
        required = ["Week", "Date", "Day", "Chapter", "Keywords", "Assignments", "Next time"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in Google Sheet: {missing}\nExpected: {required}")

        # Parse Date
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # ✅ Fix Week ordering: extract numeric week for sorting
        # Works for "Week 1", "Week1", "1", etc.
        week_num = (
            df["Week"]
            .astype(str)
            .str.extract(r"(\d+)", expand=False)
        )
        df["_week_num"] = pd.to_numeric(week_num, errors="coerce")

        # Sort by week number → date
        df = df.sort_values(["_week_num", "Date"], na_position="last").reset_index(drop=True)

        # Display-friendly Date
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        # Clean NaN
        for col in required:
            df[col] = df[col].fillna("")

        # Remove helper column
        df = df.drop(columns=["_week_num"])

        # ✅ Optional: force column order (Day is 3rd)
        df = df[["Week", "Date", "Day", "Chapter", "Keywords", "Assignments", "Next time"]]

        return df

    try:
        schedule_df = load_schedule(CSV_URL)

        q = st.text_input(
            "Filter (any keyword):",
            placeholder="e.g., Week 3, Monday, Ch. 2, quiz, transcription…"
        ).strip().lower()

        if q:
            mask = schedule_df.apply(
                lambda row: row.astype(str).str.lower().str.contains(q).any(),
                axis=1
            )
            view_df = schedule_df[mask].copy()
        else:
            view_df = schedule_df.copy()

        st.dataframe(
            view_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Week": st.column_config.Column(width=70),
                "Date": st.column_config.Column(width=95),
                "Day": st.column_config.Column(width=70),
                "Chapter": st.column_config.Column(width=90),
                "Keywords": st.column_config.Column(width="medium"),
                "Assignments": st.column_config.Column(width="large"),
                "Next time": st.column_config.Column(width="large"),
            },
        )

        st.caption("✔️ Update the Google Sheet anytime — this table always shows the latest version.")

    except Exception as e:
        st.error("Failed to load the Google Sheet schedule.")
        st.code(str(e))
        st.info(
            "If this is not the first sheet tab, change `gid=0` in the CSV URL.\n"
            "Open the sheet → click the tab → check the `gid=` value in the URL."
        )

# ---------------- Tab 2: Syllabus / Course Info ----------------
with tab2:
    st.markdown("## 💦 **English Phonetics (Spring 2026)**")
    st.caption("Quick syllabus overview")

    col1, col2 = st.columns([3, 2], vertical_alignment="top")

    with col1:
        st.markdown(
            """
            **• Instructor:** Miran Kim (Professor, Rm# 301-316)  
            **• Meeting Schedule:** Mondays (11–11:50 am) & Thursdays (9–10:50 am)  
            **• Digital classroom:** [MK316.github.io](https://englishphonetics.streamlit.app)  — course apps & resources  
            **• LMS:** rec.ac.kr/gnu  
            **• Classroom:** 301-334   
            """,
        )

    with col2:
        QR_URL = "https://github.com/MK316/english-phonetics/raw/main/pages/images/qr_phonetics.png"
        st.image(QR_URL, caption="Digital classroom QR", width=150)

    st.divider()

    st.markdown("### 📝 Course overview")
    st.markdown(
        """
        This course introduces the fundamental aspects of the English sound system with an emphasis on its application to learning and teaching English pronunciation. It covers the basic phonetic properties of English speech sounds, including consonants and vowels, along with essential concepts necessary for understanding the sound system. Additionally, the course delves into English prosody, which includes the study of syllables, rhythm, and intonation. Students will engage in practical exercises, such as phonetic transcriptions of spoken English data, to develop skills in teaching pronunciation. They will also learn to differentiate between connected and isolated speech, as well as formal and informal speech, throughout the course.

        """
    )
    AUDIO_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/audio/phonetics-overview.mp3"
    st.audio(AUDIO_URL, format="audio/mp3", start_time=0)

    st.markdown("### 📚 Textbook & Software")
    tb, sw = st.columns(2)
    with tb:
        st.markdown(
            """
            **Textbook**  
            Johnson, K. & Ladefoged, P. (2014). *A Course in Phonetics* (7th ed.). CENGAGE Learning.
            """
        )
    with sw:
        st.markdown(
            """
            **Software**  
            Praat — download: <http://www.fon.hum.uva.nl/praat/download_win.html>
            """
        )

    st.divider()

    st.markdown("### ✅ Evaluation")
    data = [
        ["Attendance & class participation", "10%", "Unexcused absence (−1); late check-in (−0.2)"],
        ["Exam", "70%", "Midterm (30) + Final (40) exam"],
        ["Assignments", "20%", "Group activities: Exercises (5), Transcription (5)"]
    ]
    df_eval = pd.DataFrame(data, columns=["Component", "Percentage", "Notes"])

    st.dataframe(
        df_eval,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Component": st.column_config.Column(width="medium"),
            "Percentage": st.column_config.Column(width=90),
            "Notes": st.column_config.Column(width="large"),
        },
    )

    st.info("Note: The course schedule can be subject to change. Most updates will be posted here.")

# ---------------- Tab 3: Assignments ----------------
with tab3:
    st.header("🧩 Assignments")
    st.caption("Add your assignments page content here.")

with tab4:
    st.caption("Bonus points earned through teamwork and class activities. Stay active, collaborate, and watch your Group Quest score grow!")
    st.markdown("👉 [Current status](https://docs.google.com/spreadsheets/d/1DjmI_dUh1a51Wz9Z7_eY228kAteVfF89Mm3pBGVw9m8/edit?usp=sharing)")
