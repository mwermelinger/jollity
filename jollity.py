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
COMMENT = r'(?ms)^ {0,3}<!--.*?-->'

def split_md(nb: NotebookNode, line_comments:list, block_comments:list) -> None:
    """Split markdown cells in headings, text, fenced blocks. Remove comments."""
    ATX = re.compile(r' {0,3}(#{1,6}) +(.+?)[ #]*$')
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
        previous_level = math.inf
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
                this_level = len(match.group(1))
                if this_level - previous_level > 1:
                    warning(f'Skipped heading level:{line}')
                close('head', {
                    'level': this_level,
                    'heading': match.group(2),
                })
                previous_level = this_level
                lines = []
            else:
                lines.append(line)

        close('text')
    nb.cells = cells

def _is_kind(cell, kinds:str) -> bool:
    """Internal function: Check if cell is of one of the given kinds."""
    return kinds == 'all' or cell.cell_type in kinds or (
        cell.cell_type[0] == 'm' and f'md:{cell.metadata.jollity.kind}' in kinds
        )

def _cells(nb, kinds:str) -> list:
    """Internal function: return all cells of the given kinds."""
    if kinds == 'all':      # efficiently handle the special case
        return nb.cells
    return [cell for cell in nb.cells if _is_kind(cell, kinds)]

def _replace(what:str, nb, kinds, replacements):
    """Internal auxiliary function."""
    if isinstance(replacements, tuple):
        replacements = [replacements]
    cells = _cells(nb, kinds)
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

def replace_str(nb, kinds:str, replacements) -> None:
    """Replace strings in all cells of the given kinds."""
    _replace('S', nb, kinds, replacements)

def replace_char(nb, kinds:str, replacements) -> None:
    """Replace characters in all cells of the given kinds."""
    _replace('C', nb, kinds, replacements)

def replace_re(nb, kinds:str, replacements) -> None:
    """Replace regular expressions in all cells of the given kinds."""
    _replace('R', nb, kinds, replacements)

def remove_empty(nb, kinds:str) -> None:
    """Remove all empty cells of the given kinds."""
    nb.cells = [c for c in nb.cells if c.source or not _is_kind(c, kinds)]

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
