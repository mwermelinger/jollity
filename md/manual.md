# Jollity User Manual

Jollity is a small library of functions that process Jupyter notebooks.
They can:

- Remove HTML comments from Markdown cells.
- Prevent cells from being deleted or edited.
- Replace a mnemonic label with an URL.

Jollity does _not_ convert notebooks from/to other formats,
like Markdown, PDF and HTML.
There are plenty of tools for that, including [pandoc](pandoc),
[nbconvert](nbconvert), [Jupytext](jupytext),
[nbsphinx](nbsphinx) and [Jupyter Book](jubook).

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

## Remove comments
When authoring, you may wish to keep notes, ideas, draft paragraphs,
alternative exercise solutions, to-do reminders and similar kinds of text
in the notebook, where it's relevant, rather than in a separate document.
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

This function is usually called before the others.
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

## Add non-breaking spaces
Text like 'Part 1' and '23 kg' should use non-breaking spaces.
Jollity can automatically insert them.
```py
add_nbsp(nb, before:str, after:str)
```
This function goes through the Markdown cells of notebook `nb` and
replaces one or more spaces between a word and a digit
with a single non-breaking space (`&nbsp;`).
Arguments `before` and `after` must be Python
[regular expressions](https://docs.python.org/3/library/re.html).
They indicate which words come respectively before and after a number for
a non-breaking space to be inserted. For example,
`add_nbsp(nb, r'Unit|[Cc]ell', r'kg|m')` replaces the space before/after
the digit in 'Unit 1', 'cell 4', '5 kg, '3.25 metres', '2 ms' (milliseconds),
'6 marble columns', but not in 'unit 1', '5 cells', '3 KG', '3 and 5'.
This function replaces spaces, it doesn't create them:
it won't insert a non-breaking space in '3kg'.

If you don't want any space before or after a digit to be replaced,
omit the corresponding argument, e.g. `add_nbsp(nb, after=r'kg')`
replaces spaces only in text like '3 kg' and nothing else.

## Expand URLs
If you use some URLs repeatedly or URLs that change regularly,
like links to the current year's course webpage, Jollity allows you to define
a dictionary of labels to URLs and use the labels in Markdown links.
Having all URLs in one place makes it easier to update them.
```py
expand_urls(nb, url:dict)
```
This function goes through all Markdown cells of notebook `nb` and,
for each link `[text](label)` where `label` doesn't start with 'http',
replaces `label` with `URL` if
the pair `label:URL` occurs in the `url` dictionary.
For example, `expand_urls(nb, {'ou':'https://open.ac.uk'})` replaces
`[Open University](ou)` with `[Open University](https://open.ac.uk)`.
```
WARNING:Unknown link label:...
```
This message indicates that `...` occurs in a link but not in the dictionary.
The example above generates this message because `ou` is not in the dictionary
created by `generate_doc.py`.

## Replace text
To save time typing boilerplate text or special characters (1/4, =>, ·, etc.),
you can define a map of abbreviations to their corresponding expansions.
```py
replace_text(nb, map:dict, code:bool)
```
This function does the replacements indicated in `map` in all Markdown
and code cells (if `code` is true) of notebook `nb`.

The dictionary maps strings to strings, e.g.
`{'etc': 'and so on', '(c)': '©', 'ø': 'Θ', '1/3': '⅓'}`.
I use the mapping of ø to Θ in my book on algorithms.
It's an example of mapping quick-to-type characters (Alt-o produces ø on my
keyboard) to characters without a shortcut (here, uppercase Theta).

Jollity defines two dictionaries:

- `POWERS` maps ^ followed by i, n, 0, ..., 9 to the corresponding superscripts
  ^i, ^n, ^0, ..., ^9. To avoid making these replacements in LaTeX maths,
  put braces around the exponent, e.g. ^{i}.
- `FRACTIONS` maps 1/2, ..., 1/10, 2/3, 3/4 to ½, ..., ⅒, ⅔, ¾.

## (Un)Lock cells
Jupyter notebook cells can be locked against accidental deletion or change.
If users want to edit or delete a locked cell, they have to unlock it first.
A compliant Jupyter notebook interface won't allow users to delete cells
that can't be edited.

Jollity can lock or unlock cells of certain types for editing and/or deletion.
```py
set_cells(nb, types:str, edit:bool, delete:bool)
```
This function sets all cells of the given types to be editable and/or deletable.
If you omit the argument, the cell's status isn't changed.
This is useful if you for example only want some text cells do be editable.

Argument `types` is a string with one or more of `markdown`, `code` and `raw`.
If all cells should be set, use the string `'all'`.

For example, `set_cells(nb, 'all', delete=False)` prevents all cells from being
deleted but leaves their editable status unchanged. The call
`set_cells(nb, 'code raw', edit=True, delete=False)` makes all
code and raw cells editable but not deletable.
The status of Markdown cells is not modified.
