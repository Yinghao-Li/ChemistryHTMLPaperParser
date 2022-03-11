import os
import json
import glob
import time
import itertools
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup, Tag

from seqlbtoolkit.text import substring_mapping
from seqlbtoolkit.data import sort_tuples_by_element_idx
from .article import Article, ArticleElementType
from .constants import *

try:
    import pyautogui
    import shutil
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import NoSuchElementException
except KeyError:
    pass


DEFAULT_HTML_STYLE = """
head {
  width: 85%;
  margin:auto auto;
}

body {
  width: 85%;
  margin:auto auto;
}

div {
  width: 100%;
  margin:auto auto;
}

p {
  text-align: justify;
  text-justify: inter-word;
}

.polymer {
background-color: lightblue;
color: black;
}

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


def scroll_down(driver_var, value):
    driver_var.execute_script("window.scrollBy(0," + str(value) + ")")


# Scroll down the page
def scroll_down_page(driver, n_max_try=100):

    old_page = driver.page_source
    for _ in range(n_max_try):
        for i in range(2):
            scroll_down(driver, 500)
            time.sleep(0.1)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            break
    return True


def every_downloads_chrome(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def download_article_windows(doi, download_path, driver_path=None):

    article_url = 'https://doi.org/' + doi
    driver = webdriver.Chrome(executable_path=driver_path)

    driver.get(article_url)
    scroll_down_page(driver)

    if doi.startswith('10.1039'):
        try:
            driver.find_element_by_link_text('Article HTML').click()
            scroll_down_page(driver)
        except NoSuchElementException:
            pass

    pyautogui.hotkey('ctrl', 's')

    time.sleep(1)

    file_name = substring_mapping(doi, CHAR_TO_HTML_LBS) + '.html'
    save_path = os.path.join(download_path, file_name)
    save_path = os.path.abspath(os.path.normpath(save_path))

    if os.path.isfile(save_path):
        os.remove(save_path)
    if os.path.isdir(save_path.replace('.html', '_files')):
        shutil.rmtree(save_path.replace('.html', '_files'))
    pyautogui.write(save_path)
    pyautogui.hotkey('enter')
    time.sleep(0.1)

    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.1)
    driver.switch_to.window(driver.window_handles[1])
    _ = WebDriverWait(driver, 120, 1).until(every_downloads_chrome)
    time.sleep(0.1)

    driver.quit()


def set_html_style(root: Tag, html_style: Optional[str] = None):
    soup = BeautifulSoup()
    style = soup.new_tag('style')
    root.insert(len(root), style)
    html_style = DEFAULT_HTML_STYLE if not html_style else html_style
    style.insert(0, html_style)
    return root


def save_html_results(save_path: str,
                      article: Article,
                      html_style: Optional[str] = None,
                      tags_to_highlight: Optional[list] = None,
                      tags_to_present: Optional[list] = None):
    """
    save html-formatted tables
    This function should only be called for test.

    Parameters
    ----------
    save_path: where to save the output file
    article: article where the table appears
    html_style: html style
    tags_to_highlight: annotation tags to be highlighted
    tags_to_present: annotation tags to be presented

    Returns
    -------
    None
    """

    soup = BeautifulSoup()
    head = soup.new_tag('head')
    soup.insert(0, head)
    title = soup.new_tag('title')
    head.insert(0, title)
    title.insert(0, article.title.text)

    set_html_style(head, html_style)

    viewport_meta = Tag(
        builder=soup.builder,
        name='meta',
        attrs={'name': "viewport", 'content': "width=device-width, initial-scale=1"}
    )
    head.insert(len(head), viewport_meta)

    title = soup.new_tag('h1')
    head.insert(len(head), title)
    title.insert(0, article.title.text)
    doi = soup.new_tag('p')
    head.insert(len(head), doi)
    doi.insert(0, f'doi:')
    doi_link = soup.new_tag('a', href=f'https://www.doi.org/{article.doi}')
    doi_link.insert(0, f'{article.doi}')
    doi.insert(len(doi), doi_link)

    body = soup.new_tag('body')
    soup.insert(len(soup), body)

    # save space for result sentences
    result_div = soup.new_tag('div', id='results')
    body.insert(len(body), result_div)

    body.insert(len(body), soup.new_tag('hr'))
    abs_div = soup.new_tag('div', id='abstract')
    body.insert(len(body), abs_div)

    inst_to_present = list()
    inst_idx_list = list()
    inst_idx = 0

    if article.abstract:
        abs_title = soup.new_tag('h2')
        abs_div.insert(0, abs_title)
        abs_title.insert(0, 'Abstract')

        abstract = soup.new_tag('p')
        abs_div.insert(len(abs_div), abstract)
        abs_para = article.abstract
        abs_txt = abs_para.text

        for tag in tags_to_highlight:
            spans = list(abs_para.get_anno_by_value(tag).keys())
            if spans:
                abs_txt, inst_ids = html_mark_spans(abs_txt, spans, abs_para.text, tag, f"result-{inst_idx}")
                inst_idx += 1

                if tag in tags_to_present:
                    for s, e in spans:
                        inst_to_present.append(abs_para.text[s: e])
                    inst_idx_list += inst_ids
        abstract.insert(len(abstract), abs_txt)

    sec_div = soup.new_tag('div', id='sections')
    body.insert(len(body), sec_div)
    for section in article.sections:

        if section.type == ArticleElementType.SECTION_TITLE:
            section_title = soup.new_tag('h2')
            sec_div.insert(len(sec_div), section_title)
            section_title.insert(0, section.content)

        elif section.type == ArticleElementType.PARAGRAPH:
            paragraph = soup.new_tag('p')
            sec_div.insert(len(sec_div), paragraph)
            para = section.content
            txt = para.text

            for tag in tags_to_highlight:
                spans = list(para.get_anno_by_value(tag).keys())
                if spans:
                    txt, inst_ids = html_mark_spans(txt, spans, para.text, tag, f"result-{inst_idx}")
                    inst_idx += 1

                    if tag in tags_to_present:
                        for s, e in spans:
                            inst_to_present.append(section.content.text[s: e])
                        inst_idx_list += inst_ids
            paragraph.insert(len(paragraph), txt)

        elif section.type == ArticleElementType.TABLE:
            section.content.write_html(sec_div)

    # save result sentences
    result_title = soup.new_tag('h2')
    result_div.insert(len(result_div), result_title)
    result_title.insert(0, 'results')
    result_list = soup.new_tag('ol')
    result_div.insert(len(result_div), result_list)

    for inst, idx in zip(inst_to_present, inst_idx_list):
        result_p = soup.new_tag('li')
        result_list.insert(len(result_list), result_p)
        result_p.insert(0, inst)
        result_link = soup.new_tag('a', href=f'#{idx}')
        result_p.insert(len(result_p), result_link)
        result_link.insert(0, '[link]')

    soup_str = soup.prettify().replace('&lt;', '<').replace('&gt;', '>')
    with open(save_path, 'w', encoding='utf-8') as outfile:
        outfile.write(soup_str)


def html_mark_spans(text: str,
                    spans: List[Tuple[int, int]],
                    ori_text: Optional[str] = None,
                    mark_class: Optional[str] = '',
                    mark_id: Optional[str] = ''):
    """
    Wrap entity spans with HTML marker

    Parameters
    ----------
    text: input text string
    spans: input spans
    ori_text: original text where the span is based
    mark_class: the class of mark tag
    mark_id: the id of the mark tag

    Returns
    -------
    Marked text
    """
    if ori_text:
        import textspan
        spans = [(s[0][0], s[-1][-1]) for s in textspan.align_spans(spans, ori_text, text)]
    spans = sort_tuples_by_element_idx(spans)

    merged_spans = list(itertools.chain(*spans))
    merged_spans = [0] + merged_spans + [len(text)]
    splitted_str = [text[x:y] for x, y in zip(merged_spans, merged_spans[1:])]
    i = 1
    ids = list()
    while i < len(splitted_str):
        id_str = f"{mark_id}-{i}"
        splitted_str[i] = f'<mark class={mark_class.lower()} id={id_str}>{splitted_str[i]}</mark>'
        i += 2
        ids.append(id_str)
    return ''.join(splitted_str), ids


def get_file_paths(input_dir: str):
    if os.path.isfile(input_dir):
        with open(input_dir, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
    elif os.path.isdir(input_dir):
        folder = input_dir
        file_list = list()
        for suffix in ('xml', 'html'):
            file_list += glob.glob(os.path.join(folder, f"*.{suffix}"))
    else:
        raise FileNotFoundError("Input file does not exist!")
    return file_list
