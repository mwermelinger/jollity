"""jollity - a library of Jupyter notebook processing functions"""

from logging import warning
from nbformat import NotebookNode
import nbformat
import re

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
    def get_url(match):
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
