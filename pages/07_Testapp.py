import streamlit as st
import pandas as pd
import numby as np

tab1, tab2=st.tabs(["tab1","tab2"])

# ---------------- Tab 2 ----------------
with tab1:
    import os
    from io import BytesIO
    import pandas as pd
    import streamlit as st
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    st.subheader("IPA Practice — Describe each symbol (no IPA keyboard needed)")

    # --- Header info ---
    c1, c2 = st.columns(2)
    with c1:
        group_name = st.text_input("Group", value="")
    with c2:
        student_name = st.text_input("Name", value="")

    st.caption("Fill in Voicing, Place, Centrality, Oro-nasal, and Manner for each symbol.")

    # Symbols (as shown on screen). Students type descriptors only.
    ipa_rows = ["p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","tʃ","dʒ","h","m","n","ŋ","ɹ","l","j","w"]
    columns = ["IPA", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]

    # Session state DF
    if "ipa_df" not in st.session_state:
        st.session_state.ipa_df = pd.DataFrame(
            {"IPA": ipa_rows, "Voicing": ["" for _ in ipa_rows], "Place": ["" for _ in ipa_rows],
             "Centrality": ["" for _ in ipa_rows], "Oro-nasal": ["" for _ in ipa_rows], "Manner": ["" for _ in ipa_rows]}
        )

    edited_df = st.data_editor(
        st.session_state.ipa_df,
        use_container_width=True,
        hide_index=True,
        column_order=columns,
        num_rows="fixed",
        key="ipa_editor",
    )
    st.session_state.ipa_df = edited_df

    st.divider()

    # ASCII labels for PDF (avoid Unicode glyphs in print)
    IPA_ASCII = {
        "θ":"theta","ð":"eth","ʃ":"sh","ʒ":"zh","tʃ":"ch","dʒ":"j","ŋ":"ng","ɹ":"r","j":"y",
        # rest pass through unchanged
    }

    def to_ascii_label(sym: str) -> str:
        return IPA_ASCII.get(sym, sym)

    def build_pdf_ascii(df: pd.DataFrame, group_name: str, student_name: str) -> bytes:
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=landscape(A4),
            leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24,
            title="IPA Practice (ASCII)"
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("t", parent=styles["Heading2"], fontName="Helvetica", spaceAfter=6)
        meta_style  = ParagraphStyle("m", parent=styles["Normal"],   fontName="Helvetica", fontSize=10, spaceAfter=10)
        cell_style  = ParagraphStyle("c", parent=styles["BodyText"], fontName="Helvetica", fontSize=10, leading=12)

        elements = []
        elements.append(Paragraph("IPA Practice — Feature Descriptions", title_style))
        elements.append(Paragraph(f"Group: {group_name or ''} &nbsp;&nbsp; Name: {student_name or ''}", meta_style))
        elements.append(Spacer(1, 6))

        # Header uses ASCII-friendly label
        header = ["Symbol", "Voicing", "Place", "Centrality", "Oro-nasal", "Manner"]
        data = [header]
        for _, row in df.iterrows():
            data.append([
                Paragraph(to_ascii_label(str(row["IPA"])), cell_style),
                Paragraph(str(row["Voicing"] or ""), cell_style),
                Paragraph(str(row["Place"] or ""), cell_style),
                Paragraph(str(row["Centrality"] or ""), cell_style),
                Paragraph(str(row["Oro-nasal"] or ""), cell_style),
                Paragraph(str(row["Manner"] or ""), cell_style),
            ])

        col_widths = [70, 110, 110, 110, 110, 130]
        tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f2f6")),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),  # Symbol column centered
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fbfbfb")]),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        elements.append(tbl)
        doc.build(elements)

        buf.seek(0)
        return buf.getvalue()

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if st.button("Export to PDF"):
            pdf_bytes = build_pdf_ascii(st.session_state.ipa_df, group_name, student_name)
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
