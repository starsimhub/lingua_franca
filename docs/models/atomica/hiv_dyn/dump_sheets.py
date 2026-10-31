"""
Write every sheet of the three spreadsheets as text, so the model can be read without Excel.

    ../../../../_envs/atomica/bin/python dump_sheets.py

Each sheet becomes `original/sheets/<workbook>__<sheet>.csv`, with the cells as Atomica reads them
(a cell holding a formula is written as its stored result). It also prints the count of model lines.
"""
import os
import csv
import openpyxl

here = os.path.dirname(os.path.abspath(__file__))
books = ['hiv_dyn_framework', 'hiv_dyn_databook', 'hiv_dyn_progbook']
skip = ['about', 'cascades'] # A name and the plots: not part of the model that is run


def text(val):
    if val is None:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)


def dump(book):
    """ Write each sheet of a workbook as CSV, and return the lines of each """
    wb = openpyxl.load_workbook(os.path.join(here, 'original', f'{book}.xlsx'), data_only=True)
    out = dict()
    for ws in wb.worksheets:
        rows = [[text(cell.value) for cell in row] for row in ws.iter_rows()]
        width = max([i + 1 for row in rows for i,val in enumerate(row) if val] or [0])
        rows = [row[:width] for row in rows]
        while rows and not any(rows[-1]):
            rows.pop()
        name = f"{book}__{ws.title.lower().replace(' ', '_')}.csv"
        path = os.path.join(here, 'original', 'sheets', name)
        with open(path, 'w', newline='') as f:
            csv.writer(f, lineterminator='\n').writerows(rows)
        with open(path) as f:
            lines = [line.rstrip('\n').rstrip(',') for line in f]
        out[name] = [line for line in lines if line]
    return out


if __name__ == '__main__':
    os.makedirs(os.path.join(here, 'original', 'sheets'), exist_ok=True)
    total = 0
    for book in books:
        for name,lines in dump(book).items():
            count = sum(2 if len(line) > 100 else 1 for line in lines)
            counted = not any(name.endswith(f'__{key}.csv') for key in skip)
            total += count*counted
            print(f'{name:45s} {len(lines):3d} rows, {count:3d} lines' + ('' if counted else ' (not counted)'))
    print(f'Total: {total} lines')
