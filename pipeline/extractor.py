import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = _extract_from_doc(doc)
    doc.close()
    return text


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = _extract_from_doc(doc)
    doc.close()
    return text


def _extract_from_doc(doc: fitz.Document) -> str:
    pages = []
    for page in doc:
        pages.append(page.get_text())
    return "\n".join(pages)
