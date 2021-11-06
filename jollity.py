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
