SUPPORTED_HTML_PUBLISHERS = ['rsc', 'springer', 'nature', 'wiley', 'aip', 'acs', 'elsevier', 'aaas']
SUPPORTED_XML_PUBLISHERS = ['acs', 'elsevier']

CHAR_TO_HTML_LBS = {
    '/': '&sl;',
    '\\': '&bs;',
    '?': '&qm;',
    '*': '&st;',
    ':': '&cl;',
    '|': '&vb;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&apos;'
}

HTML_LBS_TO_CHAR = {
    '&sl;': '/',
    '&bs;': '\\',
    '&qm;': '?',
    '&st;': '*',
    '&cl;': ':',
    '&vb;': '|',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&apos;': '\'',
    '&amp;': '&'
}
