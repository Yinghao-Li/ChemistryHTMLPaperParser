# Chemistry Paper Parser
Convert HTML/XML Chemistry/Material Science articles into plain text.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?color=purple)](https://www.python.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/Yinghao-Li/chemdocparsing)
[![PyPI version](https://badge.fury.io/py/ChemistryPaperParser.svg)](https://badge.fury.io/py/ChemistryPaperParser)
---

## 1. Install

### Requirements
The current version of Chemistry Paper Parser is built for `Python >= 3.9`.
Please check `requirements.txt` for other dependencies.

### Install package

Chemistry Paper Parser is hosted on [pypi](https://pypi.org/).
You can simply install it with
```bash
pip install ChemistryPaperParser
```

Once installed, you can import the package as `chempp` in `Python`:

```python
from chempp import parse_html, parse_xml

html_article, _ = parse_html(path_to_my_local_html)
xml_article, _ = parse_xml(path_to_my_local_xml)
```

### Supported publishers:

Currently, Chemistry Paper Parser supports the following publishers and file types.

| Publisher | Supports HTML | Supports XML |
|-----------|---------------|--------------|
| [RSC](https://pubs.rsc.org/) | ✓ | ✗ |
| [Springer](https://www.springer.com/us) | ✓ | ✗ |
| [Nature](https://www.nature.com/) | ✓ | ✗ |
| [Wiley](https://onlinelibrary.wiley.com/) | ✓ | ✗ |
| [AIP](https://pubs.aip.org/) | ✓ | ✗ |
| [ACS](https://pubs.acs.org/) | ✓ | ✓ |
| [Elsevier](https://www.elsevier.com/) | ✓ | ✓ |
| [AAAS (Science)](https://www.science.org/journals) | ✓ | ✗ |

In addition, table parsing is not supported for all publishers.

For figures, only captions will be parsed and saved in the current version.

## 2. Example

The open-access ACS article [Toland et al. (2023)](https://pubs.acs.org/doi/10.1021/acs.jpca.3c05870#) is used here as an example to demonstrate the article parsing process.
The offline file is provided at `./examples/Toland.et.al.2023.html`.
For online HTML files, you can either download the html files manually and load it as demonstrated below, or use the provided `chempp.crawler.load_online_html` function (requires external dependencies).

To parse the example article, you can try the following example in your shell.
```bash
PYTHONPATH="." python ./examples/process_articles.py --input_dir ./examples/ --output_dir ./output/ --output_format pt
```
The `--input_dir` argument can either be the file path or a directory. If it is a directory, the program will try to read and parse all `html` and `xml` files in the folder.
`--output_format` defines the output format of the parse file.
`pt` will retain all structural information within the [`Article`](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/blob/087cf01fb0a0b44008e3ac987ba4e77e2d9f8d3c/chempp/article/article.py#L57) class.
`jsonl` saves the file as a Doccano-compatible jsonl file for easy annotation.
`html` saves the file as a simplified HTML for easy demonstration of the annotated sentences and tokens.
It also is a good way to present the quality of the parsed article.

Notice that [`./examples/process_articles.py`](./examples/process_articles.py) is only an incomplete demonstration of `chempp` APIs and their usage.
The notebook [`./examples/example.ipynb`](./examples/example.ipynb) demonstrates the structure of the parsed `Article` object and some possible use cases.
You can find more details regarding Chemistry Article Parser and its application in my [blog](https://yinghao-li.github.io/posts/2023/07/material-ie/).
I'll provide more comprehensive API introduction if needed in the future.


## 3. Known issues

Due to the variety of HTML/XML documents, not all document can be successfully parsed.
It would be helpful for our improvement if you can report the failed cases in the Issue section.


- HTML highlighting sometimes may fail when multiple entities start at the same position due to incorrect text span alignment.
- May fail to extract sections from Elsevier when section ids are `s[\d]+` instead of `sec[\d]+`, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/2).
- Fails to extract abstracts from RSC due to updated HTML format, as mentioned in [this issue](https://github.com/Yinghao-Li/ChemistryHTMLPaperParser/issues/1).

## Citation

Please consider citing the following article if your find our package useful.
Although not mentioned at all, Chemistry Paper Parser is still a part of this project.
```
@article{toland.2023.accelerated.scheme,
  author = {Toland, Aubrey and Tran, Huan and Chen, Lihua and Li, Yinghao and Zhang, Chao and Gutekunst, Will and Ramprasad, Rampi},
  title = {Accelerated Scheme to Predict Ring-Opening Polymerization Enthalpy: Simulation-Experimental Data Fusion and Multitask Machine Learning},
  journal = {The Journal of Physical Chemistry A},
  volume = {127},
  number = {50},
  pages = {10709-10716},
  year = {2023},
  doi = {10.1021/acs.jpca.3c05870},
  note ={PMID: 38055927},
  URL = {https://doi.org/10.1021/acs.jpca.3c05870},
  eprint = {https://doi.org/10.1021/acs.jpca.3c05870}
}
```