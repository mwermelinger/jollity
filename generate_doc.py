"""generate_doc - generate Jollity's documentation"""

from jollity import *
import jupytext
import logging
import os
import shutil

def generate_nb(source: str, target: str):
    """Generate target notebook from source Markdown. Ignore other files."""
    if source.endswith('.md'):
        # Convert Markdown to Jupyter notebook
        nb = jupytext.read(source)

        # check for long lines before processing
        # shorter lines ease spotting differences between versions
        check_lengths(nb, 'all', 80)

        # split Markdown cells into headings, fenced blocks,
        # ANSWER and NOTE comments, and remaining text
        split_md(nb, ['answer'], ['note'])

        # remove HTML comments from text cells
        replace_re(nb, 'md:text', (COMMENT, ''))

        # remove spaces without changing indentation of first line of each cell
        replace_re(nb, 'all', [
            # (?m) turns on multi-line mode: ^ matches start of each line
            # \s matches a space, tab or newline
            (r'(?m)^\s*\n', '\n'),  # replace several blank lines with one only
            (r'^\n', ''),           # remove initial blank line
            (r'\s+$', ''),          # remove trailing white space
        ])

        # report invisible line breaks and make them explicit
        check_breaks(nb, 'md:text md:note')
        replace_re(nb, 'md:text md:note', (r' {2,}\n', r'\\\n'))

        # add HTML at start/end of a note to make the coloured box
        replace_re(nb, 'md:note', [
            (r'^(.)', r'<div class="alert alert-warning">\n\1'),
            (r'(.)$', r'\1\n</div>')
        ])

        # insert text in empty answer cells
        replace_re(nb, 'md:answer', ('', '_Write your answer here._'))

        # Jupyter doesn't render italics within underscores in some contexts
        replace_re(nb, 'md:text md:head md:note',
            # replace _text_ with *text* within []
            (r'\[_([A-Za-z0-9 ]+)_\]', r'[*\1*]')
        )

        # add non-breaking spaces as in the manual's example
        # this would also replace spaces in 'fact 5', 'pact 0', '2 heroes', etc.
        BEFORE = r'act'
        AFTER = r'h'
        replace_re(nb, 'md:text', [
            # uncomment next two lines to test
            # (fr'(?i)({BEFORE}) +(\d)', r'\1&nbsp;\2'), # (?i) ignores the case
            # (fr'(?i)(\d) +({AFTER})',  r'\1&nbsp;\2'),
        ])

        # expand abbreviated URLs and then check all of them
        expand_urls(nb, 'md:text', {
            'jupytext': 'https://jupytext.readthedocs.io',
            'pandoc': 'https://pandoc.org',
            'nbconvert': 'https://nbconvert.readthedocs.io',
            'nbsphinx': 'https://nbsphinx.readthedocs.io',
            'jubook': 'https://jupyterbook.org',
        })
        check_urls(nb, 'md:text')

        replace_char(nb, 'md:text', ('Ø', 'O'))
        replace_str(nb, 'all', POWERS)
        replace_str(nb, 'markdown', [
            ('1/4', '¼'), ('=>', '⇒'), ('e.g.', 'for example')
        ])

        # remove empty cells
        remove_cells(nb, 'all', r'^$')
        # prevent deletion of all Markdown cells
        set_cells(nb, 'markdown', edit=True, delete=False)

        # final checks after all the processing
        check_levels(nb)
        check_lengths(nb, 'md:fence code', 70)

        name, extension = os.path.splitext(target)
        # write code to separate file: this requires recognising md:head
        with open(name + '.py', 'w') as f:
            f.write(extract_code(nb))
        remove_metadata(nb, 'all')              # remove traces of Jollity
        jupytext.write(nb, name + '.ipynb')     # finally write notebook to file


logging.basicConfig(
    format='%(levelname)s %(message)s',
    # to show messages on the screen, comment the next line
    filename='log.txt', filemode='w',
)
# running this script regenerates doc folder from scratch
shutil.rmtree('doc/')
shutil.copytree('md/', 'doc/', copy_function=generate_nb)
print('See the log.txt file for errors and warnings.')
