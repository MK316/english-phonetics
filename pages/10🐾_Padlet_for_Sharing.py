import streamlit as st

st.set_page_config(page_title="Class Padlet Wall", layout="wide")

st.markdown("### 🧱 Class Padlet Wall")
st.markdown(
    """
    Use this space to view shared student work and follow assignment instructions.  
    If you are submitting or viewing work, click the Padlet button below to open it in a new tab.
    """
)

# Layout: left for instructions, right for Padlet link
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🔍 Assignment Instructions")
    st.markdown(
        """
        **Step 1:** Review your assignment prompt in the class LMS.  
        **Step 2:** Upload your work to the Padlet wall.  
        **Step 3:** Leave a brief comment on at least one peer's work.

        💡 *Be respectful and constructive in your feedback!*
        """
    )

with col2:
    st.markdown("### 🧩 Shared Work Padlet")
    st.markdown(
        """
        <a href="https://padlet.com/mirankim316/englishphonetics" target="_blank">
            <button style='padding:10px 20px; font-size:16px;'>Open Padlet Wall 🔗</button>
        </a>
        """,
        unsafe_allow_html=True,
    )
