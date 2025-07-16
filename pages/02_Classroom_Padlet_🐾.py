import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Class Padlet Wall", layout="wide")

st.markdown("### 🧱 Class Padlet Wall")
st.markdown(
    """
    Use this space to view shared student work and follow assignment instructions.  
    If you are submitting or viewing work, scroll through the Padlet embedded on the right.
    """
)

# Layout: left for instructions, right for embedded Padlet
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🔍 Assignment Instructions")
    st.markdown(
        """
        **Step 1:** Review your assignment prompt in the class LMS.  
        **Step 2:** Upload your work to the Padlet wall below.  
        **Step 3:** Leave a brief comment on at least one peer's work.

        💡 *Be respectful and constructive in your feedback!*
        """
    )

with col2:
    st.markdown("### 🧩 Shared Work Padlet")
    components.iframe(
        "https://padlet.com/mirankim316/englishphonetics",  # ← Replace with your actual Padlet URL
        height=600,
        scrolling=True
    )
