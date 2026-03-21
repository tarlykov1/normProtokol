from pathlib import Path
import base64

from app.services.parser.docx_parser import extract_docx_text


def test_extract_docx_text_from_base64_fixture(tmp_path):
    fixture_b64 = Path(__file__).parent / "fixtures" / "sample_protocol.docx.b64"
    docx_path = tmp_path / "sample_protocol.docx"
    docx_path.write_bytes(base64.b64decode(fixture_b64.read_text().encode("ascii")))

    text, chunks = extract_docx_text(docx_path)

    assert "Протокол совещания" in text
    assert any("Поручить Иванову" in chunk for chunk in chunks)
    assert any("Организовать запуск пилота" in chunk for chunk in chunks)
