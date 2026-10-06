"""Regenerate the deterministic fictional PDF (no City records)."""

from pathlib import Path
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "tests/fixtures/week2/engagement.pdf"
c = canvas.Canvas(str(path), pagesize=(612, 792), invariant=1)
c.setTitle("Fictional Process Improvement Engagement")
for page, (heading, lines) in enumerate(
    [
        (
            "Project scope and timeline",
            [
                "The fictional department requests a preliminary improvement plan.",
                "The implementation timeline is six weeks.",
                "Staff interview sessions document the current intake process.",
                "The project concerns permit processing and service delays.",
            ],
        ),
        (
            "Requested deliverables",
            [
                "Deliverables include findings, alternatives, and an implementation plan.",
                "The report must identify risks and measures of success.",
                "The audience is the fictional department leadership.",
                "No actual City records, personnel, or procurement decisions are included.",
            ],
        ),
    ],
    1,
):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 735, "AI Corps | Fictional fixture")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 690, heading)
    c.setFont("Helvetica", 11)
    for i, line in enumerate(lines):
        c.drawString(50, 650 - i * 25, line)
    c.setFont("Helvetica", 9)
    c.drawString(50, 45, f"Week 2 test corpus | Page {page} of 2 | Not a City record")
    c.showPage()
c.save()
print(path)
