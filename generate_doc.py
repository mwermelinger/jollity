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
        jollity.remove_comments(nb)
        jollity.add_nbsp(nb, before=r'Part|Unit|[Cc]ell')
        jollity.add_nbsp(nb, after=r'kg|m') # done separately for testing
        jollity.expand_urls(nb, {
            'jupytext': 'https://jupytext.readthedocs.io',
            'pandoc': 'https://pandoc.org',
            'nbconvert': 'https://nbconvert.readthedocs.io',
            'nbsphinx': 'https://nbsphinx.readthedocs.io',
            'jubook': 'https://jupyterbook.org',
        })

        # Replace extension .md with .ipynb and write the file
        path, _ = os.path.splitext(target)
        jupytext.write(nb, path + '.ipynb')

logging.basicConfig(
    format='%(levelname)s:%(message)s',
    # to show messages on the screen, comment the next line
    filename='log.txt', filemode='w',
)
shutil.rmtree('doc/')
shutil.copytree('md/', 'doc/', copy_function=generate_nb)
