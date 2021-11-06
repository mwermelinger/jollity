"""jollity - a library of Jupyter notebook processing functions"""

from logging import warning
from nbformat import NotebookNode
import nbformat
import re

# maps for function `replace-text`
POWERS = {  '^0':'⁰', '^1':'¹', '^2':'²', '^3':'³', '^4':'⁴', '^5':'⁵',
            '^6':'⁶', '^7':'⁷', '^8':'⁸', '^9':'⁹', '^n':'ⁿ', '^i':'ⁱ'}
FRACTIONS = {'1/2': '½', '1/3': '⅓', '1/4': '¼', '1/5': '⅕', '1/6': '⅙',
             '1/7': '⅐', '1/8': '⅛', '1/9': '⅑', '1/10': '⅒',
             '2/3': '⅔', '3/4': '¾'}

def remove_comments(nb: NotebookNode) -> None:
    """Remove HTML comments from Markdown cells."""
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            lines = []
            comment = False
            for line in cell.source.split('\n'):
                if re.match(' ? ? ?<!--', line):
                    comment = True
                if not comment:
                    lines.append(line)
                if '-->' in line:
                    if not comment:
                        warning(f'Spurious end of comment:{line}')
                    else:
                        comment = False
                        match = re.search(r'-->(.+)$', line)
                        if match:
                            warning(f'Text after comment:{match.group(1)}')
            cell.source = '\n'.join(lines)

def add_nbsp(nb, before:str='', after:str='') -> None:
    """Replace spaces between numbers and words with a non-breaking space."""
    BEFORE = re.compile(fr'({before}) +(\d)')
    AFTER = re.compile(fr'(\d) +({after})')
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            if before:
                cell.source = BEFORE.sub(r'\1&nbsp;\2', cell.source)
            if after:
                cell.source = AFTER.sub(r'\1&nbsp;\2', cell.source)

def expand_urls(nb, url:dict) -> None:
    """Replace labels with URLs in Markdown links."""
    def get_url(match) -> str:
        label = match.group(1)
        if label in url:
            return '](' + url[label] + ')'
        else:
            warning(f'Unknown link label:{label}')
            return match.group(0)   # don't change link

    # match ](...) but not ](http...)
    URL = re.compile(r'\]\((?!http)([^\)]+)\)')
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            cell.source = URL.sub(get_url, cell.source)

def replace_text(nb, map:dict, code:bool) -> None:
    """Apply the replacements in the dictionary."""
    char = dict()   # maps characters to replacement strings
    text = dict()   # maps strings to strings
    for key, value in map.items():
        if len(key) == 1:
            char[key] = value
        else:
            text[key] = value
    CHARS = str.maketrans(char)

    for cell in nb.cells:
        if cell.cell_type == 'markdown' or (code and cell.cell_type == 'code'):
            cell.source = cell.source.translate(CHARS)
            for abbrv, expansion in text.items():
                cell.source = cell.source.replace(abbrv, expansion)

def set_cells(nb, types:str='all', edit=None, delete=None) -> None:
    """Lock or unlock the given types of cells for editing or deletion."""
    if 'all' in types:
        types = 'markdown code raw'
    for cell in nb.cells:
        if cell.cell_type in types:
            if edit is not None:
                cell.metadata.editable = edit
            if delete is not None:
                cell.metadata.deletable = delete
