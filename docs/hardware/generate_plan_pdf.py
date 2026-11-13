import html
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).with_name('FIV_Hardware_Integration_Plan.pdf')
INLINE_TOKEN = re.compile(r'(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)')


def inline_markup(text):
    result = []
    cursor = 0
    for match in INLINE_TOKEN.finditer(text):
        result.append(html.escape(text[cursor:match.start()]))
        token = match.group(0)
        if token.startswith('['):
            label, url = re.match(r'\[([^\]]+)\]\(([^)]+)\)', token).groups()
            result.append(
                f'<link href="{html.escape(url, quote=True)}" '
                f'color="#1769aa">{html.escape(label)}</link>'
            )
        elif token.startswith('**'):
            result.append(f'<b>{html.escape(token[2:-2])}</b>')
        else:
            result.append(
                f'<font name="Courier">{html.escape(token[1:-1])}</font>'
            )
        cursor = match.end()
    result.append(html.escape(text[cursor:]))
    return ''.join(result)


def table_rows(lines):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells and all(re.fullmatch(r':?-{3,}:?', cell) for cell in cells):
            continue
        rows.append([Paragraph(inline_markup(cell), STYLES['BodyText']) for cell in cells])
    return rows


def markdown_flowables(text, available_width):
    lines = text.splitlines()
    flowables = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        if line.startswith('```'):
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].startswith('```'):
                code_lines.append(lines[index])
                index += 1
            flowables.append(Preformatted(
                '\n'.join(code_lines),
                STYLES['FIVCode'],
                maxLineLength=100,
            ))
            flowables.append(Spacer(1, 6))
            index += 1
            continue

        if line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].startswith('|'):
                rows.append(lines[index])
                index += 1
            parsed_rows = table_rows(rows)
            if parsed_rows:
                column_count = max(len(row) for row in parsed_rows)
                widths = [available_width / column_count] * column_count
                normalized = [
                    row + [''] * (column_count - len(row))
                    for row in parsed_rows
                ]
                table = Table(normalized, colWidths=widths, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#17324d')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#bcc7d3')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                flowables.extend([table, Spacer(1, 8)])
            continue

        heading = re.match(r'^(#{1,3})\s+(.+)$', line)
        if heading:
            level = len(heading.group(1))
            style = {1: 'FIVHeading1', 2: 'FIVHeading2', 3: 'FIVHeading3'}[level]
            flowables.append(Paragraph(
                inline_markup(heading.group(2)),
                STYLES[style],
            ))
            index += 1
            continue

        bullet = re.match(r'^\s*[-*]\s+(.+)$', line)
        numbered = re.match(r'^\s*\d+\.\s+(.+)$', line)
        if bullet or numbered:
            body = bullet.group(1) if bullet else numbered.group(1)
            flowables.append(Paragraph(
                inline_markup(body),
                STYLES['FIVBullet'],
                bulletText='•' if bullet else '–',
            ))
            index += 1
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not lines[index].startswith(('#', '|', '```'))
            and not re.match(r'^\s*[-*]\s+', lines[index])
            and not re.match(r'^\s*\d+\.\s+', lines[index])
        ):
            paragraph_lines.append(lines[index].strip())
            index += 1
        flowables.append(Paragraph(
            inline_markup(' '.join(paragraph_lines)),
            STYLES['BodyText'],
        ))
    return flowables


def draw_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#d0d7de'))
    canvas.line(0.65 * inch, 0.55 * inch, 7.85 * inch, 0.55 * inch)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#57606a'))
    canvas.drawString(0.7 * inch, 0.35 * inch, 'FIV Hardware Integration Plan')
    canvas.drawRightString(7.8 * inch, 0.35 * inch, f'Page {document.page}')
    canvas.restoreState()


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(
    name='CoverTitle',
    parent=STYLES['Title'],
    fontName='Helvetica-Bold',
    fontSize=26,
    leading=32,
    textColor=colors.HexColor('#12304a'),
    alignment=TA_CENTER,
    spaceAfter=16,
))
STYLES.add(ParagraphStyle(
    name='CoverSubtitle',
    parent=STYLES['BodyText'],
    fontSize=13,
    leading=19,
    textColor=colors.HexColor('#44576a'),
    alignment=TA_CENTER,
))
STYLES.add(ParagraphStyle(
    name='FIVHeading1',
    parent=STYLES['Heading1'],
    fontSize=17,
    leading=21,
    textColor=colors.HexColor('#12304a'),
    spaceBefore=14,
    spaceAfter=8,
))
STYLES.add(ParagraphStyle(
    name='FIVHeading2',
    parent=STYLES['Heading2'],
    fontSize=13,
    leading=17,
    textColor=colors.HexColor('#1e5a84'),
    spaceBefore=10,
    spaceAfter=5,
))
STYLES.add(ParagraphStyle(
    name='FIVHeading3',
    parent=STYLES['Heading3'],
    fontSize=11,
    leading=14,
    textColor=colors.HexColor('#34495e'),
    spaceBefore=8,
    spaceAfter=4,
))
STYLES.add(ParagraphStyle(
    name='FIVCode',
    fontName='Courier',
    fontSize=7.6,
    leading=10,
    leftIndent=8,
    rightIndent=8,
    backColor=colors.HexColor('#f3f5f7'),
    borderColor=colors.HexColor('#d0d7de'),
    borderWidth=0.4,
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=8,
))
STYLES['BodyText'].fontSize = 9.2
STYLES['BodyText'].leading = 13
STYLES['BodyText'].spaceAfter = 6
STYLES.add(ParagraphStyle(
    name='FIVBullet',
    parent=STYLES['BodyText'],
    leftIndent=20,
    firstLineIndent=-10,
    spaceAfter=4,
))


def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.8 * inch,
        title='FIV Hardware Integration Plan',
        author='FIV Team',
    )
    story = [
        Spacer(1, 1.8 * inch),
        Paragraph('FIV Hardware<br/>Integration Plan', STYLES['CoverTitle']),
        Paragraph(
            'Jetson Orin Nano · Hokuyo UST-10LX · VESC chassis<br/>'
            'Simulation, manual control, autonomy, and stereo camera roadmap',
            STYLES['CoverSubtitle'],
        ),
        Spacer(1, 0.35 * inch),
        Paragraph(
            'Prepared 13 November 2026 · ROS 2 Humble / JetPack 6.x baseline',
            STYLES['CoverSubtitle'],
        ),
        PageBreak(),
    ]

    for source in ('README.md', 'deliverables.md', 'motor-control.md'):
        content = (Path(__file__).parent / source).read_text(encoding='utf-8')
        story.extend(markdown_flowables(content, doc.width))
        if source != 'motor-control.md':
            story.append(PageBreak())

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    print(OUTPUT)


if __name__ == '__main__':
    main()
