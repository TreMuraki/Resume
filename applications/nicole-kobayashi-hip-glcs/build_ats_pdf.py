#!/usr/bin/env python3
"""Render the ATS-optimized resume PDF.

Design constraints are ATS constraints, not aesthetic ones:
  - single column, no tables, no text boxes, no headers/footers, no graphics
  - one standard font family (Helvetica), real text (never outlined or imaged)
  - standard section headings an ASCII parser recognizes
  - plain hyphen bullets, no glyphs outside Latin-1
  - contact details in the body flow, not in the page margin area
"""

import re
import sys

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
)

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
INK = "#000000"

styles = {
    "name": ParagraphStyle(
        "name", fontName=FONT_BOLD, fontSize=17, leading=20,
        spaceAfter=2, alignment=TA_LEFT, textColor=INK,
    ),
    "contact": ParagraphStyle(
        "contact", fontName=FONT, fontSize=9.5, leading=12,
        spaceAfter=9, textColor=INK,
    ),
    "section": ParagraphStyle(
        "section", fontName=FONT_BOLD, fontSize=10.5, leading=12,
        spaceBefore=9, spaceAfter=1, textColor=INK,
    ),
    "role": ParagraphStyle(
        "role", fontName=FONT_BOLD, fontSize=10, leading=12.5,
        spaceBefore=6, spaceAfter=0, textColor=INK,
    ),
    "meta": ParagraphStyle(
        "meta", fontName=FONT, fontSize=9, leading=11,
        spaceAfter=2, textColor=INK,
    ),
    "body": ParagraphStyle(
        "body", fontName=FONT, fontSize=9.5, leading=12.2,
        spaceAfter=3, textColor=INK,
    ),
    "bullet": ParagraphStyle(
        "bullet", fontName=FONT, fontSize=9.5, leading=12.2,
        leftIndent=11, firstLineIndent=-11, spaceAfter=2.5, textColor=INK,
    ),
}


def md_inline(text):
    """Convert **bold** / *italic* to ReportLab markup and escape XML."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text


def rule():
    return HRFlowable(width="100%", thickness=0.7, color=INK,
                      spaceBefore=1, spaceAfter=4)


def build_story(md_path):
    lines = open(md_path, encoding="utf-8").read().splitlines()
    story = []
    i = 0
    # Leading blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1

        if not line:
            continue

        if line.startswith("# "):
            story.append(Paragraph(md_inline(line[2:].strip()), styles["name"]))
            # The next non-blank, non-heading line is the contact block.
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].lstrip().startswith("#"):
                story.append(
                    Paragraph(md_inline(lines[j].strip()), styles["contact"])
                )
                i = j + 1
            continue

        if line.startswith("## "):
            story.append(Paragraph(md_inline(line[3:].strip().upper()),
                                   styles["section"]))
            story.append(rule())
            continue

        if line.startswith("### "):
            story.append(Paragraph(md_inline(line[4:].strip()), styles["role"]))
            # An immediately following non-bullet line is the date/location meta.
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if (j < len(lines) and lines[j].strip()
                    and not lines[j].lstrip().startswith(("-", "#"))):
                story.append(Paragraph(md_inline(lines[j].strip()),
                                       styles["meta"]))
                i = j + 1
            continue

        if line.startswith("- "):
            # Join wrapped continuation lines into one bullet.
            chunk = [line[2:].strip()]
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].lstrip().startswith(("-", "#"))
                   and lines[i].startswith(("  ", "\t"))):
                chunk.append(lines[i].strip())
                i += 1
            story.append(
                Paragraph("- " + md_inline(" ".join(chunk)), styles["bullet"])
            )
            continue

        # Plain paragraph; absorb soft-wrapped continuation lines.
        chunk = [line]
        while (i < len(lines) and lines[i].strip()
               and not lines[i].lstrip().startswith(("-", "#"))):
            chunk.append(lines[i].strip())
            i += 1
        story.append(Paragraph(md_inline(" ".join(chunk)), styles["body"]))

    return story


def main():
    md_path = sys.argv[1]
    out_path = sys.argv[2]

    doc = BaseDocTemplate(
        out_path,
        pagesize=LETTER,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="Nicole Kobayashi - Resume",
        author="Nicole Kobayashi",
        subject="Grant Life Cycle Specialist",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="single", frames=[frame])])
    doc.build(build_story(md_path))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
