# Chemistry Article Parser
Convert HTML/XML Chemistry/Material Science articles into plain text.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?color=purple)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/Yinghao-Li/chemdocparsing)
---

## 1. Requirement

See `requirements.txt`.

Packages with versions specified in `requirements.txt` are used to test the code.
Other versions are not fully tested but may also work.

## Supported publishers:

- RSC (HTML)
- Springer (HTML)
- Nature (HTML)
- Wiley (HTML)
- AIP (HTML)
- ACS (HTML & XML)
- Elsevier (HTML & XML)
- AAAS (Science) (HTML)

Table parsing is supported but not for all publishers.
For figures, only figure captions are parsed in the current version.

## 2. Example

Fork this repo and clone it to your local machine;

To parse HTML files, run the following code:
```shell
python tests/parse_articles.py --input_dir </path/to/html/files> --parse_html
```
or
```shell
cd tests
python parse_articles.py config.json
```
where parameters are stored in file `config.json`.

Add `--parse_xml` to the argument list to enable xml parsing.

## 3. Issues

Due to the variety of HTML/XML documents, not all document can be successfully parsed.
It would be helpful for our improvement if you can report the failed cases in the Issue section.

### 3.1. Known Issues

- HTML highlighting sometimes may fail when multiple entities start at the same position due to incorrect text span alignment.
- May fail to extract sections from Elsevier when section ids are `s[\d]+` instead of `sec[\d]+`, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/2).
- Fails to extract abstracts from RSC due to updated HTML format, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/1).

