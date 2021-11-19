# Jollity User Manual
<!-- Save this file WITH trailing spaces to test check_breaks() -->

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

## Logging
The Jollity functions log any warnings and errors as they process notebooks.
By default, the warning and error messages are printed on the screen,
but you can collect them in a file.

If you're using a bash-like command line, you can type
`python your_script.py 2> log_file` to redirect the messages,
e.g. `python generate_doc.py 2> log.txt`.
This will overwrite the log file every time you run your script.

Alternatively, add the following to your script:
```python
import logging

logging.basicConfig(filename='log.txt')
```
This will append the messages to the file, if it exists.
In this way you can preserve the log of previous runs of your script.
If you want the log file to start afresh every time you run the script, write
```python
logging.basicConfig(filename='log.txt', filemode='w')
```

## Markdown
Jollity doesn't include a full Markdown parser. It only assumes the following.

- An HTML comment starts in a line beginning with 0–3 spaces followed by `<!--`.
- An HTML comment ends at the first occurrence of `-->`.
- A fenced block starts in a line beginning with 0–3 spaces, followed by
  3 or more backticks or by 3 or more tildes.
- A fenced block ends in a line with 0–3 spaces followed by
  at least as many backticks or tildes as it started.
- Within HTML comments, backticks and tildes don't start fenced blocks.
- Within a fenced block, the characters `<!--` don't start an HTML comment.
- A heading is a line of the form: 0–3 spaces, 1-6 hashes, 1 or more spaces,
  heading text, optional spaces and hashes.
- The end of a Markdown cell also ends any HTML comment or fenced block.

## Split Markdown
To facilitate processing, the first step is to split Markdown cells into
smaller cells of particular kinds:
headings, text, fenced blocks and special HTML comments.
The kind of each cell is stored in the notebook. This allows processing steps
to only handle some cells, e.g. only number the headings.

An HTML comment is special if it consists of a single word indicated by you.
The word is also used to record the kind of comment.
Jollity does a case-insensitive matching when looking for special comments, e.g.
the word `answer` will match comments `<!-- ANSWER -->`, `<!-- Answer -->`
and others.

You will have to define functions that process special comments.
For example, you can have a special comment `<!-- ANSWER -->` that leads to
a Markdown cell with text
<!-- ANSWER -->
in the deployed notebooks, but nothing in the PDF and HTML versions.

You can also have block comments: they start and end with the same one-line comment.
For example, with Jollity you can replace
```
<!-- NOTE -->
Jollity only processes ATX headings, not Setext headings.
<!-- NOTE -->
```
with a coloured alert box:
<!-- NOTE -->
Jollity only processes ATX headings, not Setext headings.
<!-- NOTE -->
```py
split_md(nb, line_comments:list, block_comments:list)
```
This function must be called first. The arguments are lists of strings.
Every single-line or block comment consisting of one of those strings is
replaced with a Markdown cell of the kind given by the string.
For a single-line comment, the resulting cell is empty; for a block comment,
the cell has the content between the start and end of the block.

For example,
the call `split_md(nb, ['answer'], ['hint'])` splits this Markdown text
```
## Question
Question text.
<!-- answer here -->
<!-- ANSWER -->
<!-- HINT -->
Use the same method as in the previous exercise.
<!-- HINT -->
```
into four cells:

1. A cell of kind `head` with the heading.
2. A cell of kind `text` with the second and third lines.
3. An empty cell of kind `answer`.
4. A cell of kind `hint` with the sixth line.

Fenced blocks are put in cells of kind `fence`.

<!-- When authoring, you may wish to keep notes, ideas, draft paragraphs,
alternative exercise solutions, to-do reminders and similar kinds of text
in the notebook, where it's relevant, rather than in a separate document.
You can write such text within HTML comments,
so that it isn't rendered in the notebook.
However, readers will see the comments if they edit the cells.
Jollity can remove them before you deliver the notebooks to your audience. -->

<!-- single-line comment -->
  <!--
  multi-line comment
  indented by two spaces
  --><!-- This comment is kept. -->

## Header / Footer
The next two functions add boilerplate text at the start or end of a notebook,
like a copyright notice or
'The latest version of this notebook is [here](some url)'.
```py
prepend(nb, text:str, kind:str='')
```
If `kind` is omitted, this function inserts text at the start of the first
cell in the notebook, whether it's a raw, code or Markdown cell.
The text is inserted as-is, i.e. you must include any separator (e.g. a newline)
from the existing text, if you need to.

If kind is given, a new cell of that kind, with the given text,
is inserted at the start of the notebook.
If `kind='md:head'`, the function checks the text is a valid heading.
No checks are done for other Markdown kinds.

```py
append(nb, text:str, kind:str='')
```
This function works like `prepend` but inserts the text at the end of
the last cell or creates a new last cell with the text.

## Check notebook
The following functions don't modify a notebook: they only log potential issues.
Most functions take as argument the kinds of cells to be analysed.
```py
check_breaks(nb, kinds:str)
```
This function reports all lines ending in two or more spaces:
they represent a line break in Markdown.
Usually this function is called with `kinds='md:text'`.
```py
check_levels(nb)
```
This reports any heading that is more than one level below its previous heading.
```py
check_lengths(nb, kinds:str, length:int)
```
This reports any line longer than the given length.
Usually this function is called on `code` and `md:fence` cells, as other lines
simply wrap around at the window edge.
```py
check_urls(nb, kinds:str)
```
This reports any links of the form `](http...)` that can't be opened,
e.g. because they raise a 404 error.

#### Test checks
<!-- Must keep 3 spaces at end of next line! -->
This heading (level 4) comes after a level 2 heading, and this sentence   
has an invisible line break, so the log has two messages.

## Expand URLs
If you use some URLs repeatedly or URLs that change every year,
like a link to the course webpage, Jollity allows you to define
a dictionary of labels to URLs and use the labels in Markdown links.
Having all URLs in one place makes it easier to update them.
```py
expand_urls(nb, kinds:str, url:dict)
```
This function goes through the cells of the given kinds and,
for each link `...](label)` where `label` doesn't start with 'http',
replaces `label` with `URL` if
the pair `label:URL` occurs in the `url` dictionary.
For example, `expand_urls(nb, {'ou':'https://www.open.ac.uk'})` replaces
`[Øpen University](ou)` with `[Øpen University](https://www.open.ac.uk)`.

<!-- ```
WARNING:Unknown link label:...
```
This message indicates that `...` occurs in a link but not in the dictionary.
The paragraph above generates two messages because neither `ou` nor `label`
are in the dictionary created by `generate_doc.py`. -->

## Replace text
Jollity provides three functions to replace text.
They can be used for various purposes.

Each function accepts a string with the kinds of cells to be processed:
`all` for all cells; `code`, `raw` and `markdown` for all cells of that kind;
`md:text`, `md:fence`, `md:head`, etc. for only certain kinds of Markdown cells.

Each function takes a list of (old, new) string pairs, or a single pair.
The function applies the replacements, in the order given,
to all cells of the given kinds.

### Replace characters
If you frequently need to type special characters for which there's no keyboard
shortcut, you can tell Jollity which quick-to-type characters should be
replaced with those special characters.
```py
replace_char(nb, kinds:str, replacements:list)
```
This function usually only takes a single (old, new) string pair.
Both strings must be of the same length:
the n-th character in old is replaced with the n-th character in new.
If the strings differ in length, there's an error message
and no replacement is done.

For example, for my algorithms book I do
```py
replace_char(nb, 'markdown code', ('ø·', 'Θ×'))
```
This replaces in all code and markdown cells ø (Alt-o on my keyboard) with
uppercase Theta (which has no keyboard shortcut) and · (Alt-Shift-9) with ×.

Jollity replaces all occurrences of the old character by the new character,
so make sure you don't use the old character for other purposes.
In the rare occasions I do need the dot product sign, I write it
in LaTeX: `$\cdot$`.

### Replace strings
Jollity can also replace strings with strings.
```py
replace_str(nb, kinds:str, replacements)
```
This function is like `replace_char` but the string pairs are not
interpreted as separate character by character replacements:
```py
replace_str(nb, 'markdown', [('(c)', '©'), ('etc.', 'and so on')])
```
Jollity defines two replacement lists you can pass to this function:

- `POWERS` replaces ^ followed by i, n, 0, ..., 9 with superscripts
  ^i, ^n, ^0, ..., ^9. To avoid making these replacements in LaTeX maths,
  put braces around the exponent, e.g. ^{i}.
- `FRACTIONS` replaces 1/2, ..., 1/10, 2/3, 3/4 with ½, ..., ⅒, ⅔, ¾.

### Replace regular expressions

<!-- This and previous blank line will be removed. Next spaces won't. -->
   The most powerful function replaces text that matches a regular expression.
```py
replace_re(nb, kinds:str, replacements)
```
This function is like the previous two but the strings are regular expressions.
With this function you can, among other things:

- Remove all leading or all trailing whitespace from cells.
- Replace consecutive blank lines with a single one.
- Insert text at the beginning or end of every cell of a certain kind.
- Replace spaces between certain words and digits with a non-breaking space,
  e.g. turn `Act  1 lasts 2 h` into `Act&nbsp;1 lasts 2&nbsp;h`.
- Replace `_text_` with `*text*` in some contexts, to make Jupyter render
  italics correctly, e.g. [_within square brackets_].
- Make invisible line breaks (two or more spaces at the end of a line)
  visible (with a backslash).

If you don't know how to write
[regular expressions](https://docs.python.org/3/library/re.html) in Python,
you should learn to: they are very powerful.
You can see examples of the above in file `generate_doc.py`.

Jollity defines a regular expression `COMMENTS` for HTML comments. The call
```py
jollity.replace_re(nb, 'md:text', (jollity.COMMENT, ''))
```
removes all comments from Markdown text cells, e.g.
```
This is some text. <!-- To do: needs rewriting -->
<!-- Should have a figure here -->
Next line of text.
```
becomes
```
This is some text. <!-- To do: needs rewriting -->

Next line of text.
```
because only the second comment begins after 0–3 spaces at the start of a line.

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

## Extract code
The Jupyter interface allows us to save a notebook as a code file, but it will
also include all the text, as comments.
```py
extract_code(nb, headings:bool=True) -> str
```
This function returns a string will all the code cells content and,
if the second argument is true, all the headings, to put the code in context.
If the notebook has no code cells, the returned string is empty.
This function assumes the code is in Python, R or another language where
comment lines start with `#`.

## Cleanup
These functions cleanup the notebook.
The `replace_re` function can also be used for that purpose, e.g. to
remove blank lines.
```py
remove_cells(nb, kinds:str, text:str)
```
This function removes all cells of the given kinds that include text matching
the regular expression `text`. Examples:

- `remove_cells(nb, 'md:fence', '')` removes all fenced blocks, because any text includes the empty string
- `remove_cells(nb, 'all', r'^$)` removes all empty cells.

```py
remove_metadata(nb, kinds:str)
```
This function removes all Jollity metadata from the cells of the given kinds.
This loses information about the different kinds of Markdown cells.
For example, after calling this function with `kinds='md:head'`,
any other function called with the same `kinds` won't do anything because 
Jollity won't distinguish heading cells from other Markdown cells anymore.
