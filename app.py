from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

import streamlit as st

from app.config import load_settings
from app.exporter import create_excel
from app.models import InvoiceRecord
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
    uploaded_files = [(upload.name, upload.getvalue()) for upload in uploads]
    file_results: list[list[InvoiceRecord] | None] = [None] * len(uploaded_files)
    progress = st.progress(0, text="Starting validation")
    with ThreadPoolExecutor(max_workers=min(4, len(uploaded_files))) as executor:
        futures = {
            executor.submit(process_invoice, filename, data, settings): (index, filename)
            for index, (filename, data) in enumerate(uploaded_files)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            index, filename = futures[future]
            file_results[index] = future.result()
            progress.progress(
                completed / len(uploaded_files),
                text=f"Processed {filename} ({completed}/{len(uploaded_files)})",
            )
    records = [record for result in file_results if result is not None for record in result]
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
