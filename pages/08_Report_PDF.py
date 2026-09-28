"""
Page 8: Research Project Report (PDF Viewer & Download)
Presents the official M.Sc Big Data Analytics dissertation report for the
ATM Cash Management Decision Support System.
"""

import os
import base64
from pathlib import Path
import streamlit as st

from utils.styling import inject_custom_css, render_header

# Resolve PDF report location with robust fallbacks
POSSIBLE_PATHS = [
    Path(__file__).parent.parent / "reports" / "ATM_Cash_Management_Project_Report.pdf",
    Path(__file__).parent.parent / "data" / "ATM_Cash_Management_Project_Report.pdf",
    Path("reports/ATM_Cash_Management_Project_Report.pdf"),
    Path("ATM_Cash_Management_Project_Report.pdf"),
    Path("/home/michaelfernandes/Downloads/ATM_Cash_Management_Project_Report.pdf")
]

def get_report_pdf_bytes():
    for p in POSSIBLE_PATHS:
        if p.exists():
            with open(p, "rb") as f:
                return f.read(), p
    return None, None

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

    pdf_bytes, found_path = get_report_pdf_bytes()

    if pdf_bytes is None:
        st.error(
            "⚠️ Project report PDF file could not be found. Please ensure "
            "`ATM_Cash_Management_Project_Report.pdf` exists in the `reports/` directory."
        )
        return

    # Metadata & Key Highlights Card
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Document Type", "Research Dissertation", "34 Pages")
        with c2:
            st.metric("Primary Author", "Glen Noronha", "Roll No. 09")
        with c3:
            st.metric("Faculty Guide", "Mr. Ameya Chitnis", "St. Xavier's College")
        with c4:
            st.metric("File Size", f"{len(pdf_bytes) / (1024 * 1024):.1f} MB", "Standard PDF Format")

    st.markdown("<br>", unsafe_allow_html=True)

    # Action bar: Download button + quick tips
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
            "💡 You can read the full 34-page dissertation report directly in the viewer below, "
            "or download the PDF file to your device for offline reading and archiving."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Multi-tab view: Live PDF Viewer, Executive Abstract & Table of Contents
    tab_viewer, tab_abstract, tab_toc = st.tabs([
        "📄 Embedded PDF Viewer",
        "📝 Executive Summary & Abstract",
        "📑 Table of Contents"
    ])

    with tab_viewer:
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f"""
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}#toolbar=1&navpanes=1&scrollbar=1" 
            width="100%" 
            height="1000px" 
            type="application/pdf"
            style="border: 1px solid #CBD5E1; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);"
        >
            <div style="padding: 20px; text-align: center; background-color: #F8FAFC; border-radius: 8px;">
                <p style="font-size: 1.1rem; color: #334155;">
                    Your browser does not support embedded PDF rendering.
                </p>
                <a href="data:application/pdf;base64,{base64_pdf}" download="ATM_Cash_Management_Project_Report.pdf" 
                   style="display: inline-block; padding: 10px 20px; background-color: #2563EB; color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">
                    Click here to download the PDF
                </a>
            </div>
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

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
