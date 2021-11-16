"""generate_doc - generate Jollity's documentation"""

import jollity
import jupytext
import logging
import os
import shutil

def generate_nb(source: str, target: str):
    """Generate target notebook from source Markdown. Ignore other files."""
    if source.endswith('.md'):
        # Convert Markdown to Jupyter notebook
        nb = jupytext.read(source)

        # Process the notebook

        # split Markdown cells into headings, fenced blocks,
        # ANSWER and NOTE comments, and remaining text
        jollity.split_md(nb, ['answer'], ['note'])

        jollity.check_levels(nb)
        jollity.check_breaks(nb, 'md:text md:note')
        jollity.check_lengths(nb, 'md:text', 80)

        # remove HTML comments from text cells
        jollity.replace_re(nb, 'md:text', (jollity.COMMENT, ''))

        # remove spaces without changing indentation of first line of each cell
        jollity.replace_re(nb, 'all', [
            # (?m) turns on multi-line mode: ^ matches start of each line
            # \s matches a space, tab or newline
            (r'(?m)^\s*\n', '\n'),  # replace several blank lines with one only
            (r'^\n', ''),           # remove initial blank line
            (r'\s+$', ''),          # remove trailing white space
        ])

        # make line breaks explicit
        jollity.replace_re(nb, 'md:text', (r' {2,}\n', r'\\\n'))

        # add HTML at start/end of a note to make the coloured box
        jollity.replace_re(nb, 'md:note', [
            (r'^(.)', r'<div class="alert alert-warning">\n\1'),
            (r'(.)$', r'\1\n</div>')
        ])

        # insert text in empty answer cells
        jollity.replace_re(nb, 'md:answer', ('', '_Write your answer here._'))

        # remove any remaining empty cells
        jollity.remove_empty(nb, 'all')

        # Jupyter doesn't render italics within underscores in some contexts
        jollity.replace_re(nb, 'md:text md:head md:note',
            # replace _text_ with *text* within []
            (r'\[_([A-Za-z0-9 ]+)_\]', r'[*\1*]')
        )

        # add non-breaking spaces as in the user manual's example
        # this also replaces spaces in 'fact 5', 'pact 0', '2 heroes', etc.
        BEFORE = r'act'
        AFTER = r'h'
        jollity.replace_re(nb, 'md:text', [
            # uncomment next two lines to test
            # (fr'(?i)({BEFORE}) +(\d)', r'\1&nbsp;\2'), # (?i) ignores the case
            # (fr'(?i)(\d) +({AFTER})',  r'\1&nbsp;\2'),
        ])
        jollity.expand_urls(nb, 'md:text', {
            'jupytext': 'https://jupytext.readthedocs.io',
            'pandoc': 'https://pandoc.org',
            'nbconvert': 'https://nbconvert.readthedocs.io',
            'nbsphinx': 'https://nbsphinx.readthedocs.io',
            'jubook': 'https://jupyterbook.org',
        })
        jollity.check_urls(nb, 'md:text')

        jollity.replace_char(nb, 'md:text', ('Ø', 'O'))
        jollity.replace_str(nb, 'all', jollity.POWERS)
        jollity.replace_str(nb, 'markdown', [
            ('1/4', '¼'), ('=>', '⇒'), ('e.g.', 'for example')
        ])
        jollity.set_cells(nb, 'markdown', edit=True, delete=False)

        # Replace extension .md with .ipynb and write the file
        path, _ = os.path.splitext(target)
        jupytext.write(nb, path + '.ipynb')
        # write code to separate file
        with open(path + '.py', 'w') as f:
            f.write(jollity.extract_code(nb))

logging.basicConfig(
    format='%(levelname)s:%(message)s',
    # to show messages on the screen, comment the next line
    filename='log.txt', filemode='w',
)
shutil.rmtree('doc/')
shutil.copytree('md/', 'doc/', copy_function=generate_nb)
