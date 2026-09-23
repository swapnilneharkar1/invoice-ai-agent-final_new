from __future__ import annotations

import logging

import streamlit as st

from app.config import load_settings
from app.exporter import create_excel
from app.processor import process_invoice

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="BFL GST Invoice Validator", page_icon=":page_facing_up:", layout="wide")

settings = load_settings()

st.title("BFL GST Invoice Validator")
st.caption("Extract, validate, and export GST invoice information.")

# ============================================================
# Access control
# ============================================================
if "authorized_email" not in st.session_state:
    st.session_state["authorized_email"] = None

if not st.session_state["authorized_email"]:
    email_input = st.text_input("Enter your work email to continue:")
    if email_input:
        if email_input.strip().lower() in {e.lower() for e in settings.access_list}:
            st.session_state["authorized_email"] = email_input.strip()
            st.rerun()
        else:
            st.error("Access denied. Contact your administrator to request access.")
    st.stop()

st.success(f"Signed in as {st.session_state['authorized_email']}")

# ============================================================
# Main app
# ============================================================
uploads = st.file_uploader(
    "Upload invoice PDF files",
    type=["pdf"],
    accept_multiple_files=True,
)
st.caption("Maximum recommended size: 10 MB per PDF file")
if uploads:
    st.write(f"Uploaded files: {len(uploads)}")
    st.dataframe({"FileName": [item.name for item in uploads]}, use_container_width=True, hide_index=True)

if st.button("Validate Invoices", type="primary", disabled=not uploads):
    records = []
    progress = st.progress(0, text="Starting validation")
    for index, upload in enumerate(uploads):
        progress.progress(index / len(uploads), text=f"Processing {upload.name}")
        records.extend(process_invoice(upload.name, upload.getvalue(), settings))
    progress.progress(1.0, text="Validation complete")
    st.session_state["records"] = records

records = st.session_state.get("records")
if records:
    st.subheader("Validation results")
    st.dataframe([record.as_row() for record in records], use_container_width=True, hide_index=True)
    st.download_button(
        "Download Excel output",
        create_excel(records),
        "bfl_invoice_validation.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
