# ========== Imports (TOP OF FILE) ==========
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
# ==========================================


st.set_page_config(page_title="IPA Practice — Feature Classification", layout="centered")
st.title("IPA Practice — Feature Classification")

st.caption(
    "Choose features for each IPA symbol, then export a printable PDF. "
    "Oro-nasal includes *Not applicable*."
)

# If you already have tabs, you can wrap this block in `with tab2:`.

# ----- Header (persist) -----
colA, colB = st.columns(2)
with colA:
    group_name = st.text_input("Group", value=st.session_state.get("group_name", ""))
    st.session_state.group_name = group_name
with colB:
    student_name = st.text_input("Name", value=st.session_state.get("student_name", ""))
    st.session_state.student_name = student_name

st.divider()

# ----- Symbols & feature options -----
ipa_symbols = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]
feature_cols = ["Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

OPTIONS = {
    "Voicing": ["voiceless", "voiced"],
    "Place": ["bilabial", "labio-dental", "dental", "alveolar", "post-alveolar", "palatal", "velar", "glottal"],
    "Centrality": ["central", "lateral"],
    "Oro-nasal": ["oral", "nasal", "Not applicable"],   # << added option
    "Manner": ["stop", "fricative", "affricate", "approximant"],
}
DEFAULTS = {
    "Voicing": "voiceless",
    "Place": "bilabial",
    "Centrality": "central",
    "Oro-nasal": "oral",
    "Manner": "stop",
}

# ----- Initialize state ONCE (each cell gets a default) -----
if "ipa_selects" not in st.session_state:
    st.session_state.ipa_selects = {}
    for sym in ipa_symbols:
        for col in feature_cols:
            st.session_state.ipa_selects[f"{sym}__{col}"] = DEFAULTS[col]

# ----- Form (prevents reruns while choosing) -----
with st.form("ipa_select_form", clear_on_submit=False):
    # header row
    hdr = st.columns([0.7, 1.2, 1.6, 1.2, 1.4, 1.6])
    hdr[0].markdown("**IPA**")
    hdr[1].markdown("**Voicing**")
    hdr[2].markdown("**Place**")
    hdr[3].markdown("**Centrality**")
    hdr[4].markdown("**Oro-nasal**")
    hdr[5].markdown("**Manner**")

    for sym in ipa_symbols:
        cols = st.columns([0.7, 1.2, 1.6, 1.2, 1.4, 1.6])
        cols[0].markdown(f"**{sym}**")

        for i, col in enumerate(feature_cols, start=1):
            key = f"{sym}__{col}"
            opts = OPTIONS[col]
            current = st.session_state.ipa_selects.get(key, DEFAULTS[col])
            # The key stores the current selection; index only used first render
            cols[i].selectbox(
                col,
                options=opts,
                index=opts.index(current) if current in opts else 0,
                key=key,
                label_visibility="collapsed",
            )

    submitted = st.form_submit_button("Generate PDF", type="primary")

# ----- Build DataFrame only on submit -----
def selections_to_df():
    rows = []
    for sym in ipa_symbols:
        row = {"IPA": sym}
        for col in feature_cols:
            row[col] = st.session_state.ipa_selects.get(f"{sym}__{col}", DEFAULTS[col])
        rows.append(row)
    return pd.DataFrame(rows, columns=["IPA"] + feature_cols)

# ----- PDF helpers -----
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

    header = ["IPA"] + feature_cols
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

    col_widths = [35, 95, 120, 90, 110, 120]  # tuned for A4 portrait
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

# ----- Actions -----
if submitted:
    df_out = selections_to_df()
    st.session_state["last_df"] = df_out
    pdf_bytes = build_pdf(df_out, group_name, student_name)
    st.success("PDF ready. You can download it below.")
    st.download_button(
        "📥 Download PDF",
        data=pdf_bytes,
        file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.pdf",
        mime="application/pdf",
    )

if "last_df" in st.session_state:
    st.download_button(
        "Download CSV (backup)",
        data=st.session_state["last_df"].to_csv(index=False).encode("utf-8"),
        file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.csv",
        mime="text/csv",
    )
