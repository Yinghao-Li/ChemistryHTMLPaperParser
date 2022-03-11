import os
from typing import Tuple

from bs4 import BeautifulSoup
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from .article import (
    Article,
    ArticleComponentCheck
)
from .section_extr import *


class ArticleFunctions:
    def __init__(self):
        pass

    @staticmethod
    def article_construct_html_nature(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'nature'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split('|')[0].strip()
        article.title = title

        body = soup.body
        sections = body.find_all('section')

        # --- get abstract ---
        abstract = None
        abstract_idx = None
        for i, section in enumerate(sections):
            try:
                if 'abs' in section['aria-labelledby'].lower() or section['data-title'] == 'Abstract':
                    abs_paras = section.find_all('p')
                    abstract = ''
                    for abs_para in abs_paras:
                        abstract += abs_para.text
                    abstract = format_text(abstract.strip())
                    abstract_idx = i
            except KeyError:
                pass
        if not abstract:
            # print('[Warning] No abstract is detected!')
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get sections ---
        content_sections = list()
        for i, section in enumerate(sections):
            try:
                if i == abstract_idx:
                    pass
                else:
                    content_sections.append(section)
            except KeyError:
                pass

        element_list = list()
        for section in content_sections:
            section_elements = html_section_extract_nature(section_root=section)
            if section_elements:
                element_list += section_elements
        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list
        return article, article_component_check

    @staticmethod
    def article_construct_html_wiley(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'wiley'

        # --- get title ---
        title = soup.find_all('title')
        title = title[0].text.split(' - ')[0].strip()
        article.title = title

        body = soup.body
        sections = body.find_all('section')

        # --- get abstract ---
        abstract = None
        for section in sections:
            try:
                if 'article-section__abstract' in section['class']:
                    abs_paras = section.find_all('p')
                    abstract = ''
                    for abs_para in abs_paras:
                        abstract += abs_para.text
                    abstract = format_text(abstract.strip())
            except KeyError:
                pass
        if not abstract:
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get sections ---
        content_sections = None
        for section in sections:
            try:
                if 'article-section__full' in section['class']:
                    content_sections = section
            except KeyError:
                pass

        if content_sections:
            element_list = html_section_extract_wiley(section_root=content_sections)
        else:
            # print(f"[Warning] No section is detected")
            element_list = []
            article_component_check.sections = False

        article.sections = element_list
        return article, article_component_check

    @staticmethod
    def article_construct_html_rsc(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'rsc'

        # --- get title ---
        head = soup.head
        body = soup.body

        title = body.find_all('h1')
        if title:
            title = format_text(title[0].text).strip()
        else:
            title = head.find_all('title')
            title = '-'.join(title[0].text.split('-')[:-1]).strip()
        article.title = title

        paras = body.find_all('p')

        # --- get abstract ---
        abstract = ''
        for section in paras:
            try:
                if 'abstract' in section['class']:
                    abstract = section.text
                    abstract = format_text(abstract.strip())
            except KeyError:
                pass
        if not abstract:
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get sections ---

        element_list = html_section_extract_rsc(section_root=body)
        if '<abs>' in element_list:
            element_list.remove('<abs>')
        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list
        return article, article_component_check

    @staticmethod
    def article_construct_html_springer(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'springer'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split('|')[0].strip()
        article.title = title

        body = soup.body
        sections = body.find_all('section')

        # --- get abstract ---
        abstract = ''
        abstract_idx = None
        for i, section in enumerate(sections):
            data_title = section.get('data-title', '')
            if isinstance(data_title, str):
                data_title = [data_title.lower()]
            elif isinstance(data_title, list):
                data_title = [t.lower() for t in data_title]
            else:
                data_title = []
            class_element = section.get('class', '')
            if isinstance(class_element, str):
                class_element = [class_element.lower()]
            elif isinstance(class_element, list):
                class_element = [t.lower() for t in class_element]
            else:
                class_element = []
            is_abs = False
            for ele in data_title + class_element:
                if 'abstract' in ele or 'summary' in ele:
                    is_abs = True
            if is_abs:
                abs_paras = section.find_all('p')
                abstract = ''
                for abs_para in abs_paras:
                    abstract += abs_para.text
                abstract = format_text(abstract.strip())
                abstract_idx = i
        if not abstract:
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get sections ---
        content_sections = list()
        for i, section in enumerate(sections):
            try:
                if i != abstract_idx and not section.find_parent('section'):
                    content_sections.append(section)
            except KeyError:
                pass

        element_list = list()
        for section in content_sections:
            section_elements = html_section_extract_springer(section_root=section)
            if section_elements:
                element_list += section_elements
        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list
        return article, article_component_check

    @staticmethod
    def article_construct_html_aip(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'aip'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split(':')[0].strip()
        article.title = title

        element_list = html_section_extract_aip(section_root=soup)

        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list
        return article, article_component_check

    @staticmethod
    def article_construct_html_acs(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'acs'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split(' | ')[0].strip()
        article.title = title

        # --- get abstract ---
        body = soup.body
        h2s = body.find_all('h2')
        abs_h2 = None
        for h2 in h2s:
            h2_class = h2.get('class', [''])
            if len(h2_class) == 0:
                h2_class = ['']
            if h2_class[0] == 'article_abstract-title':
                abs_h2 = h2
        if abs_h2 is not None:
            abstract = abs_h2.nextSibling.text.strip()
        else:
            ps = body.find_all('p')
            abs_p = None
            for p in ps:
                if p.get('class', [''])[0] == 'articleBody_abstractText':
                    abs_p = p
            if not abs_p:
                # print('[Warning] Abstract is not found!')
                abstract = ''
                article_component_check.abstract = False
            else:
                abstract = abs_p.text.strip()

        abstract = format_text(abstract)
        article.abstract = abstract

        # --- get body sections ---
        element_list = html_section_extract_acs(section_root=soup)

        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list

        return article, article_component_check

    @staticmethod
    def article_construct_html_elsevier(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'elsevier'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split(' - ')[0].strip()
        article.title = title

        # --- get abstract ---
        body = soup.body
        abs_divs = body.find_all('div', {"class": "Abstracts"})
        if abs_divs:
            abs_div = abs_divs[0]
        else:
            abs_div = []
        abstract = list()
        for div in abs_div:

            for s in div.find_all('h2'):
                s.extract()

            div_class = div.get('class', '')
            div_class = ' '.join(div_class) if isinstance(div_class, list) else div_class
            if 'graphical' not in div_class and 'author-highlights' not in div_class:
                abstract.append(format_text(div.text))
        if not abstract:
            abstract = ''
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get body sections ---
        element_list = html_section_extract_elsevier(section_root=body)

        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        article.sections = element_list

        return article, article_component_check

    @staticmethod
    def article_construct_html_aaas(soup: bs4.BeautifulSoup, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'aaas'

        # --- get title ---
        head = soup.head
        title = head.find_all('title')
        title = title[0].text.split(' | ')[0].strip()
        article.title = title

        # --- get abstract ---
        body = soup.body
        h2s = body.find_all('h2')
        abs_h2 = None
        for h2 in h2s:
            if h2.text.lower() == 'abstract':
                abs_h2 = h2
                break
        if abs_h2:
            abstract = format_text(abs_h2.nextSibling.text)
        else:
            abstract = None
        if not abstract:
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abstract

        # --- get body sections ---
        element_list = html_section_extract_aaas(section_root=body)
        if not element_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False
        article.sections = element_list

        return article, article_component_check

    @staticmethod
    def article_construct_xml_elsevier(root: ET.Element, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'elsevier'

        ori_txt = root.findall(r'{http://www.elsevier.com/xml/svapi/article/dtd}originalText')[0]
        doc = ori_txt.findall(r'{http://www.elsevier.com/xml/xocs/dtd}doc')[0]

        # get title
        title_element = list(doc.iter(tag=r'{http://www.elsevier.com/xml/common/dtd}title'))[-1]
        iter_txt = list()
        for txt in title_element.itertext():
            txt_s = txt.strip()
            if txt_s:
                iter_txt.append(txt)
        title = ''.join(iter_txt).strip()
        article.title = title

        # get abstract
        abs_elements = list(doc.iter(tag=r'{http://www.elsevier.com/xml/common/dtd}abstract'))
        abs_element = None
        for abs_ele in abs_elements:
            try:
                if abs_ele.attrib['class'] == 'author':
                    abs_element = abs_ele
            except KeyError:
                # print('[ERROR] keyword "class" does not exist!')
                pass

        abs_paras = list()
        try:
            for abs_ele in (abs_element.iter(tag=r'{http://www.elsevier.com/xml/common/dtd}simple-para')):
                abs_text = list()
                for txt in abs_ele.itertext():
                    txt_s = txt.strip()
                    if txt_s:
                        abs_text.append(txt)
                abs_paras.append(''.join(abs_text))
        except Exception:
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abs_paras

        # get tables
        try:
            table_elements = list(doc.iter(tag=r'{http://www.elsevier.com/xml/common/dtd}table'))
            section_list = []
            for table_element in table_elements:
                tbl = xml_table_extract_elsevier(table_element)
                tbl_element = ArticleElement(type=ArticleElementType.TABLE, content=tbl)
                section_list.append(tbl_element)
        except Exception:
            section_list = []

        # get article content
        try:
            sections_element = list(doc.iter(tag=r'{http://www.elsevier.com/xml/common/dtd}sections'))[-1]
            section_list += xml_section_extract_elsevier(section_root=sections_element)
        except Exception:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        new_section_list = list()
        for i in range(len(section_list)):
            if section_list[i].type == ArticleElementType.SECTION_ID:
                continue
            elif section_list[i].type == ArticleElementType.SECTION_TITLE:
                if i > 0 and section_list[i - 1].type == ArticleElementType.SECTION_ID:
                    combined_section_title = section_list[i - 1].content + ' ' + section_list[i].content
                    new_section_list.append(
                        ArticleElement(type=ArticleElementType.SECTION_TITLE, content=combined_section_title)
                    )
                else:
                    new_section_list.append(section_list[i])
            else:
                new_section_list.append(section_list[i])

        article.sections = new_section_list

        return article, article_component_check

    @staticmethod
    def article_construct_xml_acs(root: ET.Element, doi: str):
        article = Article()
        article_component_check = ArticleComponentCheck()
        article.doi = doi
        article.publisher = 'acs'

        front = root.findall('front')[0]

        title_text = list()
        for element in front.iter(tag='article-title'):
            title_text.append(element.text)
        title = format_text(''.join(title_text))
        article.title = title

        abs_text = list()
        for element in front.iter(tag='abstract'):
            if not element.attrib:
                for txt in element.itertext():
                    abs_text.append(txt)
        abstract = format_text(''.join(abs_text))
        if not abstract:
            # print('[Warning] Abstract is not found!')
            article_component_check.abstract = False
        article.abstract = abstract

        # get article content
        body = root.findall('body')[0]
        section_list = xml_section_extract_acs(body)
        if not section_list:
            # print('[Warning] No section is detected!')
            article_component_check.sections = False

        new_section_list = list()
        for i in range(len(section_list)):
            if section_list[i].type == ArticleElementType.SECTION_ID:
                continue
            elif section_list[i].type == ArticleElementType.SECTION_TITLE:
                if i > 0 and section_list[i - 1].type == ArticleElementType.SECTION_ID:
                    combined_section_title = section_list[i - 1].content + ' ' + section_list[i].content
                    new_section_list.append(
                        ArticleElement(type=ArticleElementType.SECTION_TITLE,
                                       content=combined_section_title)
                    )
                else:
                    new_section_list.append(section_list[i])
            else:
                new_section_list.append(section_list[i])

        article.sections = new_section_list

        return article, article_component_check


def check_html_publisher(soup: bs4.BeautifulSoup):
    publisher = None
    try:
        if soup.html.attrs['xmlns:rsc'] == 'urn:rsc.org':
            publisher = 'rsc'
    except KeyError:
        pass
    metas = soup.find_all('meta')
    title = soup.find_all('title')
    pub_web = None
    if title and len(title) >= 1:
        pub_web = title[0].text.strip().split(' - ')[-1]
    for meta in metas:
        try:
            if meta['name'].lower() == 'dc.publisher' and \
                    meta['content'] == 'Springer':
                publisher = 'springer'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    meta['content'] == 'Nature Publishing Group':
                publisher = 'nature'
                break
            elif meta['name'].lower() == 'citation_publisher' and \
                    'John Wiley & Sons, Ltd' in meta['content']:
                publisher = 'wiley'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    (meta['content'] == 'American Institute of PhysicsAIP' or ('AIP Publishing' in meta['content'])):
                publisher = 'aip'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    meta['content'].strip() == 'American Chemical Society':
                publisher = 'acs'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    meta['content'].strip() == 'The Royal Society of Chemistry':
                publisher = 'rsc'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    meta['content'].strip() == 'American Association for the Advancement of Science':
                publisher = 'aaas'
                break
            elif meta['name'].lower() == 'dc.publisher' and \
                    meta['content'].strip() == 'World Scientific Publishing Company':
                publisher = 'cjps'
            elif meta['name'] == 'citation_springer_api_url':
                publisher = 'springer'
                break
        except KeyError:
            pass
    if not publisher and pub_web.lower() == 'sciencedirect':
        publisher = 'elsevier'
    if not publisher:
        raise ValueError('Publisher not found!')

    return publisher


def check_xml_publisher(root: ET.Element):
    publisher = None

    tag = root.tag
    if 'elsevier' in tag:
        publisher = 'elsevier'
    else:
        for child in root.iter():
            if child.tag == 'publisher-name':
                text = child.text
                text = format_text(text)
                if text == 'American Chemical Society':
                    publisher = 'acs'
                break
    if not publisher:
        raise ValueError('Publisher not found!')

    return publisher


def search_html_doi_publisher(soup, publisher=None):
    if not publisher:
        publisher = check_html_publisher(soup)

    if publisher == 'acs':
        doi_sec = soup.find_all('div', {'class': 'article_header-doiurl'})
        doi_url = doi_sec[0].text.strip().lower()
    elif publisher == 'wiley':
        doi_sec = soup.find_all('a', {'class': 'epub-doi'})
        doi_url = doi_sec[0].text.strip().lower()
    elif publisher == 'springer':
        doi_spans = soup.find_all('span')
        doi_sec = None
        for span in doi_spans:
            span_class = span.get("class", [''])
            span_class = ' '.join(span_class) if isinstance(span_class, list) else span_class
            if 'bibliographic-information__value' in span_class and 'doi.org' in span.text:
                doi_sec = span
        doi_url = doi_sec.text.strip().lower()
    elif publisher == 'rsc':
        doi_sec = soup.find_all('div', {'class': 'article_info'})
        doi_url = doi_sec[0].a.text.strip().lower()
    elif publisher == 'elsevier':
        doi_sec = soup.find_all('a', {'class': 'doi'})
        doi_url = doi_sec[0].text.strip().lower()
    elif publisher == 'nature':
        doi_link = soup.find_all('a', {'data-track-action': 'view doi'})[0]
        doi_url = doi_link.text.strip().lower()
    elif publisher == 'aip':
        doi_sec = soup.find_all('div', {'class': 'publicationContentCitation'})
        doi_url = doi_sec[0].text.strip().lower()
    elif publisher == 'aaas':
        doi_sec = soup.find_all('div', {'class': 'self-citation'})
        doi_url = doi_sec[0].a.text.strip().split()[-1].strip().lower()
    else:
        raise ValueError('Unknown publisher')

    doi_url_prefix = "https://doi.org/"
    try:
        doi = doi_url[doi_url.index(doi_url_prefix) + len(doi_url_prefix):].strip()
    except ValueError:
        doi = doi_url

    return doi, publisher


def search_xml_doi_publisher(root, publisher=None):
    if not publisher:
        publisher = check_xml_publisher(root)

    if publisher == 'elsevier':
        doi_sec = list(root.iter('{http://www.elsevier.com/xml/xocs/dtd}doi'))
        doi = doi_sec[0].text.strip().lower()
    elif publisher == 'acs':
        doi_sec = list(root.iter('article-id'))
        doi = doi_sec[0].text.strip().lower()
    else:
        raise ValueError('Unknown publisher')

    return doi, publisher


def parse_html(file_path: str) -> Tuple[Article, ArticleComponentCheck]:
    """
    Parse html files

    Parameters
    ----------
    file_path: File name

    Returns
    -------
    article: Article, component check: ArticleComponentCheck
    """
    file_path = os.path.normpath(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        contents = f.read()
    soup = BeautifulSoup(contents, 'lxml')

    # get publisher and doi
    doi, publisher = search_html_doi_publisher(soup)

    if publisher in ['elsevier', 'rsc']:
        # allow illegal nested <p>
        # soup = BeautifulSoup(contents, 'html.parser')
        # allow nested <span>
        soup = BeautifulSoup(contents, 'html5lib')

    article_construct_func = getattr(ArticleFunctions, f'article_construct_html_{publisher}')
    article, component_check = article_construct_func(soup=soup, doi=doi)

    return article, component_check


def parse_xml(file_path: str) -> Tuple[Article, ArticleComponentCheck]:
    """
    Parse xml files

    Parameters
    ----------
    file_path: File name

    Returns
    -------
    article: Article, component check: ArticleComponentCheck
    """
    file_path = os.path.normpath(file_path)

    tree = ET.parse(file_path)
    root = tree.getroot()

    # get the publisher
    doi, publisher = search_xml_doi_publisher(root)

    article_construct_func = getattr(ArticleFunctions, f'article_construct_xml_{publisher}')
    article, component_check = article_construct_func(root=root, doi=doi)

    return article, component_check
