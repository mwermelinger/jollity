# Jollity Manual
Jollity is a small library of Python functions that process Jupyter notebooks.
Jollity does _not_ convert notebooks from/to other formats,
like Markdown, PDF and HTML.
There are plenty of tools for that, including [pandoc](pandoc),
[nbconvert](nbconvert), [Jupytext](jupytext),
[nbsphinx](nbsphinx) and [Jupyter Book](jubook).

## Example
Let's first see an example of how Jollity is used in practice.

I'm authoring in Markdown a textbook for M269,
the algorithms and data structures module at The Open University, UK.
I wrote a Python script that:

1. processes the Markdown files
2. converts the Markdown files to Jupyter notebooks
3. processes the notebooks
4. executes the notebooks with nbconvert
5. converts the notebooks to PDF and HTML with nbsphinx
6. processes the notebooks
7. zips all files into an archive for uploading to the M269 website.

Markdown cells at the end of stage 2 may look like this:
```
The best-case complexity is ø(1) and the worst-case complexity is ø(2^n).
<!-- INFO -->
Exponential functions were introduced in [MU123](mu123).
<!-- INFO -->

**Exercise:** Explain why the worst-case is exponential.
<!-- ANSWER -->
<!-- NOTE -->
In practice the worst-case may only occur very rarely.
<!-- NOTE -->

**Exercise**: Edit the next cell to complete the sentence.
<!-- EDIT -->
The average-case complexity is ...
<!-- EDIT -->
```
This example shows the four kinds of special comments used in M269.
(You can define your own.)

- The `ANSWER` comment becomes a separate Markdown cell with text
  '_Write your answer here._' in the final notebook that goes to students,
  but nothing appears in the PDF or HTML.
- The `INFO` and `NOTE` comments are replaced with HTML code that puts the text
  in a coloured box (different colours for info and note boxes).
- The text within `EDIT` comments is put in a separate Markdown cell, so that
  students don't edit by mistake all other surrounding text.

The example also shows the use of special characters or character combinations
to make typing the text faster. The script uses Jollity to replace all
occurrences of ø with Θ and of ^ followed by n with ^n.
The ø letter is quick to type on my keyboard (Alt-o), but there's no
shortcut for uppercase theta.

The script also replaces occurrences of `mu123` within a link
with the corresponding URL. Keeping a mapping of abbreviations to URLs
avoids repeatedly writing and updating the same URL in several notebooks.

Code cells often include `%timeit` commands to measure the run-time of code.
This slows down the execution of the code cells in stage 4, so the script
can be run in a 'draft' mode that comments out the `%timeit` commands  
before the notebooks are executed.

Stage 3 uses Jollity to:

- Put the four special comments into their own Markdown cells.
- Add HTML code at the start and end of the info and note cells
  to generate the boxes.
- Strip spaces and newlines from the start and end of each cell.
- Do text replacements to obtain special characters like superscripts.
- Replace `_text_` with `*text*` in certain contexts to avoid a Jupyter bug when
  rendering italicised text.
- Replace one or more spaces between certain words and digits with a single
  non-breaking space, e.g. `step 1.2 takes 45 µs` becomes `step&nbsp;1.2 takes 45&nbsp;µs`.
- Expand abbreviated URLs and check all URLs lead to existing pages.
- Comment out all timing lines in code cells, if in draft mode.
- Report code lines longer than 69 characters: they wrap around in the PDF.
- Report invisible line breaks in Markdown.
- Report when a heading level is skipped.
- Remove all code between `# skip` and `# \skip`,
  as illustrated in the [README](../README.md).
- If the notebook is the start of a chapter, add at the end a reminder to
  check the M269 website for news and errata before working through the chapter.

Stage 6 (after execution and conversion to PDF and HTML) uses Jollity to:

- Convert the Markdown syntax within the info and note boxes to HTML.
  Nbsphinx correctly converts the boxes' Markdown content to PDF and HTML, but
  the Jupyter interface can't render Markdown within HTML.
- Insert the boilerplate text in the empty `ANSWER` cells.
- If a notebook has code, extract it to a separate file, with a copyright
  notice before the code. Comment out all IPython commands with `%`.

File `m269.py` has the code that calls Jollity to do all the above.
The Jollity functions are explained below.

## Using Jollity
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
    if 'introduction' in file:          # pre-process chapter introductions
        jollity.one_function(notebook)
    jollity.another_function(notebook)  # same processing for all notebooks
    nbformat.write(notebook, file)      # overwrites the original file
```
In most authoring workflows you will wish to preserve the original
and write the processed notebook to a different file or folder.

For an alternative way of going through files in a folder,
see script `generate_doc.py`.
It reads the source Markdown file of this manual in folder `md`
and writes the notebook to folder `doc`.
The script uses [Jupytext](https://jupytext.readthedocs.io) to convert
a Markdown file to a Jupyter notebook.
<!-- NOTE -->
Jollity requires Python 3.8 or later.
<!-- NOTE -->

### Logging
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
Jollity doesn't include a full Markdown parser. It only assumes the following:

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

### Cell kinds
Jollity must first divide Markdown cells into particular kinds:
headings, text, fenced blocks and special HTML comments.
The kind of each cell is stored in the notebook. This allows processing steps
to only handle some cells, e.g. check the levels of headings and
ignore all other kinds of cells.

An HTML comment is special if it consists of a single word indicated by you.
The word is also used to record the kind of comment.
Jollity does a case-insensitive matching when looking for special comments, e.g.
the word `answer` will match comments `<!-- ANSWER -->`, `<!-- Answer -->`, etc.

You will have to define functions that process special comments.
For example, you can have a special comment `<!-- ANSWER -->` that leads to
a Markdown cell with text
<!-- ANSWER -->
in the published notebooks, but nothing in the PDF and HTML versions.

You can have block comments that start and end with the same one-line comment.
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

If you define `answer` as a single-line comment and `hint` as a block comment,
then Jollity will split Markdown cell
```
## Exercise
What can't Jollity do?
<!-- Answer: convert formats -->
<!-- ANSWER -->
<!-- HINT -->
Read again the start of this manual.
<!-- HINT -->
```
into four Markdown cells:

1. A cell of kind `md:head` with the heading (first line).
2. A cell of kind `md:text` with the second and third lines.
3. An empty cell of kind `md:answer`.
4. A cell of kind `md:hint` with the sixth line.

Fenced blocks are put in cells of kind `md:fence`.
Fenced blocks are rendered verbatim so you may wish to not process them further.

All Markdown cells are of kind `markdown`.
The other kinds of cells are `code` and `raw`.

Most of Jollity's functions have an argument to indicate which kinds of cells
should be processed. If the argument is `all`, every cell is processed.

The rest of this manual explains the available functions.

## Setup
```py
split_md(nb, line_comments:list, block_comments:list)
```
This function is usually called first. The arguments are lists of strings.
Every single-line or block comment consisting of one of those strings is
replaced with a Markdown cell of the kind given by the string.
For a single-line comment, the resulting cell is empty; for a block comment,
the cell has the content between the start and end of the block.

The example above is obtained by calling `split_md(nb, ['answer'], ['hint'])`.

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
'The latest version of this notebook is [here](http://....)'.
```py
prepend(nb, text:str, kind:str='')
```
If `kind` is omitted, the function inserts text at the start of the first
cell in the notebook, whether it's a raw, code or Markdown cell.
The text is inserted as-is, i.e. you must include any separator (e.g. a newline)
from the existing text, if you need to.

If kind is given, a new cell of that kind, with the given text,
is inserted at the start of the notebook.
If `kind='md:head'`, the function checks the text is a valid heading.
No checks are done for other Markdown kinds. For example,
if `kind='md:fence'`, the `text` must include the necessary backticks or tildes.

```py
append(nb, text:str, kind:str='')
```
This function works like `prepend` but inserts the text at the end of
the last cell or creates a new last cell with the text.

## Check notebook
The following functions don't modify a notebook: they only log potential issues.
Most functions take as argument the kinds of cells to be analysed.
You can indicate several kinds, separated by spaces.
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
Usually this function is called with `kinds='code md:fence'`, as lines in
other kinds of cells simply wrap around at the window edge.
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
replaces `label` with `URL` if `label:URL` occurs in the `url` dictionary.
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

For example,
```py
replace_char(nb, 'all', ('ø·', 'Θ×'))
```
replaces in all cells ø (Alt-o on my keyboard) with
uppercase Theta (which has no keyboard shortcut) and · (Alt-Shift-9) with ×.

Jollity replaces all occurrences of the old character with the new character,
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

You can see examples of the above in file `generate_doc.py`.
If you don't know how to write
[regular expressions](https://docs.python.org/3/howto/regex.html) in Python,
you should learn to: they are very powerful and useful.

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
- `remove_cells(nb, 'all', r'^$')` removes all empty cells.

```py
set_cells(nb, kinds:str, edit:bool, delete:bool)
```
This function sets all cells of the given kinds to be editable and/or deletable.
Jupyter interfaces usually don't allow users to delete cells
that can't be edited. Users can still unlock cells for editing and deletion,
but they can't do it accidentally.

If you omit the argument, the cell's status isn't changed:

- `set_cells(nb, 'all', delete=False)` prevents all cells from deletion
  but leaves their editable status unchanged
- `set_cells(nb, 'code raw', edit=True, delete=False)` makes all code and raw
  cells editable but not deletable. The status of Markdown cells isn't modified.

```py
remove_metadata(nb, kinds:str)
```
This function removes all Jollity metadata from the cells of the given kinds.
This loses information about the different kinds of Markdown cells.
For example, after calling this function with `kinds='md:head'`
Jollity won't be able to distinguish heading cells and process them separately.
This function is usually called last.
