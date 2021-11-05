"""generate_doc - generate Jollity's documentation"""

from glob import iglob
import jupytext
import os
import shutil

def generate_nb(source: str, target: str):
    """Generate target notebook from source Markdown. Ignore other files."""
    if source.endswith('.md'):
        nb = jupytext.read(source)
        path, _ = os.path.splitext(target)      # discard .md extension
        jupytext.write(nb, path + '.ipynb')

shutil.rmtree('doc/')
shutil.copytree('md/', 'doc/', copy_function=generate_nb)
