import csv


class CSVReader:

    def __init__(self, file_object, header, columns_mapper, delimiter=None):
        file_object.seek(0)
        self._header = header
        self._columns_mapper = columns_mapper
        self._rows = csv.DictReader(file_object, delimiter=delimiter or '|')

    def _validate_header(self):
        if not self._rows.fieldnames == self._header:
            raise csv.Error('Invalid Header: expected {}, got {}'.format(
                self._header,
                self._rows.fieldnames
            ))

    def get_data(self):
        self._validate_header()
        return self._columns_mapper(self._rows)
