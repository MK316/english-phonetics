import streamlit as st

st.set_page_config(page_title="Course Video Player", layout="wide")

# ---------------------------
# Tabs
# ---------------------------
tabs = st.tabs([
    "📘 Course videos",
    "📗 Lesson videos",
    "📙 Supplementary videos",
])

# ---------------------------
# Video lists (tab별로 분리)
# 👉 나중에 여기만 추가하면 됨
# ---------------------------
course_videos = {
    "Overview": "https://youtu.be/np2O9vzGFmA",
    # "Course Introduction": "https://youtu.be/xxxx",
}

lesson_videos = {
    "Chapter 1": "https://youtu.be/yyyy",
    "Chapter 2": "https://youtu.be/zzzz",
}

supplementary_videos = {
    "What is sound? [6m]": "https://www.youtube.com/watch?v=pcWiWjxhKE8",
    "How does the human body produce voice and speech? [4m]": "https://www.youtube.com/watch?v=JF8rlKuSoFM",
    "Vocal fold vibration while singing": "https://www.youtube.com/watch?v=3j92lXSwJHY",
    "Vocal anatomy": "https://www.youtube.com/watch?v=eyJVVdnCXko"
}

# ---------------------------
# Helper function
# ---------------------------
def video_selector(title, video_dict):
    st.subheader(title)

    video_title = st.selectbox(
        "Select a video",
        options=list(video_dict.keys()),
    )

    st.video(video_dict[video_title])

# ---------------------------
# Tab 1: Course videos
# ---------------------------
with tabs[0]:
    video_selector("Course videos", course_videos)

# ---------------------------
# Tab 2: Lesson videos
# ---------------------------
with tabs[1]:
    video_selector("Lesson videos", lesson_videos)

# ---------------------------
# Tab 3: Supplementary videos
# ---------------------------
with tabs[2]:
    video_selector("Supplementary videos", supplementary_videos)

  
