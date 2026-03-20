from pathlib import Path

from docx import Document

from app.models.entities import Protocol


def export_protocol_docx(protocol: Protocol, output_path: Path) -> Path:
    doc = Document()
    doc.add_heading(f"Нормализованный протокол #{protocol.id}", level=1)

    topics = sorted(protocol.topics, key=lambda t: t.order_index)
    unassigned = [t for t in protocol.tasks if t.topic_id is None]

    for topic in topics:
        doc.add_heading(topic.title, level=2)
        tasks = sorted([t for t in protocol.tasks if t.topic_id == topic.id], key=lambda x: x.order_index)
        for idx, task in enumerate(tasks, start=1):
            doc.add_paragraph(f"{idx}. {task.normalized_text}")
            doc.add_paragraph(f"Исполнитель: {task.assignee_b24_name or task.assignee_raw or '-'}")
            doc.add_paragraph(f"Срок: {task.deadline_iso or task.deadline_raw or '-'}")

    if unassigned:
        doc.add_heading("Без темы", level=2)
        for idx, task in enumerate(unassigned, start=1):
            doc.add_paragraph(f"{idx}. {task.normalized_text}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path
