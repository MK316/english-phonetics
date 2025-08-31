import re
import requests
import streamlit as st

st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.header("📚 Chapter 1: Articulation and Acoustics")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
# Folder you expect the images to be under (match is case-insensitive & flexible)
FOLDER_PATH   = "pages/lecture/Ch01"
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")
DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10
# ---------------------------------

def natural_key(s: str):
    """Sort like humans (slide2 before slide10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _auth_headers():
    # Optional: add GITHUB_TOKEN in Streamlit Secrets to avoid rate limits
    # Settings → Secrets: GITHUB_TOKEN = "ghp_xxx..."
    token = st.secrets.get("GITHUB_TOKEN", None)
    return {"Authorization": f"token {token}"} if token else {}

def _mk_raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

@st.cache_data(show_spinner=False, ttl=600)
def list_images(owner: str, repo: str, folder: str, branch: str):
    """
    1) Try GitHub contents API with pagination
    2) Fall back to git/trees API (recursive) and match folder path anywhere
    Returns (urls, names). Also returns a debug dict to help diagnose.
    """
    headers = _auth_headers()
    debug = {"phase": "", "hits": 0, "samples": []}

    # -------- Try 1: contents API with pagination (fastest when folder path is exact) ----------
    files = []
    page = 1
    while True:
        api = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}"
            f"?ref={branch}&per_page=100&page={page}"
        )
        r = requests.get(api, headers=headers, timeout=20)
        if r.status_code != 200:
            files = None
            break

        batch = r.json()
        if not isinstance(batch, list):
            files = None
            break
        if not batch:
            break

        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    if files:
        valid = [
            it for it in files
            if it.get("type") == "file"
            and it.get("name", "").lower().endswith(VALID_EXTS)
        ]
        valid.sort(key=lambda x: natural_key(x["name"]))
        urls  = [_mk_raw_url(owner, repo, branch, f"{folder.rstrip('/')}/{f['name']}") for f in valid]
        names = [f["name"] for f in valid]
        if urls:
            debug.update({"phase": "contents_api", "hits": len(urls), "samples": names[:5]})
            return urls, names, debug

    # -------- Try 2: git/trees API (recursive list of the whole repo) ----------
    tree_api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    r = requests.get(tree_api, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"GitHub API error {r.status_code} while listing files.\n"
            f"Tip: add GITHUB_TOKEN to Secrets to avoid rate limits."
        )
    data = r.json()
    tree = data.get("tree", [])

    # Build a flexible, case-insensitive regex for the folder path segments
    # e.g., "pages/lecture/Ch01" -> match .../pages/lecture/Ch01/... or any case variant
    segs = [re.escape(seg) for seg in folder.strip("/").split("/")]
    # Allow anything before, exact segments in order, then filename
    folder_regex = re.compile(r"(^|.*/)" + r"/".join(segs) + r"/[^/]+\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

    hits = [
        it["path"] for it in tree
        if it.get("type") == "blob"
        and it.get("path")
        and it["path"].lower().endswith(VALID_EXTS)
        and folder_regex.search(it["path"]) is not None
    ]

    if not hits:
        # As a last resort, try to match only the last segment of the folder (e.g., "Ch01")
        last_seg = re.escape(segs[-1]) if segs else ""
        loose_regex = re.compile(rf"(^|.*/){last_seg}/[^/]+\.(png|jpg|jpeg|webp)$", re.IGNORECASE)
        hits = [
            it["path"] for it in tree
            if it.get("type") == "blob"
            and it.get("path")
            and it["path"].lower().endswith(VALID_EXTS)
            and loose_regex.search(it["path"]) is not None
        ]

    hits.sort(key=lambda p: natural_key(p.rsplit("/", 1)[-1]))
    urls  = [_mk_raw_url(owner, repo, branch, p) for p in hits]
    names = [p.rsplit("/", 1)[-1] for p in hits]

    debug.update({"phase": "trees_api", "hits": len(urls), "samples": hits[:5]})
    if not urls:
        raise RuntimeError(
            "No image files found via contents or trees API.\n"
            "Please verify FOLDER_PATH and file extensions."
        )
    return urls, names, debug

# ---------- Load slide list ----------
try:
    slides, filenames, dbg = list_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
except Exception as e:
    st.error(f"❌ Could not list images: {e}")
    st.info(
        "Tips:\n"
        "• Double-check
