from __future__ import annotations

import logging

from app.config import Settings, load_settings
from app.extraction.extractor import extract_invoice, load_document
from app.models import InvoiceRecord
from app.validation.rules import validate_invoice

LOGGER = logging.getLogger(__name__)


def process_invoice(filename: str, data: bytes, settings: Settings | None = None) -> list[InvoiceRecord]:
    settings = settings or load_settings()
    try:
        if not data:
            raise ValueError("File is empty")
        content = load_document(filename, data, settings)
        records = extract_invoice(filename, content, settings)
        return [validate_invoice(record, settings) for record in records]
    except Exception as exc:
        LOGGER.exception("Failed to process %s", filename)
        return [
            validate_invoice(
                InvoiceRecord(FileName=filename, ValidationNotes=f"Processing failed: {exc}"),
                settings,
            )
        ]
