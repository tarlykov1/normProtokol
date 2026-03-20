import pytest

docx = pytest.importorskip("docx")
Document = docx.Document

from app.services.parser.docx_parser import extract_docx_text


def test_extract_docx_text(tmp_path):
    path = tmp_path / "sample.docx"
    doc = Document()
    doc.add_paragraph("Поручить Иванов И.И. подготовить отчет до 21.03.2026")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Согласовать"
    table.rows[0].cells[1].text = "договор"
    doc.save(path)

    text, chunks = extract_docx_text(path)

    assert "Поручить" in text
    assert any("Согласовать" in chunk for chunk in chunks)
