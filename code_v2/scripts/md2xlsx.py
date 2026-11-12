# -*- coding: utf-8 -*-
"""Convert the first Markdown table in a file into a formatted .xlsx workbook.

    python md2xlsx.py <input.md> [output.xlsx]

Formatting: bold header with fill, frozen header row, per-column width, two-decimal
number format, autofilter, and bold rows whose first cell is wrapped in ** (summary rows).
The text before the table (title + note) is written to a second sheet named "Notes".
Requires: openpyxl.
"""
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEAD_FILL = PatternFill('solid', fgColor='DDE5F0')
SUM_FILL = PatternFill('solid', fgColor='F2F2F2')
THIN = Side(style='thin', color='BFBFBF')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def parse_md(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    table_start = None
    rows = []
    notes = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('|') and s.endswith('|'):
            if table_start is None:
                table_start = i
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                continue                      # alignment row
            rows.append(cells)
        elif table_start is None:
            notes.append(ln)
        else:
            break                         # stop at the end of the first contiguous table
    if not rows:
        raise SystemExit('no markdown table found in %s' % path)
    return rows, '\n'.join(notes).strip()


def to_number(s):
    t = s.replace('**', '').replace(',', '').strip()
    if re.fullmatch(r'-?\d+(\.\d+)?', t):
        return float(t) if '.' in t else int(t)
    return None


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '.xlsx'
    rows, notes = parse_md(src)

    header, body = rows[0], rows[1:]
    wb = Workbook()
    ws = wb.active
    ws.title = 'results'

    for j, h in enumerate(header, start=1):
        c = ws.cell(row=1, column=j, value=h.replace('**', ''))
        c.font = Font(bold=True)
        c.fill = HEAD_FILL
        c.border = BORDER
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for i, row in enumerate(body, start=2):
        bold = row and row[0].startswith('**')
        for j, raw in enumerate(row, start=1):
            num = to_number(raw) if j > 1 else None
            c = ws.cell(row=i, column=j, value=num if (num is not None and j > 1) else raw.replace('**', ''))
            c.border = BORDER
            if isinstance(c.value, float):
                c.number_format = '0.00'
            if bold:
                c.font = Font(bold=True)
                c.fill = SUM_FILL

    widths = {}
    for j in range(1, len(header) + 1):
        longest = max(len(str(ws.cell(row=r, column=j).value or '')) for r in range(1, len(body) + 2))
        widths[j] = min(max(10, longest + 2), 42)
    for j, w in widths.items():
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = 'B2' if len(header) > 3 else 'A2'
    ws.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(header)), len(body) + 1)
    ws.row_dimensions[1].height = 32

    if notes:
        wn = wb.create_sheet('Notes')
        for i, ln in enumerate(notes.splitlines(), start=1):
            c = wn.cell(row=i, column=1, value=ln.replace('# ', '').replace('**', ''))
            if ln.startswith('# '):
                c.font = Font(bold=True, size=12)
        wn.column_dimensions['A'].width = 120

    wb.save(dst)
    print('rows=%d cols=%d -> %s' % (len(body), len(header), dst))


if __name__ == '__main__':
    main()
