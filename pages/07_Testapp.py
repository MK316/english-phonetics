import streamlit as st
# --- Imports (put these at the top of the file) ---
from io import BytesIO

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

tab1, tab2=st.tabs(["tab1","tab2"])

# ---------------- Tab 2 ----------------

with tab1:
    st.subheader("IPA Practice — Describe each symbol")

    # ---- Header fields ----
    colA, colB = st.columns(2)
    with colA:
        group_name = st.text_input("Group", value=st.session_state.get("group_name", ""))
        st.session_state.group_name = group_name
    with colB:
        student_name = st.text_input("Name", value=st.session_state.get("student_name", ""))
        st.session_state.student_name = student_name

    st.caption("Select values for Voicing, Place, Centrality, Oro-nasal, and Manner for each IPA symbol.")

    # ---- IPA symbols (left column) ----
    ipa_rows = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]

    # ---- Dropdown options ----
    OPTIONS = {
        "Voicing": ["voiceless", "voiced"],
        "Place": ["bilabial", "labiodental", "dental", "alveolar", "postalveolar", "palatal", "velar", "glottal"],
        "Centrality": ["central", "lateral"],
        "Oro-nasal": ["oral", "nasal"],
        "Manner": ["stop", "fricative", "affricate", "approximant"],
    }
    columns = ["IPA", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

    # ---- Initialize (persist across reruns) ----
    if "ipa_df" not in st.session_state:
        st.session_state.ipa_df = pd.DataFrame(
            {
                "IPA": ipa_rows,
                "Voicing": [None] * len(ipa_rows),
                "Place": [None] * len(ipa_rows),
                "Centrality": [None] * len(ipa_rows),
                "Oro-nasal": [None] * len(ipa_rows),
                "Manner": [None] * len(ipa_rows),
            }
        )

    # ---- Column configs: Selectbox for each feature; lock IPA column ----
    col_config = {
        "IPA": st.column_config.Column(label="IPA", disabled=True),
        "Voicing": st.column_config.SelectboxColumn(
            label="Voicing", options=OPTIONS["Voicing"], required=False, default=None
        ),
        "Place": st.column_config.SelectboxColumn(
            label="Place", options=OPTIONS["Place"], required=False, default=None
        ),
        "Centrality": st.column_config.SelectboxColumn(
            label="Centrality", options=OPTIONS["Centrality"], required=False, default=None
        ),
        "Oro-nasal": st.column_config.SelectboxColumn(
            label="Oro-nasal", options=OPTIONS["Oro-nasal"], required=False, default=None
        ),
        "Manner": st.column_config.SelectboxColumn(
            label="Manner", options=OPTIONS["Manner"], required=False, default=None
        ),
    }

    edited_df = st.data_editor(
        st.session_state.ipa_df,
        use_container_width=True,
        hide_index=True,
        column_order=columns,
        column_config=col_config,
        num_rows="fixed",
        key="ipa_editor",  # stable key to avoid resets
    )

    # Persist latest edits
    st.session_state.ipa_df = edited_df

    st.divider()

    # ---- PDF builder (portrait A4) with timestamp & IPA support ----
    def _find_unicode_font():
        """
        Try to use a Unicode font that covers IPA. If none is found,
        fall back to Helvetica (some symbols may not render).
        """
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",          # common on Linux
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "fonts/DejaVuSans.ttf",  # bundled path (if you ship it)
            "fonts/NotoSans-Regular.ttf",
        ]
        for p in candidates:
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
        elements.append(Paragraph(f"Group: {group_name or ''} &nbsp;&nbsp; Name: {student_name or ''} &nbsp;&nbsp; "
                                  f"Exported: {ts}", meta_style))
        elements.append(Spacer(1, 6))

        # Table header & data (keep IPA glyphs as-is)
        header = ["IPA", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]
        table_data = [header]
        for _, row in df.iterrows():
            table_data.append([
                Paragraph(str(row["IPA"]), cell_style),
                Paragraph("" if pd.isna(row["Voicing"]) else str(row["Voicing"]), cell_style),
                Paragraph("" if pd.isna(row["Place"]) else str(row["Place"]), cell_style),
                Paragraph("" if pd.isna(row["Centrality"]) else str(row["Centrality"]), cell_style),
                Paragraph("" if pd.isna(row["Oro-nasal"]) else str(row["Oro-nasal"]), cell_style),
                Paragraph("" if pd.isna(row["Manner"]) else str(row["Manner"]), cell_style),
            ])

        # Column widths tuned for portrait A4
        col_widths = [40, 90, 110, 90, 90, 110]

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

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Export to PDF", type="primary"):
            pdf_bytes = build_pdf(st.session_state.ipa_df, group_name, student_name)
            st.success("PDF ready.")
            st.download_button(
                "📥 Download PDF",
                data=pdf_bytes,
                file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
    with c2:
        st.download_button(
            "Download CSV (backup)",
            data=st.session_state.ipa_df.to_csv(index=False).encode("utf-8"),
            file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.csv",
            mime="text/csv",
        )
