import streamlit as st
import requests
import re

st.markdown("#### Chapter 1. Articulation and Acoustics")

st.set_page_config(page_title="Lecture Slides (Folder)", layout="wide")
st.title("📚 Lecture Slide Player — Folder Mode")

# ---------------------------
# CONFIG: set your GitHub folder here
# ---------------------------
GITHUB_OWNER  = "MK316"        # e.g., "MK316"
GITHUB_REPO   = "english-phonetics"        # e.g., "LectureSlides"
GITHUB_BRANCH = "pages"        # e.g., "main" or "master"
FOLDER_PATH   = "lecture/Ch1"      # e.g., "slides/week01"

# File extensions to include
VALID_EXTS = (".jpeg")

# ---------------------------
# Helpers
# ---------------------------
def natural_key(s: str):
    """Sort key that handles numbers inside filenames naturally."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

@st.cache_data(show_spinner=False, ttl=60*10)
def list_github_images(owner: str, repo: str, folder: str, branch: str):
    """
    Return a naturally sorted list of RAW URLs for images in a GitHub folder.
    Uses the public GitHub API (no token required for public repos).
    """
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={branch}"
    r = requests.get(api, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(
            f"GitHub API error {r.status_code}: {r.text[:200]} \n"
            f"Check owner/repo/branch/path."
        )
    items = r.json()
    files = [it for it in items if it.get("type") == "file" and it["name"].lower().endswith(VALID_EXTS)]
    # natural sort by filename
    files.sort(key=lambda x: natural_key(x["name"]))
    # convert to RAW URLs
    raw_base = f"https://raw.github_
