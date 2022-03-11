import functools
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union, List, Tuple

from .table import Table
from .paragraph import Paragraph, Sentence

logger = logging.getLogger(__name__)


class ArticleElementType(Enum):
    SECTION_ID = 1
    SECTION_TITLE = 2
    PARAGRAPH = 3
    TABLE = 4


@dataclass
class ArticleElement:
    type: ArticleElementType
    content: Union[Paragraph, Table, str]

    def __post_init__(self):
        if self.type == ArticleElementType.PARAGRAPH and isinstance(self.content, str):
            # if len(self.content) == 0:
            #     logger.warning("Encountered empty content!")
            self.content = Paragraph(text=self.content)


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
