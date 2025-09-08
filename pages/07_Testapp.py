# ===== Imports (top of file) =====
from io import BytesIO
from datetime import datetime
import os

import streamlit as st
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ===== App setup =====
st.set_page_config(page_title="IPA Practice — Step-by-Step", layout="centered")
st.title("IPA Practice — Step-by-Step Feature Classification")

st.caption(
    "Work through the five steps. Each step shows one feature for all symbols. "
    "At the end, you’ll see correctness, feedback, and a PDF download."
)

# ----- Header info (persist) -----
cA, cB = st.columns(2)
with cA:
    group_name = st.text_input("Group", value=st.session_state.get("group_name", ""))
    st.session_state.group_name = group_name
with cB:
    student_name = st.text_input("Name", value=st.session_state.get("student_name", ""))
    st.session_state.student_name = student_name

st.divider()

# ===== Data / options =====
FEATURES_ORDER = ["Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

ipa_symbols = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]

# Options (as requested): Centrality has "Not applicable"; Oro-nasal no longer has it
OPTIONS = {
    "Voicing": ["voiceless", "voiced"],
    "Place": ["bilabial", "labio-dental", "dental", "alveolar", "post-alveolar", "palatal", "velar", "glottal"],
    "Centrality": ["central", "lateral", "Not applicable"],
    "Oro-nasal": ["oral", "nasal"],
    "Manner": ["stop", "fricative", "affricate", "approximant"],
}
DEFAULTS = {
    "Voicing": "voiceless",
    "Place": "bilabial",
    "Centrality": "central",
    "Oro-nasal": "oral",
    "Manner": "stop",
}

# A simple answer key that fits your option sets
# Note: in this schema, nasals are marked "approximant" for Manner and "nasal" under Oro-nasal.
ANSWER_KEY = {
    "p":  {"Voicing":"voiceless","Place":"bilabial","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "b":  {"Voicing":"voiced","Place":"bilabial","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "t":  {"Voicing":"voiceless","Place":"alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "d":  {"Voicing":"voiced","Place":"alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "k":  {"Voicing":"voiceless","Place":"velar","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "g":  {"Voicing":"voiced","Place":"velar","Centrality":"central","Oro-nasal":"oral","Manner":"stop"},
    "f":  {"Voicing":"voiceless","Place":"labio-dental","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "v":  {"Voicing":"voiced","Place":"labio-dental","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "θ":  {"Voicing":"voiceless","Place":"dental","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "ð":  {"Voicing":"voiced","Place":"dental","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "s":  {"Voicing":"voiceless","Place":"alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "z":  {"Voicing":"voiced","Place":"alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "ʃ":  {"Voicing":"voiceless","Place":"post-alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "ʒ":  {"Voicing":"voiced","Place":"post-alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "tʃ": {"Voicing":"voiceless","Place":"post-alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"affricate"},
    "dʒ": {"Voicing":"voiced","Place":"post-alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"affricate"},
    "h":  {"Voicing":"voiceless","Place":"glottal","Centrality":"central","Oro-nasal":"oral","Manner":"fricative"},
    "m":  {"Voicing":"voiced","Place":"bilabial","Centrality":"central","Oro-nasal":"nasal","Manner":"approximant"},
    "n":  {"Voicing":"voiced","Place":"alveolar","Centrality":"central","Oro-nasal":"nasal","Manner":"approximant"},
    "ŋ":  {"Voicing":"voiced","Place":"velar","Centrality":"central","Oro-nasal":"nasal","Manner":"approximant"},
    "ɹ":  {"Voicing":"voiced","Place":"post-alveolar","Centrality":"central","Oro-nasal":"oral","Manner":"approximant"},
    "l":  {"Voicing":"voiced","Place":"alveolar","Centrality":"lateral","Oro-nasal":"oral","Manner":"approximant"},
    "j":  {"Voicing":"voiced","Place":"palatal","Centrality":"central","Oro-nasal":"oral","Manner":"approximant"},
    "w":  {"Voicing":"voiced","Place":"velar","Centrality":"central","Oro-nasal":"oral","Manner":"approximant"},
}

# ===== State init =====
if "step" not in st.session_state:
    st.session_state.step = 0  # 0..4 => feature steps; 5 => results
if "selections" not in st.session_state:
    st.session_state.selections = {
        feat: {sym: DEFAULTS[feat] for sym in ipa_symbols} for feat in FEATURES_ORDER
    }

# ===== Helper: render one-step form =====
def render_step(feature_name: str):
    pretty = feature_name
    help_text = {
        "Voicing": "Choose voiced / voiceless.",
        "Place": "Choose one place of articulation.",
        "Centrality": "Choose central / lateral / Not applicable.",
        "Oro-nasal": "Choose oral / nasal.",
        "Manner": "Choose stop / fricative / affricate / approximant.",
    }[feature_name]

    st.markdown(f"### Step {st.session_state.step + 1} of 5 — {pretty}")
    st.caption(help_text)

    with st.form(f"form_{feature_name}", clear_on_submit=False):
        # header
        hdr = st.columns([0.7, 2.5])
        hdr[0].markdown("**IPA**")
        hdr[1].markdown(f"**{pretty}**")

        for sym in ipa_symbols:
            cols = st.columns([0.7, 2.5])
            cols[0].markdown(f"**{sym}**")
            current = st.session_state.selections[feature_name][sym]
            cols[1].selectbox(
                label=feature_name,
                options=OPTIONS[feature_name],
                index=OPTIONS[feature_name].index(current) if current in OPTIONS[feature_name] else 0,
                key=f"sel__{feature_name}__{sym}",
                label_visibility="collapsed",
            )

        next_label = "Finish & Check" if feature_name == "Manner" else "Next ▶️"
        submitted = st.form_submit_button(next_label, type="primary")

    if submitted:
        # save choices back to selections
        for sym in ipa_symbols:
            st.session_state.selections[feature_name][sym] = st.session_state.get(
                f"sel__{feature_name}__{sym}", st.session_state.selections[feature_name][sym]
            )
        # go to next stage
        st.session_state.step += 1
        st.experimental_rerun()

# ===== Helper: build user DataFrame from selections =====
def selections_to_df():
    data = []
    for sym in ipa_symbols:
        row = {"IPA": sym}
        for feat in FEATURES_ORDER:
            row[feat] = st.session_state.selections[feat][sym]
        data.append(row)
    return pd.DataFrame(data, columns=["IPA"] + FEATURES_ORDER)

# ===== PDF helpers =====
def _find_unicode_font():
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "fonts/DejaVuSans.ttf",
        "fonts/NotoSans-Regular.ttf",
    ]:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("UnicodeBase", p))
                return "UnicodeBase"
            except Exception:
                pass
    return "Helvetica"

def build_pdf(df: pd.DataFrame, group_name: str, student_name: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=28, bottomMargin=28,
        title="IPA Practice"
    )
    base_font = _find_unicode_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading2"], fontName=base_font, spaceAfter=6)
    meta_style  = ParagraphStyle("Meta",  parent=styles["Normal"],   fontName=base_font, fontSize=9, spaceAfter=10)
    cell_style  = ParagraphStyle("Cell",  parent=styles["BodyText"], fontName=base_font, fontSize=9, leading=11)

    elements = []
    elements.append(Paragraph("IPA Practice — Feature Classification", title_style))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    elements.append(Paragraph(
        f"Group: {group_name or ''} &nbsp;&nbsp; Name: {student_name or ''} &nbsp;&nbsp; Exported: {ts}",
        meta_style
    ))
    elements.append(Spacer(1, 6))

    header = ["IPA"] + FEATURES_ORDER
    data = [header]
    for _, r in df.iterrows():
        data.append([
            Paragraph(str(r["IPA"]), cell_style),
            Paragraph(str(r["Voicing"]), cell_style),
            Paragraph(str(r["Place"]), cell_style),
            Paragraph(str(r["Centrality"]), cell_style),
            Paragraph(str(r["Oro-nasal"]), cell_style),
            Paragraph(str(r["Manner"]), cell_style),
        ])

    col_widths = [35, 90, 120, 100, 90, 120]
    tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f2f6")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfbfb")]),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(tbl)

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

# ===== Flow control =====
if st.session_state.step < len(FEATURES_ORDER):
    # render the current step
    render_step(FEATURES_ORDER[st.session_state.step])
else:
    # ===== Results =====
    st.markdown("### Results")
    df_user = selections_to_df()

    # Build the answer DataFrame aligned to user DF
    df_ans = pd.DataFrame(
        [{"IPA": sym, **ANSWER_KEY[sym]} for sym in ipa_symbols],
        columns=["IPA"] + FEATURES_ORDER
    )

    # Compare for correctness (feature columns only)
    wrong_mask = pd.DataFrame(False, index=df_user.index, columns=df_user.columns)
    for feat in FEATURES_ORDER:
        wrong_mask[feat] = df_user[feat] != df_ans[feat]
    # IPA column never styled as wrong
    wrong_mask["IPA"] = False

    # Style: wrong cells black + white text
    def _style_wrong(df: pd.DataFrame):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        styles = styles.mask(wrong_mask, other="background-color: black; color: white;")
        return styles

    styled = df_user.style.apply(_style_wrong, axis=None)
    st.write(styled)

    # Feedback list
    incorrect_rows = []
    for i, sym in enumerate(df_user["IPA"]):
        wrong_feats = [feat for feat in FEATURES_ORDER if wrong_mask.loc[i, feat]]
        if wrong_feats:
            detail = ", ".join(
                f"{feat}: expected {df_ans.loc[i, feat]} / got {df_user.loc[i, feat]}"
                for feat in wrong_feats
            )
            incorrect_rows.append(f"• **{sym}** — {detail}")

    if incorrect_rows:
        st.error("Some entries need review:")
        st.markdown("\n".join(incorrect_rows))
    else:
        st.success("🎉 All correct!")

    st.divider()

    # Generate PDF + download
    if st.button("Generate PDF", type="primary"):
        pdf_bytes = build_pdf(df_user, group_name, student_name)
        st.download_button(
            "📥 Download PDF",
            data=pdf_bytes,
            file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.pdf",
            mime="application/pdf",
        )

    # Optional: restart
    st.button("Start Over", on_click=lambda: st.session_state.update(step=0))
