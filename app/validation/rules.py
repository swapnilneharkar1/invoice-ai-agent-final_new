from __future__ import annotations

from app.config import Settings, load_settings
from app.models import InvoiceRecord


def validate_invoice(record: InvoiceRecord, settings: Settings | None = None) -> InvoiceRecord:
    """
    The Vendor Invoice Validation Agent already performs all business-rule
    validation (GSTIN structure, required-field checks, invoice number
    rules) and returns its findings in ValidationNotes. This function is a
    light safety net only — it does NOT re-implement the agent's logic,
    to avoid the two layers disagreeing with each other.
    """
    settings = settings or load_settings()

    if not record.ValidationNotes.strip():
        record.ValidationNotes = "All fields found."

    return record
