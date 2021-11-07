"""jollity - a library of Jupyter notebook processing functions"""

from logging import warning
from nbformat import NotebookNode
import math
import nbformat
import nbformat.v4 as nb4
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

def replace_regexp(nb: NotebookNode, replace:list) -> None:
    """Apply the replacements to Markdown cells.

    `replace` is a list of pairs of regular expressions (old, new)
    """
    # do one substitution at a time to use cached compiled regexp
    for old, new in replace:
        for cell in nb.cells:
            if cell.cell_type == 'markdown':
                cell.source = re.sub(old, new, cell.source)

def remove_comments(nb: NotebookNode, special:str) -> None:
    """Remove non-special HTML comments from Markdown cells."""
    # (?m) turns on re.MULTILINE so that ^ matches at the start of each line
    # (?s) turns on re.DOTALL so that .* matches newlines too
    # .*? is a non-greedy match so that it stops at the first -->
    # (?!re) matches if regular expression re does not match
    COMMENT = r'(?ms)^ ? ? ?<!-- *(?!' + special + ').*?-->\n?'
    replace_regexp(nb, [(COMMENT, '')])

def add_nbsp(nb, before:str='', after:str='') -> None:
    """Replace spaces between numbers and words with a non-breaking space."""
    replacements = []
    if before:
        replacements.append( (fr'({before}) +(\d)', r'\1&nbsp;\2') )
    if after:
        replacements.append( (fr'(\d) +({after})', r'\1&nbsp;\2') )
    replace_regexp(nb, replacements)

def fix_italics(nb: NotebookNode) -> None:
    """Avoid a Jupyter bug in italics with underscores."""
    replace_regexp(nb, [
        # replace _text_ with *text* inside [] or || or :] (slice)
        (r'([\[│:])_([A-Za-z0-9 ]+)_([\]│])', r'\1*\2*\3'),
        # replace _text_ with *text* before exponents
        (r'_([A-Za-z0-9 ]+)_([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ])', r'*\1*\2')
    ])

def extract_headers(nb: NotebookNode) -> None:
    """Put each ATX header in its own cell. The existing metadata is lost."""
    cells = []
    previous_level = math.inf
    for cell in nb.cells:
        if cell.cell_type != 'markdown':
            cells.append(cell)
        else:
            lines = []
            code = False
            for line in cell.source.split('\n'):
                if line.startswith('```'):
                    code = not code
                header = re.match(r'(#+) *(.+)', line)
                if header and not code:
                    if lines:
                        cells.append(nb4.new_markdown_cell('\n'.join(lines)))

                    cell = nb4.new_markdown_cell(line)
                    this_level = len(header.group(1))
                    cell.metadata.jollity = {
                        'header': header.group(2),
                        'level': this_level
                    }
                    cells.append(cell)
                    if this_level - previous_level > 1:
                        warning(f'Skipped heading level:{line}')
                    previous_level = this_level

                    lines = []          # start new cell
                else:
                    lines.append(line)

            if lines:
                cells.append(nb4.new_markdown_cell('\n'.join(lines)))
    nb.cells = cells

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
