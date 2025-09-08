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
st.caption("Pick features for each IPA symbol, then export a printable PDF.")

tab1, tab2 = st.tabs(["tab1","tab2"])
# ---------------- Tab 2 ----------------
with tab2:
    # ===== Imports (safe to keep at top of your file too) =====
    from io import BytesIO
    from datetime import datetime
    import os
    import pandas as pd
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    st.subheader("IPA Practice — Type feature descriptions (stable text boxes)")

    # ----- Header fields (persist) -----
    c1, c2 = st.columns(2)
    with c1:
        group_name = st.text_input("Group", value=st.session_state.get("group_name", ""))
        st.session_state.group_name = group_name
    with c2:
        student_name = st.text_input("Name", value=st.session_state.get("student_name", ""))
        st.session_state.student_name = student_name

    st.caption(
        "Type the features for each symbol. Suggestions: "
        "Voicing (voiced/voiceless), Place (bilabial…glottal), Centrality (central/lateral), "
        "Oro-nasal (oral/nasal), Manner (stop/fricative/affricate/approximant)."
    )

    # ----- Symbols & columns -----
    ipa_symbols = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]
    feat_cols   = ["Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

    # Prime session defaults (once)
    if "ipa_text_values" not in st.session_state:
        st.session_state.ipa_text_values = {}
        for sym in ipa_symbols:
            for col in feat_cols:
                st.session_state.ipa_text_values[f"{sym}__{col}"] = ""

    # ----- Build the input grid inside a FORM (no reruns while typing) -----
    with st.form("ipa_text_form", clear_on_submit=False):
        # header row
        h = st.columns([0.7, 1.2, 1.6, 1.2, 1.2, 1.6])
        h[0].markdown("**IPA**")
        h[1].markdown("**Voicing**")
        h[2].markdown("**Place**")
        h[3].markdown("**Centrality**")
        h[4].markdown("**Oro-nasal**")
        h[5].markdown("**Manner**")

        for sym in ipa_symbols:
            c = st.columns([0.7, 1.2, 1.6, 1.2, 1.2, 1.6])
            c[0].markdown(f"**{sym}**")
            # show text boxes with persisted values
            for i, col in enumerate(feat_cols, start=1):
                key = f"{sym}__{col}"
                placeholder = {
                    "Voicing": "voiced / voiceless",
                    "Place": "bilabial…glottal",
                    "Centrality": "central / lateral",
                    "Oro-nasal": "oral / nasal",
                    "Manner": "stop / fricative / affricate / approximant",
                }[col]
                st.session_state.ipa_text_values[key] = c[i].text_input(
                    col, value=st.session_state.ipa_text_values.get(key, ""),
                    key=key, placeholder=placeholder, label_visibility="collapsed"
                )

        submitted = st.form_submit_button("Generate PDF", type="primary")

    # ----- Make a DataFrame & export when submitted -----
    def values_to_df():
        rows = []
        for sym in ipa_symbols:
            row = {"IPA": sym}
            for col in feat_cols:
                row[col] = st.session_state.ipa_text_values.get(f"{sym}__{col}", "")
            rows.append(row)
        return pd.DataFrame(rows, columns=["IPA"] + feat_cols)

    # PDF utils
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
        return "Helvetica"  # fallback

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

        header = ["IPA"] + feat_cols
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

        col_widths = [35, 95, 120, 90, 95, 120]
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

    if submitted:
        df_out = values_to_df()
        st.session_state["last_df"] = df_out  # persist
        pdf_bytes = build_pdf(df_out, group_name, student_name)
        st.success("PDF ready. You can download it below.")
        st.download_button(
            "📥 Download PDF",
            data=pdf_bytes,
            file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.pdf",
            mime="application/pdf",
        )

    # Always offer CSV of the latest entries (if any)
    if "last_df" in st.session_state:
        st.download_button(
            "Download CSV (backup)",
            data=st.session_state["last_df"].to_csv(index=False).encode("utf-8"),
            file_name=f"IPA_Practice_{(student_name or 'student').replace(' ', '_')}.csv",
            mime="text/csv",
        )
