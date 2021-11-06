# Jollity User Manual

Jollity is a small library of functions that process Jupyter notebooks.
They can:

- Remove HTML comments from Markdown cells.
- Prevent cells from being deleted or edited.
- Replace a mnemonic label with an URL.

Jollity does _not_ convert notebooks from/to other formats.
There are plenty of tools for that.

Jollity uses the `NotebookNode` class of the `nbformat` module to
represent a notebook in memory.
Each function takes an instance of that class and modifies it.
To process your notebooks, you will need to write code like this:
```py
import glob
import jollity
import nbformat

# go through all notebooks in `folder` or a subfolder of it
for file in glob.iglob('folder/**/*.ipynb', recursive=True):
    notebook = nbformat.read(file, 4)   # 4 is the notebook format version
    jollity.one_function(notebook)
    jollity.another_function(notebook)
    nbformat.write(notebook, file)      # overwrites the original file
```
If you wish to preserve the original,
write the processed notebook to a different file or folder.

<!-- To do: Explain how to process different notebooks differently -->

For an example of how to use Jollity, see script `generate_doc.py`.
It reads the source Markdown files of this manual in folder `md`
and regenerates the notebooks in folder `doc`.
The script uses [Jupytext](https://jupytext.readthedocs.io) to convert
a Markdown file to a Jupyter notebook.

The Jollity functions log any warnings and errors as they process notebooks.
By default, the warning and error messages are printed on the screen,
but you can collect them in a file.

If you're using a bash-like command line, you can type
`python your_script.py 2> log_file` to redirect the messages,
e.g. `python generate_doc.py 2> log.txt`.
This will overwrite the log file every time you run your script.

Alternatively, add the following to your script:
```py
import logging

logging.basicConfig(filename='log.txt')
```
This will append the messages to the file, if it exists.
In this way you can preserve the log of previous runs of your script.
If you want the log file to start afresh every time you run the script, write
```py
logging.basicConfig(filename='log.txt', filemode='w')
```

## Removing comments

When authoring, you may wish to keep notes, ideas, draft paragraphs,
alternative exercise solutions, to-do reminders and similar kinds of text
in the same file, rather than in a separate document.
You can write such text within HTML comments,
so that it isn't rendered in the notebook.
However, readers will see the comments if they edit the cells.
Jollity can remove them before you deliver the notebooks to your audience.
```py
jollity.remove_comments(nb)
```
This function removes HTML comments from all Markdown cells in notebook `nb`.
It only removes comments that start with `<!--`
at the beginning of a line, preceded by at most three spaces.
The line with the first closing `-->` is also removed, i.e.
any text on the same line after the comment is discarded.
```
WARNING:Text after comment:...
```
This message warns that text `...` was deleted because it comes
after closing a comment. The Markdown source of this manual has
next an example that raises this message.
<!-- single-line comment -->
  <!--
  multi-line comment
  indented by two spaces
  --> This sentence will be deleted.
```
WARNING:Spurious end of comment:...
```
This message warns that line `...` has `-->` but no comment was open.
This may be deliberate, as in the previous sentence,
or the corresponding `<!--` isn't at the start of a line.
