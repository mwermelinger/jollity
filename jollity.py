"""jollity - a library of Jupyter notebook processing functions"""

from logging import warning, error
from nbformat import NotebookNode
import math
import nbformat
import nbformat.v4 as nb4
import re

# maps for function `replace_text`
POWERS = list({
    '^0':'⁰', '^1':'¹', '^2':'²', '^3':'³', '^4':'⁴', '^5':'⁵',
    '^6':'⁶', '^7':'⁷', '^8':'⁸', '^9':'⁹', '^n':'ⁿ', '^i':'ⁱ'}.items())
            
FRACTIONS = list({
    '1/2': '½', '1/3': '⅓', '1/4': '¼', '1/5': '⅕', '1/6': '⅙',
    '1/7': '⅐', '1/8': '⅛', '1/9': '⅑', '1/10': '⅒',
    '2/3': '⅔', '3/4': '¾'}.items())
             
# In CommonMark, an HTML comment may be preceded by at most 3 spaces.
# (?m) turns on re.MULTILINE so that ^ matches at the start of each line
# (?s) turns on re.DOTALL so that .* matches newlines too
# .*? is a non-greedy match so that it stops at the first -->
COMMENT = r'(?ms)^ ? ? ?<!--.*?-->\n?'

def _replace(nb, kind, replacements, types):
    """Internal auxiliary function."""
    if types == 'all':
        types = 'markdown code raw'
    if isinstance(replacements, tuple):
        replacements = [replacements]
    for old, new in replacements:
        if kind == 'C':
            if len(old) != len(new):
                error(f'No 1-to-1 replacement for {old}')
                continue
            else:
                substitutions = str.maketrans(old, new)
        for cell in nb.cells:
            if cell.cell_type in types:
                if kind == 'S':    # string substitution
                    cell.source = cell.source.replace(old, new)
                elif kind == 'C':  # character substitution
                    cell.source = cell.source.translate(substitutions)
                else:               # regexp substitution
                    cell.source = re.sub(old, new, cell.source)
        
def replace_str(nb, types:str, replacements) -> None:
    """Replace strings in all matching cell types."""
    _replace(nb, 'S', replacements, types)

def replace_char(nb, types:str, replacements) -> None:
    """Replace characters in all matching cell types."""
    _replace(nb, 'C', replacements, types)
    
def replace_re(nb, types:str, replacements) -> None:
    """Replace regular expressions in all matching cell types."""
    _replace(nb, 'R', replacements, types)

def add_nbsp(nb, before:str='', after:str='') -> None:
    """Replace spaces between numbers and words with a non-breaking space."""
    if before:
        replace_re(nb, 'markdown', (fr'({before}) +(\d)', r'\1&nbsp;\2') )
    if after:
        replace_re(nb, 'markdown', (fr'(\d) +({after})', r'\1&nbsp;\2') )

def fix_italics(nb: NotebookNode) -> None:
    """Avoid a Jupyter bug in italics with underscores."""
    replace_re(nb, 'markdown', [
        # replace _text_ with *text* inside [] or || or :] (slice)
        (r'([\[│:])_([A-Za-z0-9 ]+)_([\]│])', r'\1*\2*\3'),
        # replace _text_ with *text* before exponents
        (r'_([A-Za-z0-9 ]+)_([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ])', r'*\1*\2')
    ])

def spaces(nb: NotebookNode, fix_breaks:bool) -> None:
    """Handle spaces in cells."""
    for cell in nb.cells:
        if cell.cell_type == 'markdown' and '  \n' in cell.source:
            for line in cell.source.split('\n'):
                if line.endswith('  '):
                    warning(f'Invisible line break:{line}')
            if fix_breaks:
                cell.source = re.sub(r'  +\n', r'\\\n', cell.source)

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

    
