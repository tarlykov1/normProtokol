import pytest

pytest.importorskip("docx")

from types import SimpleNamespace

from app.services.exporter.docx_exporter import export_protocol_docx


def test_export_docx(tmp_path):
    protocol = SimpleNamespace(
        id=1,
        topics=[SimpleNamespace(id=10, title="Тема", order_index=0)],
        tasks=[SimpleNamespace(topic_id=10, normalized_text="Сделать", assignee_b24_name="Иванов", assignee_raw=None, deadline_iso="2026-03-21", deadline_raw=None, order_index=0)],
    )
    out = tmp_path / "out.docx"
    export_protocol_docx(protocol, out)
    assert out.exists()
