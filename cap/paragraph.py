import copy
import logging
import functools
from typing import Optional, List, Union, Dict, Callable, Tuple
from seqlbtoolkit.eval import Metric
from collections import OrderedDict

logger = logging.getLogger(__name__)


DEFAULT_ANNO_SOURCE = '<DEFAULT>'


class Sentence:

    def __init__(
            self,
            text: str,
            start_idx: Optional[int] = None,
            end_idx: Optional[int] = None,
            anno: Optional[Union[Dict[str, Dict[Tuple[int, int], str]], Dict[Tuple[int, int], str]]] = None,
            grouped_anno: Optional[List[Metric]] = None,
            word_tokenizer: Optional[Callable] = None
    ):
        self._text = text
        self._tokens: Union[List[str], None] = None
        self._anno = anno
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.grouped_anno = grouped_anno
        self._word_tokenizer = word_tokenizer
        self._post_init()

    def _post_init(self):
        if self.start_idx is None:
            self.start_idx = 0
        self.end_idx = self.start_idx + len(self.text)
        if self._anno is None:
            self._anno = {DEFAULT_ANNO_SOURCE: dict()}
        elif isinstance(list(self._anno.keys())[0], tuple):
            self._anno = {DEFAULT_ANNO_SOURCE: self._anno}
        if self.grouped_anno is None:
            self.grouped_anno = list()
        self._tokens = self.word_tokenizer() if not self._word_tokenizer else self._word_tokenizer(self._text)

    def word_tokenizer(self, text=None) -> List[str]:
        if text is None:
            text = self._text
        from chemdataextractor.nlp.tokenize import ChemWordTokenizer
        cwt = ChemWordTokenizer()
        tokens = cwt.tokenize(text)

        return tokens

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text_: str):
        self._text = text_
        self._post_init()
        logger.warning("Text has been changed! Annotations may no longer be valid")

    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, tokens_: List[str]):
        self._tokens = tokens_
        logger.warning("Tokens have been changed! Make sure the tokens correspond to the text")

    @property
    def anno(self):
        return self._anno

    @property
    def base_anno(self):
        return self.anno[DEFAULT_ANNO_SOURCE]

    @property
    @functools.lru_cache(maxsize=None)
    def all_anno(self):
        annos = dict()
        for src, anno in self.anno.items():
            for span, v in anno.items():
                if span not in annos.keys():
                    annos[span] = v
        return annos

    @anno.setter
    def anno(self, anno_: Union[Dict[str, Dict], Dict[Tuple[int, int], str]]):
        if anno_:
            if isinstance(list(anno_.keys())[0], str):
                self._anno = anno_
            elif isinstance(list(anno_.keys())[0], tuple):
                self._anno[DEFAULT_ANNO_SOURCE] = anno_
            else:
                raise ValueError("Unknown annotation type!")
        else:
            logger.warning("Input annotation is emtpy!")
        try:
            delattr(self, 'all_anno')
        except Exception:
            pass

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def __getitem__(self, item):
        return self.tokens[item]

    def get_anno_with_value(self, value: Union[List[str], str]):
        if isinstance(value, str):
            value = [value]
        filtered_dict = dict(filter(lambda item: item[1] in value, self.all_anno.items()))
        return filtered_dict

    def remove_anno_overlaps(self):
        updated_dict = dict()
        for src in self.anno.keys():
            sorted_dict = OrderedDict(sorted(self.anno[src].items()))
            lb_span_dict = dict()
            for span, lb in sorted_dict.items():

                span_set = set(range(span[0], span[1]))
                if lb not in lb_span_dict:
                    lb_span_dict[lb] = [span_set]
                elif lb_span_dict[lb][-1] & span_set:
                    if span_set - lb_span_dict[lb][-1]:
                        lb_span_dict[lb][-1] = lb_span_dict[lb][-1] | span_set
                else:
                    lb_span_dict[lb].append(span_set)

            tmp_dict = dict()
            for lb, span_sets in lb_span_dict.items():
                for span_set in span_sets:
                    tmp_dict[min(span_set), max(span_set)+1] = lb

            updated_dict[src] = dict(OrderedDict(sorted(tmp_dict.items())))

        self.anno = updated_dict
        return self


class Paragraph:
    def __init__(self,
                 text: Optional[str] = None,
                 sentences: Optional[List["Sentence"]] = None,
                 anno: Optional[dict] = None,
                 grouped_anno: Optional[List[Metric]] = None,
                 sent_tokenizer: Optional[Callable] = None):
        self._text = text
        self._tokens: Union[List[str], None] = None

        if anno is None:
            self._anno = {DEFAULT_ANNO_SOURCE: dict()}
        elif isinstance(list(anno.keys())[0], tuple):
            self._anno = {DEFAULT_ANNO_SOURCE: anno}
        else:
            self._anno = anno

        self.sentences = sentences
        self.grouped_anno = grouped_anno if grouped_anno is not None else list()
        self.char_idx_to_sent_idx = dict()
        self._sent_tokenizer = sent_tokenizer
        self._post_init()

    def _post_init(self):
        if self.sentences is None:
            sents = self.sentence_tokenizer() if self._sent_tokenizer is None else self._sent_tokenizer(self._text)
            self.sentences = list()

            s_idx = 0
            for sent in sents:
                self.sentences.append(Sentence(sent, s_idx, s_idx+len(sent)))
                s_idx += len(sent) + 1

            self._text = ' '.join(sents)

            self.update_sentence_anno()

        else:
            assert len(self.sentences) > 0, AttributeError("Assigning empty list to `sentences` is not allowed")

            start_idx = 0
            self._text = ' ' * (self.sentences[-1].end_idx + 1)
            for sent in self.sentences:
                assert sent.end_idx > sent.start_idx >= start_idx, ValueError('Sentences are overlapping!')
                start_idx = sent.end_idx
                self._text[sent.start_idx: sent.end_idx] = sent.text

            self.update_paragraph_anno()

        self._tokens = [s.tokens for s in self.sentences]

        if not self.char_idx_to_sent_idx:
            self._set_char_idx_to_sent_idx()

    def _set_char_idx_to_sent_idx(self):
        sent_idx = 0
        for char_idx in range(len(self.text)):
            if self.sentences[sent_idx].start_idx <= char_idx < self.sentences[sent_idx].end_idx:
                self.char_idx_to_sent_idx[char_idx] = sent_idx
            elif char_idx == self.sentences[sent_idx].end_idx:
                sent_idx += 1

    def get_sentence_by_char_idx(self, char_idx: int):
        sent_idx = self.char_idx_to_sent_idx[char_idx]
        return self.sentences[sent_idx]

    # noinspection PyTypeChecker
    def sentence_tokenizer(self, text=None):
        if text is None:
            text = self._text
        from chemdataextractor.doc import Paragraph as CDEParagraph
        para = CDEParagraph(text)

        sents = list()
        for sent in para.sentences:
            sents.append(sent.text)

        return sents

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text_: str):
        self._text = text_
        self._post_init()
        logger.warning("Text has been changed! Annotations may no longer be valid")

    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, tokens_: List[str]):
        self._tokens = tokens_
        logger.warning("Tokens have been changed! Make sure the tokens correspond to the text")

    @property
    def anno(self):
        return self._anno

    @property
    def base_anno(self):
        return self.anno[DEFAULT_ANNO_SOURCE]

    @property
    @functools.lru_cache(maxsize=None)
    def all_anno(self):
        annos = dict()
        for src, anno in self.anno.items():
            for span, v in anno.items():
                if span not in annos.keys():
                    annos[span] = v
        return annos

    @anno.setter
    def anno(self, anno_: Union[Dict[str, Dict], Dict[Tuple[int, int], str]]):
        if anno_:
            if isinstance(list(anno_.keys())[0], str):
                self._anno = anno_
            elif isinstance(list(anno_.keys())[0], tuple):
                self._anno[DEFAULT_ANNO_SOURCE] = anno_
            else:
                raise ValueError("Unknown annotation type!")
        else:
            logger.warning("Input annotation is emtpy!")
        try:
            delattr(self, 'all_anno')
        except Exception:
            pass

    def align_anno(self):
        """
        Align sentence and paragraph-level annotations
        """
        self.update_sentence_anno()
        self.update_paragraph_anno()
        return self

    def update_paragraph_anno(self, sent_idx: Optional[int] = None):
        if sent_idx is None:
            for sent in self.sentences:
                for src, anno in sent.anno.items():
                    if src not in self.anno.keys():
                        self.anno[src] = dict()
                    for (s, e), v in anno.items():
                        if (s+sent.start_idx, e+sent.start_idx) not in self.anno[src]:
                            self.anno[src][(s+sent.start_idx, e+sent.start_idx)] = v
        elif isinstance(sent_idx, int):
            sent = self.sentences[sent_idx]
            for src, anno in sent.anno.items():
                if src not in self.anno.keys():
                    self.anno[src] = dict()
                for (s, e), v in anno.items():
                    if (s + sent.start_idx, e + sent.start_idx) not in self.anno[src]:
                        self.anno[src][(s + sent.start_idx, e + sent.start_idx)] = v
        else:
            raise ValueError(f'Unsupported index type: {type(sent_idx)}')

        return self

    def update_sentence_anno(self):
        if not self.char_idx_to_sent_idx:
            self._set_char_idx_to_sent_idx()

        for src, anno in self.anno.items():
            for (s, e), v in anno.items():
                sent_idx = self.char_idx_to_sent_idx[s]
                sent_s = s - self[sent_idx].start_idx
                sent_e = e - self[sent_idx].start_idx

                if src not in self[sent_idx]:
                    self[sent_idx].anno[src] = dict()

                if sent_e > self[sent_idx].end_idx:
                    logger.warning("Encountered multi-sentence annotation span. Will split.")
                    self[sent_idx].anno[src][(sent_s, self[sent_idx].end_idx)] = v
                    self[sent_idx + 1].anno[src][(0, e - self[sent_idx + 1].start_idx)] = v

                elif (sent_s, sent_e) not in self[sent_idx].anno[src]:
                    self[sent_idx].anno[src][(sent_s, sent_e)] = v
        return self

    def update_paragraph_anno_group(self, sent_idx: Optional[int] = None):
        """
        update paragraph annotation group
        """
        if sent_idx is None:
            anno_groups = list()
            for sent in self.sentences:
                if not sent.grouped_anno:
                    continue
                for anno_group in sent.grouped_anno:
                    para_anno_group = copy.deepcopy(anno_group)
                    for k in para_anno_group.keys():
                        if isinstance(para_anno_group[k], tuple) and len(para_anno_group[k]) == 2:
                            s, e = para_anno_group[k]
                            para_anno_group[k] = (s+sent.start_idx, e+sent.start_idx)
                        elif isinstance(para_anno_group[k], list) and len(para_anno_group[k]) > 0:
                            for i in range(len(para_anno_group[k])):
                                anno_pair = para_anno_group[k][i]
                                if isinstance(anno_pair, tuple) and len(anno_pair) == 2:
                                    s, e = anno_pair
                                    para_anno_group[k][i] = (s+sent.start_idx, e+sent.start_idx)
                        else:
                            pass
                    anno_groups.append(para_anno_group)
            self.grouped_anno = anno_groups

        elif isinstance(sent_idx, int):

            sent = self.sentences[sent_idx]
            if not sent.grouped_anno:
                return self
            anno_groups = list()
            for anno_group in sent.grouped_anno:
                para_anno_group = copy.deepcopy(anno_group)
                for k in para_anno_group.keys():
                    if isinstance(para_anno_group[k], tuple) and len(para_anno_group[k]) == 2:
                        s, e = para_anno_group[k]
                        para_anno_group[k] = (s+sent.start_idx, e+sent.start_idx)
                anno_groups.append(para_anno_group)

            self.grouped_anno += anno_groups
            self.grouped_anno = list(set(self.grouped_anno))

        else:
            raise ValueError(f'Unsupported index type: {type(sent_idx)}')

    def update_sentence_anno_group(self):
        raise NotImplementedError

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def __getitem__(self, item):
        return self.sentences[item]

    def get_anno_by_value(self, value: Union[List[str], str]):
        if isinstance(value, str):
            value = [value]
        filtered_dict = dict(filter(lambda item: item[1] in value, self.all_anno.items()))
        return filtered_dict

    def remove_anno_overlaps(self):
        updated_dict = dict()
        for src in self.anno.keys():
            sorted_dict = OrderedDict(sorted(self.anno[src].items()))
            lb_span_dict = dict()
            for span, lb in sorted_dict.items():

                span_set = set(range(span[0], span[1]))
                if lb not in lb_span_dict:
                    lb_span_dict[lb] = [span_set]
                elif lb_span_dict[lb][-1] & span_set:
                    if span_set - lb_span_dict[lb][-1]:
                        lb_span_dict[lb][-1] = lb_span_dict[lb][-1] | span_set
                else:
                    lb_span_dict[lb].append(span_set)

            tmp_dict = dict()
            for lb, span_sets in lb_span_dict.items():
                for span_set in span_sets:
                    tmp_dict[min(span_set), max(span_set)+1] = lb

            updated_dict[src] = dict(OrderedDict(sorted(tmp_dict.items())))

        self.anno = updated_dict
        return self
