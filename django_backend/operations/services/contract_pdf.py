"""Deterministic server-side rendering for generated contract PDFs."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from weasyprint import CSS, HTML


class ContractPdfRenderError(ValueError):
    """Raised when a contract cannot be converted to a complete PDF."""


_BASE_URL = Path(__file__).resolve().parents[2].as_uri()
_APPROVED_LAYOUT = """
@page {
  size: A4;
  margin: 20mm 18mm 22mm 18mm;
  @bottom-center { content: "ForestIQ leping"; font-size: 8pt; color: #4b5563; }
}
html { font-family: "DejaVu Serif", serif; font-size: 11pt; color: #111827; }
body { margin: 0; line-height: 1.45; }
h1, h2, h3 { color: #164e63; page-break-after: avoid; }
h1 { font-size: 20pt; margin: 0 0 12pt; }
h2 { font-size: 14pt; margin: 18pt 0 8pt; }
p, li { orphans: 3; widows: 3; }
table { width: 100%; border-collapse: collapse; margin: 10pt 0; }
th, td { border: 0.5pt solid #94a3b8; padding: 5pt; vertical-align: top; }
th { background: #e2e8f0; }
.page-break { break-before: page; }
"""


def render_contract_pdf(*, html: str) -> tuple[bytes, str]:
    """Render trusted, validated contract HTML to a complete PDF byte string.

    The caller must only persist the returned bytes after this function succeeds.
    WeasyPrint's deterministic layout and the fixed local DejaVu font ensure that
    identical template input produces identical page content and pagination.
    """

    if not html or not html.strip():
        raise ContractPdfRenderError("A non-empty HTML contract template is required for PDF rendering.")
    try:
        pdf = HTML(string=html, base_url=_BASE_URL).write_pdf(stylesheets=[CSS(string=_APPROVED_LAYOUT)])
    except Exception as exc:  # WeasyPrint exposes several renderer-specific exception classes.
        raise ContractPdfRenderError("Contract PDF rendering failed; no contract was created.") from exc
    if not pdf.startswith(b"%PDF-") or len(pdf) < 256:
        raise ContractPdfRenderError("Contract PDF rendering produced an invalid document; no contract was created.")
    return pdf, sha256(pdf).hexdigest()


__all__ = ["ContractPdfRenderError", "render_contract_pdf"]
