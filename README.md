# Chemistry Article Parser
Convert HTML/XML Chemistry/Material Science articles into plain text.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?color=purple)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/Yinghao-Li/chemdocparsing)
---

## 1. Requirement

See `requirements.txt`.

Packages with versions specified in `requirements.txt` are used to test the code.
Other versions are not fully tested but may also work.

### Supported publishers:

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

We use the open-access ACS article [Toland et al. 2023](https://pubs.acs.org/doi/10.1021/acs.jpca.3c05870#) as an example to demonstrate the article parsing process.
The offline file is provided at `./examples/Toland.et.al.2023.html`.
For online HTML files, you can either download the html files manually and load it as demonstrated below, or use the provided `chempp.crawler.load_online_html` function (requires external dependencies).

To parse the example article, you can try the following example in your shell.
```bash
PYTHONPATH="." python examples/process_articles.py --input_dir ./examples/ --output_dir ./output/ --output_format pt
```
Notice that the `--input_dir` argument can either be the file path or a directory. If it is a directory, the program will try to read and parse all `html` and `xml` files in the folder.
`--output_format` defines the output format of the parse file.
`pt` will retain all structural information within an [`Article`]() class


## 3. Issues

Due to the variety of HTML/XML documents, not all document can be successfully parsed.
It would be helpful for our improvement if you can report the failed cases in the Issue section.

### 3.1. Known Issues

- HTML highlighting sometimes may fail when multiple entities start at the same position due to incorrect text span alignment.
- May fail to extract sections from Elsevier when section ids are `s[\d]+` instead of `sec[\d]+`, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/2).
- Fails to extract abstracts from RSC due to updated HTML format, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/1).

## Citation
