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

- RSC (HTML, w/ table)
- Springer (HTML, w/ table)
- Nature (HTML, w/o table)
- Wiley (HTML, w/ table)
- AIP (HTML, w/o table)
- ACS (HTML & XML, w/ table)
- Elsevier (HTML & XML, w/ table)
- AAAS (Science) (HTML, w/o table)

Figure parsing currently is not supported

## Example

Fork this repo and clone it to your local machine;

To parse HTML files, run the following code:
```shell
python parse_articles.py --input_dir </path/to/html/files> --parse_html
```

Add `--parse_xml` to the argument list to enable xml parsing.

## Issues

Due to the variety of HTML/XML documents, not all document can be successfully parsed.
It would be helpful for our improvement if you can report the failed cases in the Issue section. 
