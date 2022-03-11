import bs4
import copy
import json
import numpy as np

from dataclasses import dataclass
from typing import Optional, List
from bs4 import BeautifulSoup


@dataclass
class TableCell:
    text: str
    width: Optional[np.int8] = 1
    height: Optional[np.int8] = 1
    linked_top: Optional[bool] = False  # judge if the current cell belongs to the above multi-row cell
    linked_left: Optional[bool] = False  # judge if the current cell belongs to the left multi-column cell


class TableRow:
    def __init__(self, cells: List[TableCell]):
        self._cells = cells
        self._width = self._get_width()
        self._expanded_cells = self._expand_cells()

    def __getitem__(self, i):
        return self.expanded_cells[i]

    def __len__(self):
        return self.width

    def _get_width(self):
        cell_widths = [cell.width for cell in self._cells]
        return np.sum(cell_widths)

    @property
    def width(self):
        return self._width

    @property
    def cells(self):
        return self._cells

    @property
    def expanded_cells(self):
        return self._expanded_cells

    @cells.setter
    def cells(self, cells):
        new_widths = [cell.width for cell in cells]
        assert self._width == new_widths, ValueError('The width must equal to the old one!')
        self._cells = cells
        self._expanded_cells = self._expand_cells()

    @expanded_cells.setter
    def expanded_cells(self, cells):
        raise AttributeError("Assigning values to `expanded_cells` is illegal!")

    def __str__(self):
        cell_line = '\t'.join([cell.text for cell in self._cells]) + '\n'
        return cell_line

    def __repr__(self):
        return self.__str__()

    def text(self):
        return self.__str__()

    def _expand_cells(self):
        expanded_cells = list()
        multicolumn_cache = list()
        cell_idx = 0
        while True:
            if multicolumn_cache:
                cached_cell = copy.deepcopy(multicolumn_cache[0])
                cached_cell.width = 1
                cached_cell.linked_left = True
                expanded_cells.append(cached_cell)
                multicolumn_cache[1] -= 1
                if multicolumn_cache[1] == 0:
                    multicolumn_cache = list()
            else:
                expanded_cells.append(self._cells[cell_idx])
                if self._cells[cell_idx].width > 1:
                    multicolumn_cache = [self._cells[cell_idx], self._cells[cell_idx].width - 1]
                cell_idx += 1
            if cell_idx == len(self._cells) and not multicolumn_cache:
                break
        return expanded_cells


class Table:
    def __init__(self,
                 label: Optional[str] = None,
                 idx: Optional[str] = None,
                 caption: Optional[str] = None,
                 rows: Optional[List[TableRow]] = None,
                 footnotes: Optional[List[str]] = None):

        self._label = label
        self._id = idx
        self._caption = caption
        self._rows = rows
        self._footnotes = footnotes

    @property
    def label(self):
        return self._label if self._label is not None else "<EMPTY>"

    @property
    def id(self):
        return self._id if self._id is not None else "<EMPTY>"

    @property
    def caption(self):
        return self._caption if self._caption is not None else ''

    @property
    def rows(self):
        return self._rows if self._rows is not None else []

    @property
    def footnotes(self):
        return self._footnotes if self._footnotes is not None else []

    @property
    def shape(self):
        return len(self), len(self._rows[0]) if self._rows else 0

    @property
    def width(self):
        return len(self._rows[0]) if self._rows else 0

    @property
    def n_columns(self):
        return self.width

    @property
    def height(self):
        return len(self)

    @property
    def n_rows(self):
        return self.height

    @label.setter
    def label(self, x):
        self._label = x

    @id.setter
    def id(self, x):
        self._id = x

    @caption.setter
    def caption(self, x):
        self._caption = x

    @rows.setter
    def rows(self, x):
        self._rows = x

    @footnotes.setter
    def footnotes(self, x):
        self._footnotes = x

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self.rows[idx]
        elif isinstance(idx, tuple) and len(idx) == 2:
            r, c = idx
            return self.rows[r].expanded_cells[c]

    def __str__(self):
        lines = self._label if self._label else ''
        lines += f' {self._caption}\n' if self._caption else ''
        rows = ''.join([row.__str__() for row in self._rows])
        lines += rows
        lines += '\n'.join(self._footnotes) if self._footnotes else ''
        return lines

    def __len__(self):
        return len(self._rows)

    def __repr__(self):
        return self.__str__()

    def _repr_html_(self):
        return self.write_html().prettify()

    def text(self):
        return self.__str__()

    def format_rows(self):
        """
        Deal with multi-row cells by appending dummy cells below them in each row
        """
        multirow_cache = dict()
        formatted_rows = list()
        for row in self.rows:
            cells = list()
            cell_idx = 1
            for cell in row.cells:
                while True:
                    if cell_idx in multirow_cache:
                        _, width, text = multirow_cache[cell_idx]
                        multirow_cell = TableCell(text, width, linked_top=True)

                        multirow_cache[cell_idx][0] -= 1
                        assert multirow_cache[cell_idx][0] >= 0
                        if multirow_cache[cell_idx][0] == 0:
                            multirow_cache.pop(cell_idx)

                        # check if we have already appended the multi-row cells before
                        if cell.text == text and cell.linked_top is True:
                            pass
                        else:
                            cell_idx += width
                            cells.append(multirow_cell)
                    else:
                        break

                # cache the properties of multi-row cells
                if cell.height > 1:
                    multirow_cache[cell_idx] = [cell.height - 1, cell.width, cell.text]

                cell_idx += cell.width
                cells.append(cell)
            formatted_rows.append(TableRow(cells))
        self._rows = formatted_rows
        return self

    def body_to_lists(self):
        element_list = list()
        for i in range(self.height):
            row_elements = list()
            for j in range(self.width):
                row_elements.append(self[i, j].text)
            element_list.append(row_elements)
        return element_list

    def write_html(self, root: Optional[bs4.element.Tag] = None):
        soup = BeautifulSoup()

        if root is None:
            root = BeautifulSoup()
        html_table = soup.new_tag('table')
        root.insert(len(root), html_table)

        if self.caption:
            caption = soup.new_tag('caption')
            html_table.insert(len(html_table), caption)
            if self.label and self.label != '<EMPTY>':
                cap_txt = f'{self.label} {self.caption}'
            else:
                cap_txt = self.caption
            caption.insert(0, cap_txt)

        tbody = soup.new_tag('tbody')
        html_table.insert(len(html_table), tbody)
        for row in self.rows:
            table_row = soup.new_tag('tr')
            tbody.insert(len(tbody), table_row)

            for entry in row.cells:
                if entry.linked_top:
                    continue
                table_data = soup.new_tag('td', colspan=str(entry.width), rowspan=str(entry.height))
                table_row.insert(len(table_row), table_data)
                table_data.insert(0, entry.text)

        if self.footnotes:
            tfoot = soup.new_tag('tfoot')
            html_table.insert(len(html_table), tfoot)
            for footnote in self.footnotes:
                table_row = soup.new_tag('tr')
                tfoot.insert(len(tfoot), table_row)
                table_data = soup.new_tag('td', colspan=str(self.rows[0].width) if self.rows else 1)
                table_row.insert(0, table_data)
                table_data.insert(0, footnote)

        return root

    def save_json(self, file_name):
        json_elements = {
            'caption': self.caption,
            'body': self.body_to_lists(),
            'footnotes': self.footnotes
        }
        with open(file_name, 'w', encoding='UTF-8') as f:
            json.dump(json_elements, f, indent=2, ensure_ascii=False)


def set_table_style(root: bs4.element.Tag):
    soup = BeautifulSoup()
    style = soup.new_tag('style')
    root.insert(len(root), style)
    style_string = \
        """
        table {
          font-family: arial, sans-serif;
          border-collapse: collapse;
          width: 90%;
          margin-left: auto;
          margin-right: auto;
          margin-top: 1.5em;
          margin-bottom: 1.5em;
        }

        caption {
          margin-bottom: 0.5em;
        }

        tbody td, th {
          border: 1px solid #dddddd;
          text-align: left;
          padding: 8px;
          font-size: 80%;
        }

        tbody tr:nth-child(even) {
          background-color: #dddddd;
        }

        tfoot td, th{
          border: none;
          text-align: left;
          padding: 8px;
          font-size: 70%;
          line-height: 100%;
        }

        tfoot tr {
          background-color: #ffffff;
        }
        """
    style.insert(0, style_string)
    return root
