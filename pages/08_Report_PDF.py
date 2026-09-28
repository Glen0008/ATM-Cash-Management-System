"""
Page 8: Research Project Report (PDF Viewer & Download)
Presents the official M.Sc Big Data Analytics dissertation report for the
ATM Cash Management Decision Support System.
Uses PyMuPDF high-fidelity native page rendering to prevent blank browser plugin errors.
"""

import os
import base64
from pathlib import Path
import streamlit as st

from utils.styling import inject_custom_css, render_header

# Optional PyMuPDF import with graceful fallback
try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    try:
        import fitz as pymupdf
        HAS_PYMUPDF = True
    except ImportError:
        HAS_PYMUPDF = False

# Resolve PDF report location with robust fallbacks
POSSIBLE_PATHS = [
    Path(__file__).parent.parent / "reports" / "ATM_Cash_Management_Project_Report.pdf",
    Path(__file__).parent.parent / "data" / "ATM_Cash_Management_Project_Report.pdf",
    Path("reports/ATM_Cash_Management_Project_Report.pdf"),
    Path("ATM_Cash_Management_Project_Report.pdf"),
    Path("/home/michaelfernandes/Downloads/ATM_Cash_Management_Project_Report.pdf")
]

CHAPTER_JUMPS = {
    "Page 1: Title & Cover Page": 1,
    "Page 2: Certificate of Originality": 2,
    "Page 3: Acknowledgement": 3,
    "Page 4: Table of Contents": 4,
    "Page 6: List of Figures & Tables": 6,
    "Page 7: Abstract / Executive Summary": 7,
    "Page 8: Chapter 1 — Introduction & Problem Statement": 8,
    "Page 10: Chapter 2 — Data Understanding & Dictionary": 10,
    "Page 12: Chapter 3 — Exploratory Data Analysis (EDA)": 12,
    "Page 16: Chapter 4 — Data Cleaning & Outlier Treatment": 16,
    "Page 17: Chapter 5 — Feature Engineering": 17,
    "Page 19: Chapter 6 — Feature Selection": 19,
    "Page 21: Chapter 7 — Preprocessing & Train/Test Strategy": 21,
    "Page 22: Chapter 8 — Model Development (XGBoost/ARIMA)": 22,
    "Page 24: Chapter 9 — Hyperparameter Tuning": 24,
    "Page 25: Chapter 10 — Model Evaluation & PR-AUC": 25,
    "Page 29: Chapter 11 — Business Impact & Replenishment": 29,
    "Page 31: Chapter 12 — Conclusion & Future Work": 31,
    "Page 32: References": 32,
    "Page 33: Appendix & Code Snippets": 33,
}

def get_report_pdf_path():
    for p in POSSIBLE_PATHS:
        if p.exists():
            return str(p)
    return None

@st.cache_data(show_spinner=False)
def load_pdf_bytes(pdf_path: str) -> bytes:
    with open(pdf_path, "rb") as f:
        return f.read()

@st.cache_data(show_spinner=False)
def get_pdf_page_count(pdf_path: str) -> int:
    if HAS_PYMUPDF:
        doc = pymupdf.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    return 34

@st.cache_data(show_spinner=False)
def render_page_image(pdf_path: str, page_number_1_indexed: int, dpi: int = 150) -> bytes:
    """Renders a PDF page to a crisp PNG image using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    page = doc.load_page(page_number_1_indexed - 1)
    pix = page.get_pixmap(dpi=dpi)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes

def main():
    st.set_page_config(
        page_title="Project Report (PDF) | ATM Cash DSS",
        page_icon="📑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    inject_custom_css()

    # Sidebar documentation metadata
    with st.sidebar:
        st.markdown("### 🎓 Academic Research")
        st.info(
            "**M.Sc Big Data Analytics**\n\n"
            "**Institution:** St. Xavier's College (Autonomous), Mumbai\n\n"
            "**Submitted by:** Glen Noronha (Roll No. 09)\n\n"
            "**Project Guide:** Mr. Ameya Chitnis\n\n"
            "**Submission Date:** September 2026\n\n"
            "**Domain:** Banking & Cash-in-Transit (CIT)"
        )
        st.markdown("---")

    render_header(
        title="Research Project Report",
        subtitle="AI-Powered ATM Cash Management Decision Support System • M.Sc Big Data Analytics Dissertation",
        badge="Academic Documentation"
    )

    pdf_path = get_report_pdf_path()
    if not pdf_path:
        st.error(
            "⚠️ Project report PDF file could not be found. Please ensure "
            "`ATM_Cash_Management_Project_Report.pdf` exists in the `reports/` directory."
        )
        return

    pdf_bytes = load_pdf_bytes(pdf_path)
    total_pages = get_pdf_page_count(pdf_path)

    # Metadata & Key Highlights Card
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Document Type", "Research Dissertation", f"{total_pages} Pages")
        with c2:
            st.metric("Primary Author", "Glen Noronha", "Roll No. 09")
        with c3:
            st.metric("Faculty Guide", "Mr. Ameya Chitnis", "St. Xavier's College")
        with c4:
            st.metric("File Size", f"{len(pdf_bytes) / (1024 * 1024):.1f} MB", "Standard PDF")

    st.markdown("<br>", unsafe_allow_html=True)

    # Primary Action Bar: Download Button + Instructions
    btn_col1, btn_col2 = st.columns([1, 2])
    with btn_col1:
        st.download_button(
            label="📥 Download Full Research Report (PDF)",
            data=pdf_bytes,
            file_name="ATM_Cash_Management_Project_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with btn_col2:
        st.caption(
            "💡 You can navigate through all 34 pages interactively below or download the "
            "complete PDF for offline reading and printing."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Multi-tab view: High-Fidelity Viewer, Abstract, and Table of Contents
    tab_viewer, tab_abstract, tab_toc = st.tabs([
        "📄 Interactive Document Viewer",
        "📝 Executive Summary & Abstract",
        "📑 Table of Contents & Structure"
    ])

    with tab_viewer:
        if HAS_PYMUPDF:
            # Viewer Controls Bar
            with st.container(border=True):
                ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])

                with ctrl1:
                    jump_selection = st.selectbox(
                        "Jump to Chapter / Section:",
                        options=list(CHAPTER_JUMPS.keys()),
                        index=0
                    )
                    target_page = CHAPTER_JUMPS[jump_selection]

                with ctrl2:
                    view_mode = st.radio(
                        "Reading Mode:",
                        options=["Single Page Flip", "Continuous Scroll (All Pages)"],
                        horizontal=True
                    )

                with ctrl3:
                    dpi_setting = st.selectbox(
                        "Resolution:",
                        options=[150, 200],
                        format_func=lambda x: f"{x} DPI ({'Standard' if x == 150 else 'Crisp HD'})",
                        index=0
                    )

            if view_mode == "Single Page Flip":
                # State management for current page
                if "pdf_current_page" not in st.session_state:
                    st.session_state.pdf_current_page = target_page

                # If user selected a chapter jump, update session state
                if st.session_state.get("last_jump_selection") != jump_selection:
                    st.session_state.pdf_current_page = target_page
                    st.session_state.last_jump_selection = jump_selection

                # Flip Controls
                flip_col1, flip_col2, flip_col3, flip_col4, flip_col5 = st.columns([1, 1, 3, 1, 1])
                with flip_col1:
                    if st.button("⏮ First", disabled=(st.session_state.pdf_current_page <= 1), use_container_width=True):
                        st.session_state.pdf_current_page = 1
                        st.rerun()
                with flip_col2:
                    if st.button("◀ Prev", disabled=(st.session_state.pdf_current_page <= 1), use_container_width=True):
                        st.session_state.pdf_current_page -= 1
                        st.rerun()

                with flip_col3:
                    chosen_page = st.slider(
                        "Page Navigator",
                        min_value=1,
                        max_value=total_pages,
                        value=st.session_state.pdf_current_page,
                        label_visibility="collapsed"
                    )
                    if chosen_page != st.session_state.pdf_current_page:
                        st.session_state.pdf_current_page = chosen_page
                        st.rerun()

                with flip_col4:
                    if st.button("Next ▶", disabled=(st.session_state.pdf_current_page >= total_pages), use_container_width=True):
                        st.session_state.pdf_current_page += 1
                        st.rerun()
                with flip_col5:
                    if st.button("Last ⏭", disabled=(st.session_state.pdf_current_page >= total_pages), use_container_width=True):
                        st.session_state.pdf_current_page = total_pages
                        st.rerun()

                st.markdown(
                    f"<p style='text-align: center; color: #64748B; font-weight: 600; margin: 4px 0 16px 0;'>"
                    f"Page {st.session_state.pdf_current_page} of {total_pages}"
                    f"</p>",
                    unsafe_allow_html=True
                )

                # Render Selected Page
                img_data = render_page_image(pdf_path, st.session_state.pdf_current_page, dpi=dpi_setting)
                col_spacer_l, col_img, col_spacer_r = st.columns([1, 8, 1])
                with col_img:
                    st.image(
                        img_data,
                        caption=f"Report Page {st.session_state.pdf_current_page} of {total_pages}",
                        use_container_width=True
                    )

            else:
                # Continuous Scroll Mode: Render pages in scroll view
                st.info(f"Rendering all {total_pages} pages in continuous reading view. Scroll down to browse.")
                for p_num in range(1, total_pages + 1):
                    p_img = render_page_image(pdf_path, p_num, dpi=130)
                    col_s_l, col_s_main, col_s_r = st.columns([1, 8, 1])
                    with col_s_main:
                        st.markdown(
                            f"<div style='border-top: 2px solid #E2E8F0; margin: 24px 0 10px 0; padding-top: 6px; color: #64748B; font-size: 0.85rem; text-align: center; font-weight: 600;'>"
                            f"— Page {p_num} of {total_pages} —"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.image(p_img, use_container_width=True)

        else:
            # Fallback: HTML5 PDF.js Canvas Viewer in an isolated iframe
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            pdfjs_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
                <style>
                    body {{ margin: 0; padding: 12px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #F1F5F9; }}
                    #toolbar {{ display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 12px; background: white; padding: 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                    button {{ padding: 6px 14px; background: #2563EB; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500; }}
                    button:disabled {{ background: #94A3B8; cursor: not-allowed; }}
                    #pdf-canvas {{ display: block; margin: 0 auto; background: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div id="toolbar">
                    <button id="prev-btn">◀ Previous</button>
                    <span>Page <strong id="page-num">1</strong> of <strong id="page-count">-</strong></span>
                    <button id="next-btn">Next ▶</button>
                </div>
                <canvas id="pdf-canvas"></canvas>

                <script>
                    const pdfData = atob("{b64_pdf}");
                    const uint8Array = new Uint8Array(pdfData.length);
                    for (let i = 0; i < pdfData.length; i++) {{
                        uint8Array[i] = pdfData.charCodeAt(i);
                    }}

                    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

                    let pdfDoc = null, pageNum = 1, pageRendering = false, pageNumPending = null;
                    const canvas = document.getElementById('pdf-canvas');
                    const ctx = canvas.getContext('2d');

                    function renderPage(num) {{
                        pageRendering = true;
                        pdfDoc.getPage(num).then(function(page) {{
                            const viewport = page.getViewport({{ scale: 1.5 }});
                            canvas.height = viewport.height;
                            canvas.width = viewport.width;

                            const renderContext = {{ canvasContext: ctx, viewport: viewport }};
                            const renderTask = page.render(renderContext);

                            renderTask.promise.then(function() {{
                                pageRendering = false;
                                if (pageNumPending !== null) {{
                                    renderPage(pageNumPending);
                                    pageNumPending = null;
                                }}
                            }});
                        }});
                        document.getElementById('page-num').textContent = num;
                        document.getElementById('prev-btn').disabled = (num <= 1);
                        document.getElementById('next-btn').disabled = (num >= pdfDoc.numPages);
                    }}

                    function queueRenderPage(num) {{
                        if (pageRendering) {{
                            pageNumPending = num;
                        }} else {{
                            renderPage(num);
                        }}
                    }}

                    document.getElementById('prev-btn').addEventListener('click', function() {{
                        if (pageNum <= 1) return;
                        pageNum--;
                        queueRenderPage(pageNum);
                    }});

                    document.getElementById('next-btn').addEventListener('click', function() {{
                        if (pageNum >= pdfDoc.numPages) return;
                        pageNum++;
                        queueRenderPage(pageNum);
                    }});

                    pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(function(pdfDoc_) {{
                        pdfDoc = pdfDoc_;
                        document.getElementById('page-count').textContent = pdfDoc.numPages;
                        renderPage(pageNum);
                    }});
                </script>
            </body>
            </html>
            """
            st.components.v1.html(pdfjs_html, height=1050, scrolling=True)

    with tab_abstract:
        st.markdown("### 📋 Abstract & Core Dissertation Overview")
        st.markdown(
            """
            > **Executive Summary:**
            > ATM cash replenishment is a recurring operational decision in which insufficient cash can disrupt customer 
            > service while excessive replenishment can increase handling and logistics costs. This project develops an 
            > AI-powered decision-support system that ranks ATMs by near-term low-cash risk and converts the ranking into 
            > an actionable replenishment recommendation.
            
            #### 🔍 Key Methodological Pillars
            1. **Transaction Panel Transformation:**
               - 222,356 raw transaction records covering 60 ATMs, 25 branches, and 10 cities (Jan 2023 – Dec 2024).
               - Transformed into an ATM-day decision panel containing 43,797 observations.
            2. **Low Cash Alert Definition:**
               - Built a leakage-safe proxy alert triggered when end-of-day cash drops below **20% of ATM cash capacity**.
               - Constructed forward-looking targets for 1-day (`low_cash_next_1d`) and 3-day (`low_cash_next_3d`) horizons.
            3. **Predictive Performance:**
               - The selected **3-day XGBoost classifier** achieved **PR-AUC 0.527**, **ROC-AUC 0.917**, and recall of **0.796** on out-of-sample test data.
               - Top-decile lift of **7.0×**: The highest-risk 10% of ATM-days captured **69.9%** of all low-cash incidents.
            4. **Empirical Policy Backtesting (59 Days):**
               - At $N = 8$: Model-driven prioritization reduced low-cash days by **25.0%**.
               - At $N = 12$: Reduced low-cash days by **53.0%**.
               - At $N = 16$: Reduced low-cash days by **68.8%**.
               - Honest negative case at $N = 5$: Round-robin fixed schedule performed slightly better (-8.0% deficit), demonstrating the necessity of a hybrid policy under severe armored courier bottlenecks.
            """
        )

    with tab_toc:
        st.markdown("### 📑 Full Dissertation Table of Contents")
        col_toc_l, col_toc_r = st.columns(2)
        with col_toc_l:
            st.markdown(
                """
                - **Preliminaries**
                  - Certificate of Originality *(Page ii)*
                  - Acknowledgement *(Page iii)*
                  - Table of Contents *(Page iv)*
                  - List of Figures & Tables *(Page vi)*
                  - Abstract / Executive Summary *(Page vii)*
                - **Chapter 1: Introduction** *(Page 1)*
                  - 1.1 Background & Motivation
                  - 1.2 Business Problem Statement
                  - 1.3 ML Problem Formulation
                  - 1.4 Objectives & Success Metrics
                  - 1.5 Scope & Constraints
                - **Chapter 2: Data Understanding** *(Page 3)*
                  - 1.6 Literature Review & Research Gap
                  - 1.7 Research Design & Methodology
                  - 2.1 Data Source(s)
                  - 2.2 Data Dictionary Summary
                  - 2.3 Initial Data Audit
                  - 2.4 Target Variable Analysis
                - **Chapter 3: Exploratory Data Analysis** *(Page 5)*
                  - 3.1 Univariate Analysis
                  - 3.2 Bivariate Analysis
                  - 3.3 Multivariate Analysis
                  - 3.4 Key Insights Summary
                - **Chapter 4: Data Cleaning** *(Page 9)*
                  - 4.1 Missing Value Treatment
                  - 4.2 Outlier Treatment
                  - 4.3 Inconsistent & Impossible Values
                  - 4.4 Duplicate Handling
                - **Chapter 5: Feature Engineering** *(Page 10)*
                  - 5.1 Derived Features
                  - 5.2 Transformations
                  - 5.3 Encoding Strategy
                  - 5.4 Feature Engineering Summary Table
                - **Chapter 6: Feature Selection** *(Page 11)*
                  - 6.1 Method(s) Used
                  - 6.2 Final Feature List
                """
            )
        with col_toc_r:
            st.markdown(
                """
                - **Chapter 7: Data Preprocessing & Train/Test Strategy** *(Page 12)*
                  - 7.1 Train/Test Split Strategy
                  - 7.2 Scaling & Encoding Pipeline
                  - 7.3 Handling Class Imbalance
                  - 7.4 Cross-Validation Design
                - **Chapter 8: Model Development** *(Page 13)*
                  - 8.1 Baseline Model
                  - 8.2 Candidate Models
                  - 8.3 Model Selection Rationale
                - **Chapter 9: Hyperparameter Tuning** *(Page 15)*
                  - 9.1 Search Method
                  - 9.2 Search Space
                  - 9.3 Best Parameters Found
                - **Chapter 10: Model Evaluation & Validation** *(Page 16)*
                  - 10.1 Classification Metrics
                  - 10.2 Discrimination Metrics
                  - 10.3 Decile / Lift / Gain Analysis
                  - 10.4 Calibration
                  - 10.5 Overfitting Diagnostics
                  - 10.6 Stability Analysis (PSI / CSI)
                - **Chapter 11: Business Impact & Recommendations** *(Page 20)*
                  - 11.1 Score-to-Action Mapping
                  - 11.2 Cost-Benefit Analysis
                  - 11.3 Deployment & Monitoring Recommendations
                - **Chapter 12: Conclusion & Future Work** *(Page 22)*
                  - 12.1 Summary of Findings
                  - 12.2 Limitations
                  - 12.3 Future Improvements
                - **References** *(Page 23)*
                - **Appendix** *(Page 24)*
                  - A. Full Data Dictionary
                  - B. Key Code Snippets
                  - C. Additional Charts & Tables
                """
            )

if __name__ == "__main__":
    main()
