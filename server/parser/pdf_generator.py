from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime
import html  # Make sure to import this to escape any special characters
import re

toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle(fontSize=14, name='TOCHeading1', leftIndent=20, firstLineIndent=-20, spaceBefore=10, leading=16),
    ParagraphStyle(fontSize=12, name='TOCHeading2', leftIndent=40, firstLineIndent=-20, spaceBefore=5, leading=12),
]

class AnchorHeading(Paragraph):
    def __init__(self, text, style, bookmark_name, level=0):
        self.bookmark_name = bookmark_name
        self.level = level
        Paragraph.__init__(self, f'<a name="{bookmark_name}"/>{text}', style)

    def draw(self):
        self.canv.bookmarkPage(self.bookmark_name)
        self.canv.addOutlineEntry(self.getPlainText(), self.bookmark_name, level=self.level, closed=False)
        self._notifyTOC()
        Paragraph.draw(self)

    def _notifyTOC(self):
        if hasattr(self.canv, 'notifyTOC'):
            self.canv.notifyTOC(self.level, self.getPlainText(), self.bookmark_name)


class TabularTOC(Flowable):
    def __init__(self, toc_entries, style):
        super().__init__()
        self.toc_entries = toc_entries
        self.style = style

    def wrap(self, availWidth, availHeight):
        return availWidth, 0

    def draw(self):
        pass  # Nothing to draw directly; handled as Table in build


def to_camel_case(text):
    parts = text.replace("-", " ").replace("_", " ").split()
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:]) if parts else text

def strip_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def convert_to_pdf_format(doc_data):
    # Mapping of internal keys to display-friendly names
    header_renames = {
        "attrs": "Attributes",
        "lineno": "Line No.",
        "docstring": "Description",
    }

    converted = []

    for section in doc_data:
        for title, content in section.items():
            if title.strip().lower() == "with":
                continue

            if isinstance(content, dict):  # Control flows or HTML tags
                for keyword, items in content.items():
                    if keyword.strip().lower() == "with":
                        continue

                    tag_name = keyword.strip().lower()

                    if tag_name in ["link", "script"]:
                        # Exclude 'id' and 'class'
                        filtered_keys = [key for key in items[0].keys() if key not in ("id", "class")] if items else []
                        headers = [header_renames.get(h, h.title()) for h in filtered_keys]
                        rows = [
                            [html.escape(strip_emojis(str(item.get(key, "")))) for key in filtered_keys]
                            for item in items
                        ]

                    else:
                        raw_keys = list(items[0].keys()) if items else ["Line", "Condition", "Description"]

                        # 🎯 Special headers
                        if tag_name == "try" and "condition" in raw_keys:
                            header_renames["condition"] = "Caught error name"

                        if tag_name == "switch" and "cases" in raw_keys:
                            raw_keys.append("cases")
                            header_renames["cases"] = "Cases"

                        # Reordering: lineno first, description/docstring last
                        first = [k for k in raw_keys if k == "lineno"]
                        last = [k for k in raw_keys if k in ("docstring", "description")]
                        middle = [k for k in raw_keys if k not in first + last + ["cases"]]
                        ordered_keys = first + middle + (["cases"] if "cases" in raw_keys else []) + last

                        headers = [header_renames.get(k, k.title()) for k in ordered_keys]

                        rows = []
                        for item in items:
                            row = []
                            for key in ordered_keys:
                                if key == "cases":
                                    case_texts = []
                                    for case in item.get("cases", []):
                                        label = case.get("pattern", "—")
                                        body = case.get("statements", "—")
                                        case_texts.append(f"{label}:\n{body}")
                                    value = Paragraph("<br/><br/>".join(html.escape(strip_emojis(line)) for line in case_texts), normal)
                                else:
                                    value = html.escape(strip_emojis(str(item.get(key, "—"))))
                                row.append(value)
                            rows.append(row)

                    converted.append({
                        "title": f"{keyword.capitalize()} Tags" if 'tags' in title.lower() else f"{keyword.capitalize()} Statements",
                        "headers": headers,
                        "items": rows,
                    })

            elif isinstance(content, list):
                raw_keys = list(content[0].keys()) if content else []
                styles = getSampleStyleSheet()
                normal = styles["Normal"]

                # Reorder for classes/functions
                first = [k for k in raw_keys if k == "lineno"]
                last = [k for k in raw_keys if k == "docstring"]
                middle = [k for k in raw_keys if k not in first + last]

                ordered_keys = first + middle + last
                headers = [header_renames.get(k, k.title()) for k in ordered_keys]

                items = []
                for item in content:
                    row = []
                    for key in ordered_keys:
                        if key == "methods":
                            methods_text = "<br/><br/>".join(
                                f"{html.escape(m['name'])}({', '.join(map(html.escape, m['params']))})" +
                                (f" → {html.escape(m['returns'])}" if m['returns'] and m['returns'].lower() != "unknown" else "")
                                for m in item["methods"]
                            )
                            value = Paragraph(methods_text, normal)
                        else:
                            value = Paragraph(html.escape(strip_emojis(str(item.get(key, "")))), normal)
    
                        row.append(value)
                    items.append(row)

                converted.append({
                    "title": title.replace("_", " ").replace("-", " ").title() or "Untitled Section",
                    "headers": headers,
                    "items": items,
                })

    return converted

def generate_pdf(data, output_path, filename="Documentation"):
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    normal = styles["Normal"]
    
    title_heading = ParagraphStyle(
        "TitleHeading",
        fontName="Helvetica-Bold",
        fontSize=32,
        alignment=1,
        textColor=colors.darkblue,
        spaceAfter=12,
    )

    filename_style = ParagraphStyle(
        "FilenameStyle",
        fontName="Courier-Bold",
        fontSize=20,
        alignment=1,
        textColor=colors.darkgreen,
        spaceAfter=30,
    )

    bottom_credit_style = ParagraphStyle(
        "BottomCredit",
        fontSize=12,
        alignment=1,
        textColor=colors.grey,
    )  

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], alignment=1, fontSize=28, spaceAfter=20)
    subtitle_style = ParagraphStyle("Subtitle", alignment=1, fontSize=16, textColor=colors.grey)
    date_style = ParagraphStyle("Date", alignment=1, fontSize=12, textColor=colors.darkgray)

    toc_entries = []

    class MyDocTemplate(SimpleDocTemplate):
        def afterFlowable(self, flowable):
            if isinstance(flowable, AnchorHeading):
                toc_entries.append((0, flowable.getPlainText(), self.canv.getPageNumber(), flowable.bookmark_name))

    def add_page_number(canvas, doc):
        page_num_text = f"Page {doc.page}"
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(200 * mm, 15 * mm, page_num_text)
        
    def add_title_page(elements):
        elements.append(Spacer(1, 180))
        elements.append(Paragraph("Documentation For", title_heading))
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(filename or "Untitled File", filename_style))
        elements.append(Spacer(1, 200))
        elements.append(HRFlowable(width="60%", thickness=1.2, color=colors.grey, spaceBefore=6, spaceAfter=20))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(datetime.now().strftime("%B %d, %Y"), bottom_credit_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Generated by Documentation Generator", bottom_credit_style))
        elements.append(PageBreak())

    # === FIRST PASS (collect TOC entries) ===
    doc = MyDocTemplate(output_path, pagesize=A4)
    temp_elements = []

    # Title Page
    add_title_page(temp_elements)

    # TOC Placeholder
    temp_elements.append(Paragraph("Table of Contents", h1))
    temp_elements.append(Spacer(1, 12))
    temp_elements.append(Paragraph("TOC will be placed here.", normal))
    temp_elements.append(PageBreak())

    # Add section headings & content
    for section in data:
        title = section.get("title", "Untitled Section").title()
        anchor = to_camel_case(title)

        temp_elements.append(AnchorHeading(title, h1, bookmark_name=anchor, level=0))
        temp_elements.append(Spacer(1, 6))

        if not section["items"]:
            temp_elements.append(Paragraph("No data available.", normal))
        else:
            headers = [Paragraph(str(h).title(), normal) for h in section["headers"]]
            rows = [
                [cell if isinstance(cell, Paragraph) else Paragraph(str(cell), normal) for cell in row]
                for row in section["items"]
            ]
            
            table_data = [headers] + rows

            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.aliceblue]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            temp_elements.append(table)

        temp_elements.append(PageBreak())

    # First pass: just collect TOC info
    doc.build(temp_elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    # === SECOND PASS (final document with actual TOC) ===
    final_elements = []

    # Title Page
    add_title_page(final_elements)

    # Build TOC Table (no page numbers now)
    final_elements.append(Paragraph("Table of Contents", h1))
    final_elements.append(Spacer(1, 12))

    toc_rows = [[Paragraph("Section", normal)]]
    for level, title, page, anchor in toc_entries:
        link = f'<link href="#{anchor}">{title.title()}</link>'
        toc_rows.append([Paragraph(link, normal)])

    toc_table = Table(toc_rows, colWidths=[460])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    final_elements.append(toc_table)
    final_elements.append(PageBreak())

    # Re-add content
    for section in data:
        title = section.get("title", "Untitled Section").title()
        anchor = to_camel_case(title)

        final_elements.append(AnchorHeading(title, h1, bookmark_name=anchor, level=0))
        final_elements.append(Spacer(1, 6))

        if not section["items"]:
            final_elements.append(Paragraph("No data available.", normal))
        else:
            headers = [Paragraph(str(h).title(), normal) for h in section["headers"]]
            rows = [
                [cell if isinstance(cell, Paragraph) else Paragraph(str(cell), normal) for cell in row]
                for row in section["items"]
            ]
            table_data = [headers] + rows

            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            final_elements.append(table)

        final_elements.append(PageBreak())

    # Final PDF generation
    final_doc = MyDocTemplate(output_path, pagesize=A4)
    final_doc.title = "Documentation for " + filename
    final_doc.author = "Document Generator"
    final_doc.subject = "CodeScroll: Auto-generated code documentation"
    final_doc.build(final_elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
