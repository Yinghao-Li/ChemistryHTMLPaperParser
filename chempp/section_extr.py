import copy
import re
import bs4
import numpy as np
from typing import List, Optional

from seqlbtoolkit.text import format_text

from .article import (
    ArticleElement,
    ArticleElementType
)
from .table import (
    Table,
    TableRow,
    TableCell
)
from .figure import Figure


def pop_xml_element_iter(root, del_tag: List[str], popped_items: Optional[list] = None):
    if popped_items is None:
        popped_items = list()
    for child in root:

        if child.tag in del_tag:
            popped_items.append(child)
            root.remove(child)
        else:
            pop_xml_element_iter(child, del_tag, popped_items)
    return popped_items


def get_xml_text_iter(element):
    txt = list()
    for t in element.itertext():
        txt.append(t)
    return format_text(''.join(txt))


def xml_section_extract_elsevier(section_root, element_list=None) -> List[ArticleElement]:
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()
    for child in section_root:
        if 'label' in child.tag or 'section-title' in child.tag or 'para' in child.tag:
            target_txt = get_xml_text_iter(child)
            element_type = None
            if 'label' in child.tag:
                element_type = ArticleElementType.SECTION_ID
            elif 'section-title' in child.tag:
                element_type = ArticleElementType.SECTION_TITLE
            elif 'para' in child.tag:
                element_type = ArticleElementType.PARAGRAPH
            element = ArticleElement(type=element_type, content=target_txt)
            element_list.append(element)
        elif 'section' in child.tag:
            xml_section_extract_elsevier(section_root=child, element_list=element_list)
    return element_list


def xml_section_extract_acs(section_root, element_list=None) -> List[ArticleElement]:
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()
    for child in section_root:
        if child.tag in ['label', 'title', 'p']:
            xml_tables = list()
            xml_figures = list()

            if child.tag == 'label':
                element_type = ArticleElementType.SECTION_ID
                target_txt = get_xml_text_iter(child)

            elif child.tag == 'title':
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = get_xml_text_iter(child)

            else:  # child.tag == 'p'
                child_cp = copy.deepcopy(child)
                items = pop_xml_element_iter(child_cp, [r'table-wrap', r'fig'])
                for item in items:
                    if item.tag == r'table-wrap':
                        xml_tables.append(item)
                    elif item.tag == r'fig':
                        xml_figures.append(item)

                element_type = ArticleElementType.PARAGRAPH
                target_txt = get_xml_text_iter(child_cp)

            element = ArticleElement(type=element_type, content=target_txt)
            element_list.append(element)

            for xml_table in xml_tables:
                element_type = ArticleElementType.TABLE
                tbl = xml_table_extract_acs(xml_table)
                element = ArticleElement(type=element_type, content=tbl)
                element_list.append(element)

            for xml_figure in xml_figures:
                element_type = ArticleElementType.FIGURE
                fig = xml_figure_extract(xml_figure)
                if not fig.caption:
                    continue
                element = ArticleElement(type=element_type, content=fig)
                element_list.append(element)

        elif child.tag == 'sec':
            xml_section_extract_acs(section_root=child, element_list=element_list)

    return element_list


def html_section_extract_nature(section_root,
                                element_list: Optional[List] = None):
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()

    for child in section_root.children:
        block_name = child.name
        try:
            # if the child is a section title
            if re.match(r"h[0-9]", block_name):
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif block_name == 'p':
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif 'figure' in block_name:
                element_type = ArticleElementType.FIGURE
                fig = html_figure_extract_springer(child)
                element_list.append(ArticleElement(type=element_type, content=fig))
            elif 'table' in block_name:
                continue
            else:
                html_section_extract_nature(section_root=child, element_list=element_list)
        except TypeError:
            pass
    return element_list


def html_section_extract_wiley(section_root,
                               element_list: Optional[List] = None):
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()

    for child in section_root.children:

        child_name = child.name
        if isinstance(child, bs4.element.Tag):
            child_class = child.attrs.get('class', '')
            if isinstance(child_class, list):
                child_class = ''.join(child_class)
        else:
            child_class = ''

        try:
            # if the child is a section title
            if re.match(r"h[0-9]", child_name):
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif child_name == 'p':
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif child_name == 'div' and child_class == 'article-table-content':
                element_type = ArticleElementType.TABLE
                tbl = html_table_extract_wiley(child)
                element_list.append(ArticleElement(type=element_type, content=tbl))
            elif 'figure' in child_name:
                element_type = ArticleElementType.FIGURE
                fig = html_figure_extract_wiley(child)
                if not fig.caption:
                    continue
                element_list.append(ArticleElement(type=element_type, content=fig))
            elif 'table' in child_name:
                continue
            else:
                html_section_extract_wiley(section_root=child, element_list=element_list)
        except TypeError:
            pass
    return element_list


def html_section_extract_rsc(section_root,
                             element_list: Optional[List] = None,
                             n_h2: Optional[int] = None):
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()

    if n_h2 is None:
        n_h2 = len(section_root.find_all('h2'))

    for child in section_root.children:

        child_name = child.name
        if isinstance(child, bs4.element.Tag):
            child_class = child.attrs.get('class', '')
            if isinstance(child_class, list):
                child_class = ''.join(child_class)
        else:
            child_class = ''

        try:
            # if the child is a section title
            if re.match(r"h[2-9]+", child_name):
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif child_name == 'p':
                # the article cannot start with paragraph
                if not element_list:
                    if 'abstract' in child_class.lower():
                        element_list.append("<abs>")
                    continue
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif child_name == 'span':
                if n_h2 > 1:
                    if not element_list:
                        if len(child.find_all('h2')) > 0:
                            html_section_extract_rsc(section_root=child, element_list=element_list, n_h2=n_h2)
                        continue
                    cid = child.get('id', '')
                    if len(element_list) == 1 and element_list[0] == '<abs>':
                        element_type = ArticleElementType.PARAGRAPH
                        target_txt = format_text(child.text)
                        element_list[0] = ArticleElement(type=element_type, content=target_txt)
                        continue
                    elif element_list[-1].type != ArticleElementType.SECTION_TITLE and 'sec' not in cid:
                        continue
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif child_name == 'div' and child_class == 'rtable__wrapper':
                tbl = html_table_extract_rsc(child)
                element_type = ArticleElementType.TABLE
                element_list.append(ArticleElement(type=element_type, content=tbl))
            # skip table captions (will be captured in `html_table_extract_rsc`)
            elif child_name == 'div' and child_class == 'table_caption':
                continue
            # skip figures (for now)
            elif 'figure' in child_name or (child_name == 'div' and child_class == 'image_table'):
                fig = html_figure_extract_rsc(child)
                element_type = ArticleElementType.FIGURE
                element_list.append(ArticleElement(type=element_type, content=fig))
            else:
                html_section_extract_rsc(section_root=child, element_list=element_list, n_h2=n_h2)
        except TypeError:
            pass
    return element_list


def html_section_extract_springer(section_root,
                                  element_list: Optional[List] = None):
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()

    for child in section_root.children:
        child_name = child.name
        if isinstance(child, bs4.element.Tag):
            child_class = child.attrs.get('class', '')
            if isinstance(child_class, list):
                child_class = ''.join(child_class)
        else:
            child_class = ''
        try:
            # if the child is a section title
            if re.match(r"h[0-9]", child_name):
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif child_name == 'p':
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif 'figure' in child_name:
                element_type = ArticleElementType.FIGURE
                fig = html_figure_extract_springer(child)
                element_list.append(ArticleElement(type=element_type, content=fig))
            elif 'table' in child_name or (child_name == 'div' and child_class == 'Table'):
                continue
            elif child_name == 'div' and child_class == 'Table':
                tbl = html_table_extract_springer(child)
                element_type = ArticleElementType.TABLE
                element_list.append(ArticleElement(type=element_type, content=tbl))
            elif child_name == 'div' and child_class == 'Para':

                for s in child.find_all('div', {"class": "Table"}):
                    table_element = s.extract()
                    element_type = ArticleElementType.TABLE
                    tbl = html_table_extract_springer(table_element)
                    element_list.append(ArticleElement(type=element_type, content=tbl))
                for s in child.find_all('figure'):
                    fig_element = s.extract()
                    element_type = ArticleElementType.FIGURE
                    fig = html_figure_extract_springer(fig_element)
                    element_list.append(ArticleElement(type=element_type, content=fig))

                if not child.find_all('p'):
                    element_type = ArticleElementType.PARAGRAPH
                    target_txt = format_text(child.text)
                    element_list.append(ArticleElement(type=element_type, content=target_txt))
                else:
                    html_section_extract_springer(section_root=child, element_list=element_list)
            else:
                html_section_extract_springer(section_root=child, element_list=element_list)
        except TypeError:
            pass
    return element_list


def html_section_extract_aip(section_root,
                             element_list: Optional[List] = None):
    if element_list is None:
        element_list = list()

    sections = section_root.find_all('div')

    for section in sections:
        try:
            if 'NLM_paragraph' in section['class']:
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(section.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
        except KeyError:
            pass
    return element_list


def get_leaf_section_elements(soup: bs4.BeautifulSoup, text=None):
    """
    Support function for `article_construct_html_elsevier`
    """
    if text is None:
        text = ['']

    block_name = soup.name
    if isinstance(soup, bs4.element.Tag):
        root_class = soup.attrs.get('class', '')
        if isinstance(root_class, list):
            root_class = ''.join(root_class)
    else:
        root_class = ''

    if re.match(r"h[0-9]", block_name):
        element_type = ArticleElementType.SECTION_TITLE
        target_txt = format_text(soup.text)
        text.append(ArticleElement(type=element_type, content=target_txt))
        text.append('')
        return None
    elif block_name == 'p':
        text.append('')
    elif block_name == 'div' and 'tables' in root_class:
        element_type = ArticleElementType.TABLE
        tbl = html_table_extract_elsevier(soup)
        text.append(ArticleElement(type=element_type, content=tbl))
        text.append('')
        return None
    elif 'figure' in block_name:
        element_type = ArticleElementType.FIGURE
        fig = html_figure_extract_elsevier(soup)
        text.append(ArticleElement(type=element_type, content=fig))
        text.append('')
        return None

    for child in soup.children:
        if isinstance(child, bs4.element.NavigableString):
            text[-1] += str(child)
        else:
            get_leaf_section_elements(child, text=text)
    return text


def html_section_extract_elsevier(section_root,
                                  element_list: Optional[List] = None,
                                  record_data: Optional[bool] = False):
    """
    Depth-first search of the text in sections
    """
    if element_list is None:
        element_list = list()

    for child in section_root:
        block_name = child.name

        if isinstance(child, bs4.element.Tag):
            child_class = child.attrs.get('class', '')
            if isinstance(child_class, list):
                child_class = ''.join(child_class)
        else:
            child_class = ''

        try:
            # if the child is a section
            if block_name == 'section':
                sec_id = child.get('id', '').lower()
                if (not sec_id.startswith('s')) and ('sec' not in sec_id):
                    sub_secs = child.find_all('section')

                    exist_sub_para = False
                    for sub_sec in sub_secs:
                        sub_sec_id = sub_sec.get('id', '').lower()
                        if sub_sec_id.startswith('s') or ('sec' in sub_sec_id):
                            exist_sub_para = True
                            break
                    if exist_sub_para:
                        html_section_extract_elsevier(
                            section_root=child,
                            element_list=element_list,
                            record_data=False
                        )
                    else:
                        continue
                elif not child.find_all('section'):  # leaf section
                    if record_data or 'sec' in sec_id:

                        ele_list = get_leaf_section_elements(child)
                        new_list = list()
                        for ele in ele_list:
                            if not ele:
                                continue
                            if not isinstance(ele, str):
                                new_list.append(ele)
                            else:
                                sub_txt = ele.split('\n')
                                for txt in sub_txt:
                                    if not txt:
                                        continue
                                    element_type = ArticleElementType.PARAGRAPH
                                    target_txt = format_text(txt)
                                    new_list.append(ArticleElement(type=element_type, content=target_txt))
                        element_list += new_list
                else:
                    html_section_extract_elsevier(
                        section_root=child,
                        element_list=element_list,
                        record_data=True
                    )
            # if the child is a section title
            elif re.match(r"h[0-9]", block_name):
                if record_data:
                    element_type = ArticleElementType.SECTION_TITLE
                    target_txt = format_text(child.text)
                    element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif block_name == 'p':
                if record_data:
                    element_type = ArticleElementType.PARAGRAPH
                    target_txt = format_text(child.text)
                    element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif block_name == 'div' and 'tables' in child_class:
                if record_data:
                    element_type = ArticleElementType.TABLE
                    tbl = html_table_extract_elsevier(child)
                    element_list.append(ArticleElement(type=element_type, content=tbl))
            elif 'figure' in block_name:
                if record_data:
                    element_type = ArticleElementType.FIGURE
                    fig = html_figure_extract_elsevier(child)
                    element_list.append(ArticleElement(type=element_type, content=fig))
            else:
                html_section_extract_elsevier(
                    section_root=child,
                    element_list=element_list,
                    record_data=record_data
                )
        except TypeError:
            pass
    return element_list


def html_section_extract_acs(section_root,
                             element_list: Optional[List] = None):
    """
    Depth-first search of the text in the sections
    """
    if element_list is None:
        element_list = list()

    for child in section_root.children:
        block_name = child.name
        try:
            # if the child is a section title
            if re.match(r"h[0-9]", block_name):
                hid = child.get('id', '')
                if not re.match(r"_i[0-9]+", hid):
                    continue
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif block_name == 'div':
                div_class = child.get('class', [''])
                if len(div_class) == 0:
                    div_class = ['']

                elif div_class[0] == "NLM_p":

                    for s in child.find_all('figure'):
                        fig_element = s.extract()
                        element_type = ArticleElementType.FIGURE
                        fig = html_figure_extract_acs(fig_element)
                        element_list.append(ArticleElement(type=element_type, content=fig))
                    html_section_extract_acs(section_root=child, element_list=element_list)

                    for s in child.find_all('div', {"class": "NLM_table-wrap"}):
                        table_element = s.extract()
                        element_type = ArticleElementType.TABLE
                        tbl = html_table_extract_acs(table_element)
                        element_list.append(ArticleElement(type=element_type, content=tbl))

                    element_type = ArticleElementType.PARAGRAPH
                    target_txt = format_text(child.text)
                    element_list.append(ArticleElement(type=element_type, content=target_txt))

                elif div_class[0] == "NLM_table-wrap":
                    tbl = html_table_extract_acs(child)
                    element_type = ArticleElementType.TABLE
                    element_list.append(ArticleElement(type=element_type, content=tbl))
                else:
                    html_section_extract_acs(section_root=child, element_list=element_list)
            elif 'figure' in block_name:
                continue
            else:
                html_section_extract_acs(section_root=child, element_list=element_list)
        except TypeError:
            pass
    return element_list


def html_section_extract_aaas(section_root,
                              element_list: Optional[List] = None):
    """
    Depth-first search of the text in the sections
    """

    if element_list is None:
        element_list = list()

    for child in section_root.children:
        block_name = child.name
        try:
            # if the child is a section title
            if re.match(r"h[2-9]", block_name):
                h2_class = child.get('class', [])
                if len(h2_class) > 0:
                    continue
                element_type = ArticleElementType.SECTION_TITLE
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            # if the child is a section block
            elif block_name == 'p':
                pid = child.get('id', '')
                if not re.match(r"p-[1-9]+", pid):
                    continue
                element_type = ArticleElementType.PARAGRAPH
                target_txt = format_text(child.text)
                element_list.append(ArticleElement(type=element_type, content=target_txt))
            elif 'figure' in block_name or 'table' in block_name:
                continue
            else:
                html_section_extract_aaas(section_root=child, element_list=element_list)
        except TypeError:
            pass

    return element_list


def xml_table_extract_elsevier(xml_table):
    table = Table()
    footnotes = list()
    rows = list()
    table.id = xml_table.attrib.get('id', None)
    for child in xml_table:
        if 'label' in child.tag:
            table.label = child.text
        elif 'caption' in child.tag:
            table.caption = get_xml_text_iter(child)
        elif 'table-footnote' in child.tag:
            footnotes.append(get_xml_text_iter(child))
        elif 'legend' in child.tag:
            footnotes.append(get_xml_text_iter(child))
        elif 'tgroup' in child.tag:
            for xml_row in child.iter(r'{http://www.elsevier.com/xml/common/cals/dtd}row'):
                cells = list()
                for xml_entry in xml_row:
                    if 'entry' in xml_entry.tag:
                        if 'namest' in xml_entry.attrib and 'nameend' in xml_entry.attrib:
                            if xml_entry.attrib['namest'].startswith('col'):
                                start = np.int8(xml_entry.attrib['namest'][3:])
                            else:
                                start = np.int8(xml_entry.attrib['namest'])
                            if xml_entry.attrib['nameend'].startswith('col'):
                                end = np.int8(xml_entry.attrib['nameend'][3:])
                            else:
                                end = np.int8(xml_entry.attrib['nameend'])
                            width = end - start + 1
                        else:
                            width = 1
                        if 'morerows' in xml_entry.attrib:
                            height = np.int8(xml_entry.attrib['morerows']) + 1
                        else:
                            height = 1

                        text = get_xml_text_iter(xml_entry)
                        cell = TableCell(text, width, height)
                        cells.append(cell)
                row = TableRow(cells)
                rows.append(row)

    table.footnotes = footnotes
    table.rows = rows
    return table.format_rows()


def xml_table_extract_acs(xml_table):
    table = Table()
    footnotes = list()
    rows = list()
    table.id = xml_table.attrib.get('id', None)
    for child in xml_table:
        if 'label' in child.tag:
            table.label = child.text
        elif 'caption' in child.tag:
            table.caption = get_xml_text_iter(child)
        elif 'table-wrap-foot' in child.tag:
            for fn_element in child:
                if 'fn' in fn_element.tag:
                    footnotes.append(get_xml_text_iter(fn_element))
            # sometimes the footnotes are not wrapped in "fn" tags
            if not footnotes:
                footnotes.append(get_xml_text_iter(child))
        elif 'table' in child.tag:
            for tb_element in child:
                if 'tgroup' in tb_element.tag:
                    for xml_row in tb_element.iter(
                            r'{http://www.niso.org/standards/z39-96/ns/oasis-exchange/table}row'):
                        cells = list()
                        for xml_entry in xml_row:
                            if 'entry' in xml_entry.tag:
                                if 'namest' in xml_entry.attrib and 'nameend' in xml_entry.attrib:
                                    if xml_entry.attrib['namest'].startswith('col'):
                                        start = np.int8(xml_entry.attrib['namest'][3:])
                                    else:
                                        start = np.int8(xml_entry.attrib['namest'])
                                    if xml_entry.attrib['nameend'].startswith('col'):
                                        end = np.int8(xml_entry.attrib['nameend'][3:])
                                    else:
                                        end = np.int8(xml_entry.attrib['nameend'])
                                    width = end - start + 1
                                else:
                                    width = 1
                                if 'morerows' in xml_entry.attrib:
                                    height = np.int8(xml_entry.attrib['morerows']) + 1
                                else:
                                    height = 1

                                text = get_xml_text_iter(xml_entry)
                                cell = TableCell(text, width, height)
                                cells.append(cell)
                        row = TableRow(cells)
                        rows.append(row)

    table.footnotes = footnotes
    table.rows = rows
    return table.format_rows()


def xml_figure_extract(xml_figure):
    figure = Figure()
    figure.id = xml_figure.attrib.get('id', None)

    for child in xml_figure:
        if 'label' in child.tag:
            figure.label = child.text
        elif 'caption' in child.tag:
            figure.caption = get_xml_text_iter(child)

    return figure


def get_html_table_row(tr):
    """
    Get a row of the html table

    Parameters
    ----------
    tr: table row (html tag)

    """
    cells = list()
    for child in tr:
        block_name = child.name
        if block_name in ['th', 'td']:
            height = np.uint8(child.get('rowspan', 1))
            width = np.uint8(child.get('colspan', 1))
            text = format_text(child.text)
            # text = text if text else '<EMPTY>'
            cell = TableCell(text, width, height)
            cells.append(cell)
    return TableRow(cells)


def get_html_table_rows(root, rows: Optional[List] = None, include_foot: Optional[bool] = True):
    """
    get row elements from html table
    """
    if rows is None:
        rows = list()

    if isinstance(root, bs4.element.NavigableString):
        return None

    for child in root.children:
        block_name = child.name
        tb_elements = ['thead', 'tbody', 'tfoot'] if include_foot else ['thead', 'tbody']
        if block_name in tb_elements:
            get_html_table_rows(child, rows)
        elif not include_foot and block_name == 'tfoot':
            continue
        elif block_name == 'tr':
            rows.append(get_html_table_row(child))
    return rows


def html_table_extract_wiley(table_div):
    headers = table_div.find_all('header')
    captions = list()
    for header in headers:
        captions.append(header.text)
    caption = ' '.join(captions)
    caption = format_text(caption)
    table_id = table_div.get('id', '<EMPTY>')

    tb_divs = table_div.find_all('div')
    tb_div = None
    for div in tb_divs:
        div_class = div.get('class', '')
        div_class = ' '.join(div_class) if isinstance(div_class, list) else div_class
        if 'footnotes' in div_class:
            tb_div = div

    footnotes = list()
    if tb_div:
        lis = tb_div.find_all('li')
        for li in lis:
            footnotes.append(format_text(li.text))

    tables = table_div.find_all('table')
    if tables:
        table = tables[0]
        rows = get_html_table_rows(table)
    else:
        rows = list()

    tbl = Table(
        idx=table_id,
        caption=caption,
        rows=rows,
        footnotes=footnotes).format_rows()
    return tbl


def html_figure_extract_wiley(html_figure):
    figure_id = html_figure.get('id', '<EMPTY>')
    label = ' '.join([lb.text for lb in html_figure.find_all("strong", class_="figure__title")])

    caption = ' '.join([cap.text for cap in html_figure.find_all("div", class_="figure__caption-text")])
    caption = format_text(caption)
    figure = Figure(idx=figure_id,
                    label=label,
                    caption=caption)
    return figure


def html_figure_extract_springer(html_figure):
    fig_idx_block = html_figure.figcaption.b
    label = fig_idx_block.text
    figure_id = fig_idx_block.get('id', '<EMPTY>')

    try:
        figure_content = html_figure.find_all('div', class_="c-article-section__figure-content")[0]
        caption = figure_content.find_all('p')[0].text
        caption = format_text(caption)
    except IndexError:
        caption = None

    return Figure(idx=figure_id, label=label, caption=caption)


def get_element_text_recursive(root, text=None):
    if text is None:
        text = list()

    block_name = root.name
    if block_name == 'a' or block_name == 'span':
        return None
    for child in root.children:
        if isinstance(child, bs4.element.NavigableString):
            text.append(format_text(str(child)))
        else:
            get_element_text_recursive(child, text=text)
    return format_text(''.join(text))


def html_table_extract_rsc(table_div):
    tables = table_div.find_all('table')
    if not tables:
        return Table()

    table = tables[0]

    caption_divs = table_div.findPreviousSiblings('div', {"class": "table_caption"})
    if caption_divs:
        caption_div = caption_divs[0]
        caption_span = caption_div.span
        caption = format_text(caption_span.text)
        table_id = caption_span.get('id', '<EMPTY>')
    else:
        caption = ''
        table_id = None

    footnote_ele = table.find_all('tfoot')
    footnotes = list()
    if footnote_ele:
        footnote_content = footnote_ele[0].tr.th
        unnumbered_footnote = get_element_text_recursive(footnote_content)
        if unnumbered_footnote:
            footnotes.append(unnumbered_footnote)
        footnote_as = footnote_content.find_all('a')
        for a in footnote_as:
            if a.get('href', ''):
                continue
            a_span = a.find_next_sibling('span')
            footnote = f'{a.text} {a_span.text}'
            footnotes.append(footnote)

    rows = get_html_table_rows(table, include_foot=False)
    tbl = Table(
        idx=table_id,
        caption=caption,
        rows=rows,
        footnotes=footnotes).format_rows()

    return tbl


def html_figure_extract_rsc(html_figure):
    try:
        title = html_figure.find_all('td', class_="image_title")[0]
        label = title.b.text.strip()
        caption = ' '.join([cap.text for cap in title.find_all('span', class_="graphic_title")])
        caption = format_text(caption)
        return Figure(label=label, caption=caption)
    except IndexError:
        return Figure()


def html_table_extract_springer(table_div):
    caption_divs = table_div.find_all('div', {"class": "Caption"})
    if caption_divs:
        caption_div = caption_divs[0]
        caption_span = caption_div.text
        caption = format_text(caption_span)
    else:
        caption = ''
    table_id = table_div.get('id', '<EMPTY>')

    footnote_div = table_div.find_all('div', {"class": "TableFooter"})
    footnotes = list()
    if footnote_div:
        footnote_ps = footnote_div[0].find_all('p')
        for p in footnote_ps:
            footnotes.append(format_text(p.text))

    tables = table_div.find_all('table')
    if tables:
        table = tables[0]
        rows = get_html_table_rows(table)
    else:
        rows = list()

    tbl = Table(
        idx=table_id,
        caption=caption,
        rows=rows,
        footnotes=footnotes).format_rows()
    return tbl


def get_acs_footnote(footnote_div):
    footnotes = list()
    pars = footnote_div.find_all('p')
    for p in pars:
        for child in p.children:
            if isinstance(child, bs4.element.NavigableString):
                if not footnotes:
                    footnotes.append(format_text(str(child)))
                else:
                    footnotes[-1] += str(child)
            elif child.name == 'i':
                footnotes.append(format_text(child.text))
            else:
                footnotes[-1] += child.text
    return footnotes


def html_table_extract_acs(table_div):
    caption = ''
    table_id = table_div.get('id', '<EMPTY>')
    footnotes = list()
    for child in table_div.children:
        child_class = child.get('class', '')
        child_class = ' '.join(child_class) if isinstance(child_class, list) else child_class
        if 'caption' in child_class.lower():
            caption = format_text(child.text)
        if 'table-wrap-foot' in child_class:
            footnotes = get_acs_footnote(child)

    tables = table_div.find_all('table')
    if tables:
        table = tables[0]
        rows = get_html_table_rows(table)
    else:
        rows = list()

    tbl = Table(
        idx=table_id,
        caption=caption,
        rows=rows,
        footnotes=footnotes).format_rows()
    return tbl


def html_figure_extract_acs(html_figure):
    fig_id = html_figure.get('id', '<EMPTY>')
    caption = format_text(html_figure.figcaption.text)
    return Figure(idx=fig_id, caption=caption)


def html_table_extract_elsevier(table_div):
    caption = ''
    table_id = table_div.get('id', '<EMPTY>')
    footnotes = list()

    for child in table_div.children:
        child_class = child.get('class', '')
        child_class = ' '.join(child_class) if isinstance(child_class, list) else child_class
        if 'captions' in child_class.lower():
            caption = format_text(child.text)
        if 'legend' in child_class.lower():
            footnotes.append(format_text(child.text))
        if 'footnotes' in child_class:
            for foot_element in child.children:
                foot_name = foot_element.name
                if foot_name == 'dt':
                    footnotes.append(f"{format_text(foot_element.text)} ")
                elif foot_name == 'dd':
                    if footnotes:
                        footnotes[-1] += format_text(foot_element.text)
                    else:
                        footnotes.append(format_text(foot_element.text))

    tables = table_div.find_all('table')
    if tables:
        table = tables[0]
        rows = get_html_table_rows(table)
    else:
        rows = list()

    tbl = Table(
        idx=table_id,
        caption=caption,
        rows=rows,
        footnotes=footnotes).format_rows()
    return tbl


def html_figure_extract_elsevier(html_figure):
    fig_id = html_figure.get('id', '<EMPTY>')
    try:
        caption = format_text(html_figure.find_all('span', class_='captions')[0].text)
    except IndexError:
        caption = None

    return Figure(idx=fig_id, caption=caption)
