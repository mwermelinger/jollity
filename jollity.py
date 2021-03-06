"""jollity - a library of Jupyter notebook processing functions"""

from logging import warning, error
from nbformat import NotebookNode
import math
import nbformat
import nbformat.v4 as nb4
import re
import urllib.request

# maps for function `replace_str`
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
COMMENT = r'(?ms)^ {0,3}<!--.*?-->'

ATX = re.compile(r' {0,3}(#{1,6}) +(.+?)[ #]*$')

# Internal functions
# ------------------
# `from jollity import *` won't import functions starting with _

def _is_kind(cell, kinds:str) -> bool:
    """Internal function: Check if cell is of one of the given kinds."""
    if kinds == 'all' or cell.cell_type in kinds:
        return True
    if 'jollity' in cell.metadata:
        return f'md:{cell.metadata.jollity.kind}' in kinds
    return False

def _cells(nb, kinds:str) -> list:
    """Internal function: Return all cells of the given kinds."""
    if kinds == 'all':      # handle the special case efficiently
        return nb.cells
    return [cell for cell in nb.cells if _is_kind(cell, kinds)]

def _replace(what:str, nb, kinds, replacements):
    """Internal function: Apply replacements in all cells of the given kinds."""
    if isinstance(replacements, tuple):
        replacements = [replacements]
    cells = _cells(nb, kinds)
    # do one replacement at a time on all cells to benefit from regexp caching
    for old, new in replacements:
        if what == 'C':
            if len(old) != len(new):
                error(f'No 1-to-1 replacement for {old}')
                continue
            else:
                substitutions = str.maketrans(old, new)
        for cell in cells:
            if what == 'S':    # string substitution
                cell.source = cell.source.replace(old, new)
            elif what == 'C':  # character substitution
                cell.source = cell.source.translate(substitutions)
            else:               # regexp substitution
                cell.source = re.sub(old, new, cell.source)

# Setup
# -----
def split_md(nb: NotebookNode, line_comments:list, block_comments:list) -> None:
    """Split markdown cells in headings, text, fenced blocks. Remove comments."""
    FENCE = re.compile(r' {0,3}(`{3,}|~{3,})')
    COMMENT_START = re.compile(r' {0,3}<!--')
    # find first --> in line with non-greedy match .*?
    COMMENT_END = re.compile(r'.*?-->(.*)')

    def close(kind, extra=dict()):
        if lines:
            cell = nb4.new_markdown_cell('\n'.join(lines))
            cell.metadata = {'jollity': {'kind': kind}}
            cell.metadata.update(old_cell.metadata)
            if extra:
                cell.metadata.jollity.update(extra)
            cells.append(cell)

    cells = []
    for old_cell in nb.cells:
        if old_cell.cell_type != 'markdown':
            cells.append(old_cell)
            continue

        lines = []
        fence = ''      # the opening fence of the current fenced block
        comment = None
        for line in old_cell.source.split('\n'):
            if comment == 'normal':
                if match := COMMENT_END.match(line):
                    comment = None
                lines.append(line)
            elif comment:
                # (?i) ignores case
                if re.match(fr'(?i) ? ? ?<!--\s*{comment}\s*-->\s*$', line):
                    close(comment)
                    lines = []
                    comment = None
                else:
                    lines.append(line)
            elif fence:
                match = FENCE.match(line)
                if match and match.group(1).startswith(fence):
                    fence = ''
                    lines.append(line)
                    close('fence')
                    lines = []
                else:
                    lines.append(line)
            # line is outside comment and fenced block
            elif COMMENT_START.match(line):
                for kind in line_comments + block_comments:
                    if re.match(fr'(?i)<!--\s*{kind}\s*-->', line.strip()):
                        close('text')
                        if kind in line_comments:
                            lines = ['']
                            close(kind)
                        else:
                            comment = kind
                        lines = []
                        break
                else:   # not a special comment
                    lines.append(line)
                    if not COMMENT_END.match(line):
                        comment = 'normal'
            elif match := FENCE.match(line):
                close('text')
                fence = match.group(1)  # remember opening sequence of ` or ~
                lines = [line]
            elif match := ATX.match(line):
                close('text')
                lines = [line]
                close('head', {
                    'level': len(match.group(1)),
                    'heading': match.group(2),
                })
                lines = []
            else:
                lines.append(line)

        close('text')
    nb.cells = cells

# Header / Footer
# ---------------

def prepend(nb, text:str, kind:str=''):
    """Add text as first cell or at start of the current first cell."""
    if kind == '':
        if nb.cells:
            nb.cells[0].source = text + nb.cells[0].source
        else:
            error("Can't prepend: empty notebook")
    elif kind == 'raw':
        nb.cells.insert(0, nb4.new_raw_cell(text))
    elif kind == 'code':
        nb.cells.insert(0, nb4.new_code_cell(text))
    elif kind == 'markdown' or kind.startswith('md:'):
        cell = nb4.new_markdown_cell(text)
        if match := re.match(r'md:(.*)', kind):
            if match.group(1) == 'head':
                if heading := re.match(ATX. text.strip()):
                    cell.metadata.jollity = {
                        'kind': 'head',
                        'level': len(heading.group(1)),
                        'heading': heading.group(2)
                    }
                else:
                    error(f'Not a heading: {text}')
        nb.cells.insert(0, cell)
    else:
        error(f'Unknown kind: {kind}')

def append(nb, text:str, kind:str=''):
    """Add text as last cell or at the end of the current last cell."""
    if kind == '':
        if nb.cells:
            nb.cells[-1].source += text
        else:
            error("Can't append:empty notebook")
    elif kind == 'raw':
        nb.cells.append(nb4.new_raw_cell(text))
    elif kind == 'code':
        nb.cells.append(nb4.new_code_cell(text))
    elif kind == 'markdown' or kind.startswith('md:'):
        cell = nb4.new_markdown_cell(text)
        if match := re.match(r'md:(.*)', kind):
            if match.group(1) == 'head':
                if heading := re.match(ATX. text.strip()):
                    cell.metadata.jollity = {
                        'kind': 'head',
                        'level': len(heading.group(1)),
                        'heading': heading.group(2)
                    }
                else:
                    error(f'Not a heading: {text}')
        nb.cells.append(cell)
    else:
        error(f'Unknown kind: {kind}')

# Replace text
# ------------
def replace_str(nb, kinds:str, replacements) -> None:
    """Replace strings in all cells of the given kinds."""
    _replace('S', nb, kinds, replacements)

def replace_char(nb, kinds:str, replacements) -> None:
    """Replace characters in all cells of the given kinds."""
    _replace('C', nb, kinds, replacements)

def replace_re(nb, kinds:str, replacements) -> None:
    """Replace regular expressions in all cells of the given kinds."""
    _replace('R', nb, kinds, replacements)

def expand_urls(nb, kinds:str, url:dict):
    """Replace labels with URLs in Markdown links."""
    def get_url(match) -> str:
        label = match.group(1)
        if label in url:
            return '](' + url[label] + ')'
        else:
            # warning(f'Unknown link label: {label}')
            return match.group(0)   # don't change link

    # match ](...) but not ](http...)
    URL = re.compile(r'\]\((?!http)(.+?)\)')
    for cell in _cells(nb, kinds):
        if cell.cell_type == 'markdown':
            cell.source = URL.sub(get_url, cell.source)

# Check notebook
# --------------
def check_breaks(nb, kinds:str):
    """Check for invisible line breaks."""
    for cell in _cells(nb, kinds):
        for line in cell.source.split('\n'):
            if line.endswith('  '):
                warning(f'Invisible line break: {line}')

def check_levels(nb):
    """Check headings levels."""
    previous_level = math.inf
    for cell in _cells(nb, 'md:head'):
        this_level = cell.metadata.jollity.level
        if this_level - previous_level > 1:
            warning(f'Skipped heading level: {cell.source}')
        previous_level = this_level

def check_lengths(nb, kinds:str, length:int):
    """Check for long lines."""
    for cell in _cells(nb, kinds):
        for line in cell.source.split('\n'):
            if len(line) > length:
                    warning(f'Long line: {line}')

def check_urls(nb, kinds:str):
    """Check for broken URLs starting with http."""
    checked = set()     # check each distinct url once
    for cell in _cells(nb, kinds):
        for match in re.findall(r'\]\((http.+?)\)', cell.source):
            if not match in checked:
                checked.add(match)
                try:
                    urllib.request.urlopen(match)
                except BaseException as e:
                    error(f'Opening {match} raises {e}')

# Extract code
# ------------
def extract_code(nb, headings:bool=True) -> str:
    """Return the content of code cells and optionally the headings too."""
    lines = []
    counter = 1
    for cell in nb.cells:
        if headings and _is_kind(cell, 'md:head'):
            lines.extend(['', cell.source])     # blank line before heading
        elif cell.cell_type == 'code':
            lines.extend(['', f'# CELL {counter}', '', cell.source])
            counter += 1
    return '\n'.join(lines) if counter > 1 else ''

# Cleanup
# -------
def merge_cells(nb, kinds:str):
    """Merge consecutive cells that are of the given kinds.

    The merged cell has the same type as the first cell but the metadata of the last one! Needs to be improved. This is draft function.
    """
    cells = []
    merged = None
    for cell in nb.cells:
        if not _is_kind(cell, kinds):   # cell is not to be merged
            if merged:
                cells.append(merged)
                merged = None
            cells.append(cell)
        elif not merged:                # cell starts new merger
            merged = cell
        else:                           # merge this cell to previous ones
            merged.source += '\n' + cell.source
            merged.metadata.update(cell.metadata)
    if merged:
        cells.append(merged)
    nb.cells = cells

def set_cells(nb, kinds:str='all', edit=None, delete=None) -> None:
    """Lock or unlock the given types of cells for editing or deletion."""
    for cell in _cells(nb, kinds):
        if edit is not None:
            cell.metadata.editable = edit
        if delete is not None:
            cell.metadata.deletable = delete

def remove_cells(nb, kinds:str, text:str):
    """Remove cells of the given kinds that contain text, given as a regexp."""
    nb.cells = [cell for cell in nb.cells if not
        (_is_kind(cell, kinds) and re.search(text, cell.source))]

def remove_metadata(nb, kinds:str):
    """Remove Jollity's metadata from the cells of the given kinds."""
    if kinds == 'all':
        nb.metadata.pop('jollity', '')
    for cell in _cells(nb, kinds):
        cell.metadata.pop('jollity', '')
