# ===== Imports =====
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
st.set_page_config(page_title="IPA Practice — Feature Classification", layout="centered")
st.title("IPA Practice — Feature Classification")

st.caption("Select the correct features for each IPA symbol, then export a printable PDF.")

# ---- Header fields (persist) ----
cA, cB = st.columns(2)
with cA:
    group_name = st.text_input("Group", value=st.session_state.get("group_name", ""))
    st.session_state.group_name = group_name
with cB:
    student_name = st.text_input("Name", value=st.session_state.get("student_name", ""))
    st.session_state.student_name = student_name

st.divider()

# ---- IPA symbols ----
ipa_rows = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]

# ---- Dropdown options & defaults ----
OPTIONS = {
    "Voicing": ["voiceless", "voiced"],
    "Place": ["bilabial", "labiodental", "dental", "alveolar", "postalveolar", "palatal", "velar", "glottal"],
    "Centrality": ["central", "lateral"],
    "Oro-nasal": ["oral", "nasal"],
    "Manner": ["stop", "fricative", "affricate", "approximant"],
}
DEFAULTS = {k: v[0] for k, v in OPTIONS.items()}  # first option per column
columns = ["IPA", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

# ---- Initialize state once with real defaults (no None) ----
if "ipa_df" not in st.session_state:
    st.session_state.ipa_df = pd.DataFrame(
        {"IPA": ipa_rows, **{col: [DEFAULTS[col]] * len(ipa_rows) for col in OPTIONS}}
    )

# Keep a copy of pre-edit values to survive transient None during reruns
_prev_df = st.session_state.ipa_df.copy(deep=True)

# ---- Data editor with SelectboxColumn (no empty option) ----
col_config = {
    "IPA": st.column_config.Column(label="IPA", disabled=True),
    "Voicing": st.column_config.SelectboxColumn(
        label="Voicing", options=OPTIONS["Voicing"], required=True, default=DEFAULTS["Voicing"]
    ),
    "Place": st.column_config.SelectboxColumn(
        label="Place", options=OPTIONS["Place"], required=True, default=DEFAULTS["Place"]
    ),
    "Centrality": st.column_config.SelectboxColumn(
        label="Centrality", options=OPTIONS["Centrality"], required=True, default=DEFAULTS["Centrality"]
    ),
    "Oro-nasal": st.column_config.SelectboxColumn(
        label="Oro-nasal", options=OPTIONS["Oro-nasal"], required=True, default=DEFAULTS["Oro-nasal"]
    ),
    "Manner": st.column_config.SelectboxColumn(
        label="Manner", options=OPTIONS["Manner"], required=True, default=DEFAULTS["Manner"]
    ),
}

edited_df = st.data_editor(
    st.session_state.ipa_df,
    use_container_width=True,
    hide_index=True,
    column_order=columns,
    column_config=col_config,
    num_rows="fixed",
    key="ipa_editor",
)

# ---- Reconcile choices AFTER edit: keep user value if valid; else keep previous valid; else default ----
for col, valid in OPTIONS.items():
    prev_col = _prev_df[col].tolist()
    new_vals = []
    for new_val, prev_val in zip(edited_df[col].tolist(), prev_col):
        if new_val in valid:
            new_vals.append(new_val)
        elif prev_val in valid:
            new_vals.append(prev_val)
        else:
            new_vals.append(DEFAULTS[col])
    edited_df[col] = new_vals

# Persist the reconciled DataFrame
st.session_state.ipa_df = edited_df

st.divider()

# ---- PDF builder (portrait A4) with timestamp; tries to use a Unicode font if present ----
def _find_unicode_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "fonts/DejaVuSans.ttf",
        "fonts/NotoSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("UnicodeBase", p))
                return "UnicodeBase"
            except Exception:
                pass
    return "Helvetica"  # fallback (some IPA glyphs may not render)

def build_pdf(df: pd.DataFrame, group_name: str, student_name: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,  # portrait
        leftMargin=24, rightMargin=24, topMargin=28, bottomMargin=28,
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

    # Table (keep IPA glyphs as-is)
    header = ["IPA", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]
    table_data = [header]
    for _, row in df.iterrows():
        table_data.append([
            Paragraph(str(row["IPA"]), cell_style),
            Paragraph(str(row["Voicing"]), cell_style),
            Paragraph(str(row["Place"]), cell_style),
            Paragraph(str(row["Centrality"]), cell_style),
            Paragraph(str(row["Oro-nasal"]), cell_style),
            Paragraph(str(row["Manner"]), cell_style),
        ])

    # Column widths tuned for A4 portrait
    col_widths = [40, 95, 115, 90, 95, 115]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f2f6")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (0,-1), "CENTER"),  # IPA column centered
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfbfb")]),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(tbl)

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

# ---- Actions ----
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    if st.button("Export to PDF", type="primary"):
        pdf_bytes = build_pdf(st.session_state.ipa_df, group_name, student_name)
        st.success("PDF ready.")
        st.download_button(
            "📥 Download PDF",
            data=pdf_bytes,
            file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
with col_dl2:
    st.download_button(
        "Download CSV (backup)",
        data=st.session_state.ipa_df.to_csv(index=False).encode("utf-8"),
        file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.csv",
        mime="text/csv",
    )
