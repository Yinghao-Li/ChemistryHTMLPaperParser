__all__ = [
    "SUPPORTED_HTML_PUBLISHERS",
    "SUPPORTED_XML_PUBLISHERS",
    "CHAR_TO_HTML_LBS",
    "HTML_LBS_TO_CHAR",
    "DEFAULT_HTML_STYLE",
]

# publishers
SUPPORTED_HTML_PUBLISHERS = ["rsc", "springer", "nature", "wiley", "aip", "acs", "elsevier", "aaas"]
SUPPORTED_XML_PUBLISHERS = ["acs", "elsevier"]

# character mappings
CHAR_TO_HTML_LBS = {
    "/": "&sl;",
    "\\": "&bs;",
    "?": "&qm;",
    "*": "&st;",
    ":": "&cl;",
    "|": "&vb;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}

HTML_LBS_TO_CHAR = {
    "&sl;": "/",
    "&bs;": "\\",
    "&qm;": "?",
    "&st;": "*",
    "&cl;": ":",
    "&vb;": "|",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&amp;": "&",
}

# html style
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
