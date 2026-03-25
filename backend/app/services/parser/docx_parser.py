import re
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def _iter_block_items(parent):
    for child in parent.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)


def _clean(value: str) -> str:
    value = value.replace("\u00ad", "")
    value = re.sub(r"(\w)-\s+(\w)", r"\1\2", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_docx_text(path: Path) -> tuple[str, list[str]]:
    doc = Document(path)
    chunks: list[str] = []

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = _clean(block.text)
            if text:
                chunks.append(text)
            continue

        row_chunks: list[str] = []
        for row in block.rows:
            cells = [_clean(c.text) for c in row.cells if _clean(c.text)]
            if cells:
                row_chunks.append(" | ".join(cells))
        chunks.extend(row_chunks)

    return "\n".join(chunks), chunks
