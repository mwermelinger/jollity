"""generate_doc - generate Jollity's documentation"""

import jollity
import jupytext
import logging
import os
import shutil

def generate_nb(source: str, target: str):
    """Generate target notebook from source Markdown. Ignore other files."""
    if source.endswith('.md'):
        nb = jupytext.read(source)
        jollity.remove_comments(nb)
        path, _ = os.path.splitext(target)      # discard .md extension
        jupytext.write(nb, path + '.ipynb')

logging.basicConfig(
    format='%(levelname)s:%(message)s',
    # to show messages on the screen, comment the next line
    filename='log.txt', filemode='w',
)
shutil.rmtree('doc/')
shutil.copytree('md/', 'doc/', copy_function=generate_nb)
