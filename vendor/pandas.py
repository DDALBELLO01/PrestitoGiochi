"""Small pandas-compatible Excel adapter used by this application."""
from datetime import datetime, date
from io import BytesIO
from math import isnan
from openpyxl import Workbook, load_workbook


class DataFrame:
    def __init__(self, data):
        self.data = data

    def to_excel(self, writer, sheet_name, index=False):
        sheet = writer.workbook.create_sheet(sheet_name)
        if not self.data:
            return
        headers = list(self.data[0].keys())
        sheet.append(headers)
        for row in self.data:
            sheet.append([row.get(header) for header in headers])

    def iterrows(self):
        for index, row in enumerate(self.data):
            yield index, row


def notna(value):
    if value is None:
        return False
    try:
        return not isnan(value)
    except TypeError:
        return True


def to_datetime(value, format=None):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.strptime(str(value), format) if format else datetime.fromisoformat(str(value))


class ExcelWriter:
    def __init__(self, path, engine=None):
        self.path = path
        self.workbook = Workbook()
        self.workbook.remove(self.workbook.active)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.workbook.save(self.path)


def read_excel(source, sheet_name=None):
    workbook = load_workbook(source, read_only=True, data_only=True)
    names = workbook.sheetnames if sheet_name is None else [sheet_name]
    result = {}
    for name in names:
        sheet = workbook[name]
        rows = list(sheet.iter_rows(values_only=True))
        headers = [str(value) if value is not None else '' for value in rows[0]] if rows else []
        result[name] = DataFrame([
            {header: row[index] if index < len(row) else None for index, header in enumerate(headers)}
            for row in rows[1:]
        ])
    return result if sheet_name is None else result[sheet_name]
