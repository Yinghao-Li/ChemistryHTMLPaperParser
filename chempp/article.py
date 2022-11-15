import json
import pickle
import functools
import itertools
import logging
from enum import Enum
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from typing import Optional, Union, List, Tuple

from seqlbtoolkit.data import sort_tuples_by_element_idx

from .table import Table
from .figure import Figure
from .paragraph import Paragraph, Sentence
from .constants import DEFAULT_HTML_STYLE

logger = logging.getLogger(__name__)


class ArticleElementType(Enum):
    SECTION_ID = 1
    SECTION_TITLE = 2
    PARAGRAPH = 3
    TABLE = 4
    FIGURE = 5


@dataclass
class ArticleElement:
    type: ArticleElementType
    content: Union[Paragraph, Table, Figure, str]

    def __post_init__(self):
        if self.type == ArticleElementType.PARAGRAPH and isinstance(self.content, str):
            self.content = Paragraph(text=self.content)

        elif self.type == ArticleElementType.FIGURE and isinstance(self.content, Figure):
            self.content = Paragraph(text=self.content.text)


@dataclass
class ArticleComponentCheck:
    abstract: Optional[bool] = True
    sections: Optional[bool] = True


class Article:
    def __init__(self,
                 doi: Optional[str] = None,
                 publisher: Optional[str] = None,
                 title: Optional[Union[Sentence, str]] = None,
                 abstract: Optional[Union[Paragraph, str, List[str]]] = None,
                 sections: Optional[List[ArticleElement]] = None):

        self._doi = doi
        self._publisher = publisher
        self._title = title
        self._abstract = abstract
        self._sections = sections if sections else list()
        self._sec_id_to_sec = dict()
        self._post_init()

    def _post_init(self):
        if self._title and isinstance(self._title, str):
            self._title = Sentence(text=self._title)
        if self._abstract:
            if isinstance(self._abstract, str):
                self._abstract = Paragraph(self._abstract)
            elif isinstance(self._abstract, list) and isinstance(self._abstract[0], str):
                paras = list()
                for para in self._abstract:
                    para = para.strip()
                    if not para.endswith('.'):
                        para += f'.'
                    paras.append(para)
                self._abstract = Paragraph('\n'.join(paras))
        self._set_sec_id_to_sec()

    @property
    def doi(self):
        return self._doi

    @property
    def publisher(self):
        return self._publisher

    @property
    def title(self):
        return self._title

    @property
    def abstract(self):
        return self._abstract

    @property
    def sections(self):
        return self._sections

    @property
    def cont_sec_ids(self):
        return list(self._sec_id_to_sec.keys())

    @property
    def paragraphs(self):
        paras = list()
        if self.abstract:
            paras.append(self.abstract)
        for sec in self.sections:
            if sec.type == ArticleElementType.PARAGRAPH:
                paras.append(sec.content)
        return paras

    @doi.setter
    def doi(self, doi_: str):
        self._doi = doi_

    @publisher.setter
    def publisher(self, publisher_: str):
        self._publisher = publisher_

    @title.setter
    def title(self, title_: Union[str, Sentence]):
        self._title = title_ if isinstance(title_, Sentence) else Sentence(title_)
        self._set_sec_id_to_sec()

    @abstract.setter
    def abstract(self, abstract_: Union[Paragraph, str, List[str]]):
        if isinstance(abstract_, str):
            self._abstract = Paragraph(abstract_)
        elif isinstance(abstract_, list) and abstract_ and isinstance(abstract_[0], str):
            paras = list()
            for para in abstract_:
                para = para.strip()
                if not para.endswith('.'):
                    para += '.'
                paras.append(para)
            self._abstract = Paragraph(' '.join(paras))
        else:
            self._abstract = abstract_
        self._set_sec_id_to_sec()
        self.get_sentences_and_tokens.cache_clear()

    @sections.setter
    def sections(self, sections_: ArticleElement):
        self._sections = sections_
        self._clear_empty_sections()
        self._set_sec_id_to_sec()
        self.get_sentences_and_tokens.cache_clear()

    def _clear_empty_sections(self):
        new_sections = list()
        for section in self.sections:
            if section.type != ArticleElementType.PARAGRAPH:
                new_sections.append(section)
            elif section.content.text:
                new_sections.append(section)
        self._sections = new_sections

    def __getitem__(self, item: Union[str, Tuple[str, int]]):
        if isinstance(item, str):
            return self._sec_id_to_sec[item]
        elif isinstance(item, tuple):
            if item[0] == 'title':
                return self._sec_id_to_sec[item[0]]
            else:
                return self._sec_id_to_sec[item[0]][item[1]]

    def _set_sec_id_to_sec(self):
        self._sec_id_to_sec['title'] = self.title
        self._sec_id_to_sec['abs'] = self.abstract
        for i, sec in enumerate(self.sections):
            if sec.type == ArticleElementType.PARAGRAPH:
                self._sec_id_to_sec[f'sec_{i}'] = sec.content
        return self

    @functools.lru_cache()
    def get_sentences_and_tokens(self, include_title=False):
        sent_list = list()
        tokens_list = list()

        inst_ids = list()  # section id, sentence idx
        if include_title:
            sent_list.append(self.title.text)
            tokens_list.append(self.title.tokens)
            inst_ids.append(('title', 0))

        if self.abstract:
            for sent_idx, sent in enumerate(self.abstract.sentences):
                sent_list.append(sent.text)
                tokens_list.append(sent.tokens)
                inst_ids.append(('abs', sent_idx))

        for sec_idx, section in enumerate(self._sections):
            if section.type != ArticleElementType.PARAGRAPH:
                continue
            for sent_idx, sent in enumerate(section.content.sentences):
                sent_list.append(sent.text)
                tokens_list.append(sent.tokens)
                inst_ids.append((f'sec_{sec_idx}', sent_idx))  # section id, sentence idx
        return sent_list, tokens_list, inst_ids

    def save_pt(self, save_path):
        """
        Save article as pt files so that it can be loaded later

        Parameters
        ----------
        save_path: path to save file

        Returns
        -------
        self
        """
        with open(save_path, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return self

    def load_pt(self, load_path):
        """
        Load article element from pt files

        Parameters
        ----------
        load_path: path to where the pt article is saved

        Returns
        -------
        self
        """
        with open(load_path, 'rb') as handle:
            article = pickle.load(handle)
        self.doi = article.doi
        self.title = article.title
        self.publisher = article.publisher
        self.abstract = article.abstract
        self.sections = article.sections

    def save_html(self,
                  save_path,
                  html_style: Optional[str] = None,
                  tags_to_highlight: Optional[list] = None,
                  tags_to_present: Optional[list] = None):
        """
        Save article instance as HTML files

        Parameters
        ----------
        save_path: path to save the html file
        html_style: html style
        tags_to_highlight: annotation tags to be highlighted
        tags_to_present: annotation tags to present

        Returns
        -------
        self
        """

        tags_to_highlight = list() if tags_to_highlight is None else tags_to_highlight
        tags_to_present = list() if tags_to_present is None else tags_to_present

        soup = BeautifulSoup()
        head = soup.new_tag('head')
        soup.insert(0, head)
        title = soup.new_tag('title')
        head.insert(0, title)
        title.insert(0, self.title.text)

        set_html_style(head, html_style)

        viewport_meta = Tag(
            builder=soup.builder,
            name='meta',
            attrs={'name': "viewport", 'content': "width=device-width, initial-scale=1"}
        )
        head.insert(len(head), viewport_meta)

        title = soup.new_tag('h1')
        head.insert(len(head), title)
        title.insert(0, self.title.text)
        doi = soup.new_tag('p')
        head.insert(len(head), doi)
        doi.insert(0, f'doi:')
        doi_link = soup.new_tag('a', href=f'https://www.doi.org/{self.doi}')
        doi_link.insert(0, f'{self.doi}')
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

        if self.abstract:
            abs_title = soup.new_tag('h2')
            abs_div.insert(0, abs_title)
            abs_title.insert(0, 'Abstract')

            abstract = soup.new_tag('p')
            abs_div.insert(len(abs_div), abstract)
            abs_para = self.abstract
            abs_txt = abs_para.text

            for tag in tags_to_highlight:
                spans = list(abs_para.get_anno_by_value(tag).keys())
                if spans:
                    abs_txt, inst_ids = html_mark_spans(abs_txt, spans, abs_para.text, tag, f"$@${inst_idx}")
                    inst_idx += 1

                    if tag in tags_to_present:
                        for s, e in spans:
                            inst_to_present.append(abs_para.text[s: e])
                        inst_idx_list += inst_ids
            abstract.insert(len(abstract), abs_txt)

        sec_div = soup.new_tag('div', id='sections')
        body.insert(len(body), sec_div)
        for section in self.sections:

            if section.type == ArticleElementType.SECTION_TITLE:
                section_title = soup.new_tag('h2')
                sec_div.insert(len(sec_div), section_title)
                section_title.insert(0, section.content)

            elif section.type in [ArticleElementType.PARAGRAPH, ArticleElementType.FIGURE]:
                paragraph = soup.new_tag('p')
                sec_div.insert(len(sec_div), paragraph)
                para = section.content
                txt = para.text

                for tag in tags_to_highlight:
                    spans = list(para.get_anno_by_value(tag).keys())
                    if spans:
                        txt, inst_ids = html_mark_spans(txt, spans, para.text, tag, f"$@${inst_idx}")
                        inst_idx += 1

                        if tag in tags_to_present:
                            for s, e in spans:
                                inst_to_present.append(section.content.text[s: e])
                            inst_idx_list += inst_ids
                paragraph.insert(len(paragraph), txt)

            elif section.type == ArticleElementType.TABLE:
                section.content.write_html(sec_div)

        if inst_to_present:
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

        return self

    def save_jsonl(self, save_path):
        """
        Save article instance to jsonl file

        Parameters
        ----------
        save_path: where to save the file

        Returns
        -------
        self
        """
        txt_lines = ''
        doi = self.doi

        txt_lines += f"doi: {doi}\n"
        global_spans = {}

        if self.title:
            txt_lines += f"title: {self.title.text}\n\n"

        if self.abstract:
            txt_lines += f"Abstract:\n\n"
            abstract = self.abstract.text

            for (s, e), v in self.abstract.base_anno.items():
                if v not in global_spans:
                    global_spans[v] = list()
                global_spans[v].append((s + len(txt_lines),
                                        e + len(txt_lines)))
            txt_lines += f"{abstract}\n"

        if self.sections:
            for section in self.sections:

                if section.type == ArticleElementType.SECTION_TITLE:
                    txt_lines += f"\n{section.content}\n\n"

                elif section.type in [ArticleElementType.PARAGRAPH, ArticleElementType.FIGURE]:
                    para = section.content
                    for (s, e), v in para.base_anno.items():
                        if v not in global_spans:
                            global_spans[v] = list()
                        global_spans[v].append((s + len(txt_lines), e + len(txt_lines)))
                    txt_lines += f"{section.content.text}\n\n"

        txt_lines = txt_lines.rstrip()
        labels_list = list()
        for k, spans in global_spans.items():
            for span in spans:
                labels_list.append([span[0], span[1], k])

        result_dict = {
            'text': txt_lines,
            'label': labels_list,
            'doi': doi
        }
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False)
        return self


def set_html_style(root: Tag, html_style: Optional[str] = None):
    soup = BeautifulSoup()
    style = soup.new_tag('style')
    root.insert(len(root), style)
    html_style = DEFAULT_HTML_STYLE if not html_style else html_style
    style.insert(0, html_style)
    return root


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
