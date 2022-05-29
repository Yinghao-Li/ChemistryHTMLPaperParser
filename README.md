# Chemistry Article Parser
Convert HTML/XML Chemistry/Material Science articles into plain text.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?color=purple)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/Yinghao-Li/chemdocparsing)
---

## Requirement

See `requirements.txt`.

Packages with versions specified in `requirements.txt` are used to test the code.
Other versions are not fully tested but may also work.

## Submodule

To get the submodule files, use

```shell
git submodule update --init
```

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

## Example

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

## Issues

Due to the variety of HTML/XML documents, not all document can be successfully parsed.
It would be helpful for our improvement if you can report the failed cases in the Issue section. 
