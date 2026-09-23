from __future__ import annotations

import base64
import json
import logging
import time

import requests

from app.config import Settings, load_settings
from app.models import NOT_APPLICABLE, NOT_AVAILABLE, InvoiceRecord

LOGGER = logging.getLogger(__name__)


def load_document(filename: str, data: bytes, settings: Settings | None = None) -> bytes:
    if not data:
        raise ValueError("File is empty")
    return data


def extract_invoice(filename: str, content: bytes, settings: Settings | None = None) -> list[InvoiceRecord]:
    settings = settings or load_settings()

    if not settings.flow_http_url:
        raise ValueError("FLOW_HTTP_URL is not configured.")

    b64_content = base64.b64encode(content).decode("utf-8")

    response = requests.post(
        settings.flow_http_url,
        json={"FileName": filename, "FileContent": b64_content},
        timeout=settings.flow_timeout_seconds,
    )
    if response.status_code == 504:
        raise RuntimeError(
            "Power Automate timed out its synchronous response. "
            "Enable Asynchronous Response on the flow and return a Location header."
        )
    response.raise_for_status()

    body = _get_flow_response(response, settings)
    invoices = _extract_invoices_list(body)

    if not invoices:
        return [InvoiceRecord(FileName=filename, ValidationNotes="Agent returned no invoice data.")]

    records: list[InvoiceRecord] = []
    for invoice in invoices:
        records.extend(_invoice_to_records(filename, invoice))
    return records


def _get_flow_response(response: requests.Response, settings: Settings) -> dict:
    if response.status_code != 202:
        return response.json()

    status_url = response.headers.get("Location")
    if not status_url:
        raise RuntimeError("Flow returned 202 without a status URL in the Location header.")

    deadline = time.monotonic() + settings.flow_timeout_seconds
    while time.monotonic() < deadline:
        time.sleep(settings.flow_poll_interval_seconds)
        status_response = requests.get(status_url, timeout=settings.flow_timeout_seconds)
        if status_response.status_code == 202:
            continue
        status_response.raise_for_status()
        return status_response.json()

    raise TimeoutError("The flow did not finish before the configured timeout.")


def _extract_invoices_list(body: dict) -> list[dict]:
    raw = body.get("invoices")

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return raw
    return []


def _invoice_to_records(filename: str, invoice: dict) -> list[InvoiceRecord]:
    if invoice.get("status") == "FAILED":
        return [
            InvoiceRecord(
                FileName=invoice.get("file_name", filename),
                InvoiceNumber=invoice.get("invoice_number", NOT_AVAILABLE),
                ValidationNotes=invoice.get("validation_notes", "Processing failed."),
            )
        ]

    hsn_lines = invoice.get("hsn_lines") or [{}]
    records: list[InvoiceRecord] = []

    for hsn in hsn_lines:
        records.append(
            InvoiceRecord(
                FileName=invoice.get("file_name", filename),
                InvoiceNumber=invoice.get("invoice_number", NOT_AVAILABLE),
                SupplierName=invoice.get("supplier_name", NOT_AVAILABLE),
                SupplierAddress=invoice.get("supplier_address", NOT_AVAILABLE),
                SupplierGSTIN=invoice.get("supplier_gstin", NOT_AVAILABLE),
                InvoiceDate=invoice.get("invoice_date", NOT_AVAILABLE),
                BFLName=invoice.get("bfl_name", NOT_AVAILABLE),
                BFLAddress=invoice.get("bfl_address", NOT_AVAILABLE),
                BFLGSTIN=invoice.get("bfl_gstin", NOT_AVAILABLE),
                HSNCode=hsn.get("hsn_code", NOT_AVAILABLE),
                Description=hsn.get("description", NOT_AVAILABLE),
                QuantityUQC=hsn.get("quantity_uqc", NOT_AVAILABLE),
                TaxableValue=hsn.get("taxable_value", NOT_AVAILABLE),
                TotalValueOfSupply=hsn.get("total_value_of_supply", NOT_AVAILABLE),
                PlaceOfSupply=invoice.get("place_of_supply", NOT_AVAILABLE),
                ReverseCharge=invoice.get("reverse_charge", NOT_AVAILABLE),
                SignaturePresent=invoice.get("signature_present", NOT_AVAILABLE),
                QRIRN=invoice.get("qr_irn", NOT_AVAILABLE),
                CGSTRate=hsn.get("cgst_rate", NOT_APPLICABLE),
                CGSTAmount=hsn.get("cgst_amount", NOT_APPLICABLE),
                SGSTRate=hsn.get("sgst_rate", NOT_APPLICABLE),
                SGSTAmount=hsn.get("sgst_amount", NOT_APPLICABLE),
                IGSTRate=hsn.get("igst_rate", NOT_APPLICABLE),
                IGSTAmount=hsn.get("igst_amount", NOT_APPLICABLE),
                UTGSTRate=hsn.get("utgst_rate", NOT_APPLICABLE),
                UTGSTAmount=hsn.get("utgst_amount", NOT_APPLICABLE),
                CessRate=hsn.get("cess_rate", NOT_APPLICABLE),
                CessAmount=hsn.get("cess_amount", NOT_APPLICABLE),
                TotalTaxAmount=invoice.get("total_tax_amount", NOT_AVAILABLE),
                ValidationNotes=invoice.get("validation_notes", ""),
            )
        )
    return records