from pathlib import Path

from docx import Document


def extract_docx_text(path: Path) -> tuple[str, list[str]]:
    doc = Document(path)
    chunks: list[str] = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            chunks.append(paragraph.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                chunks.append(" | ".join(cells))

    return "\n".join(chunks), chunks
