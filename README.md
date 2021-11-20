# Jollity

Jollity supports the authoring and publication of Jupyter notebooks.
You can keep an author's version of the notebooks,
e.g. with notes and to-do items in HTML comments, and use Jollity to produce
the published version of the notebooks.

Jollity is a small library of Python functions that you call from your script
to automate some tasks that are tedious or error-prone if done manually, like:

- Detect invisible line breaks (two spaces at the end of a line) and
  replace them with explicit line breaks (backslashes).
- Detect missing intermediate headings,
  e.g. a level-3 heading after a level-1 heading.
- Check if every http link can be followed, i.e. opens a page.
- Insert non-breaking spaces before or after numbers.
- Add text (e.g. a copyright notice) at the start or end of each notebook.
  This makes it easy to update the text.
- Clean up notebooks, e.g. by removing HTML comments and blank lines at
  the start and end of cells.
- Extract all code from a notebook into a separate file for
  those who can't use Jupyter for accessibility or other reasons.
- Prevent cells from being deleted or edited.

Jollity also allows you to type Markdown cells more quickly.
You can define abbreviations and have them expanded in all notebooks.
For example, if you use some URLs repeatedly throughout notebooks,
you can write text like `see the [course website](site)` and
have `site` replaced with the URL in every Markdown link.

You can define your own special HTML comments that enclose Markdown text
to be processed separately from other text. For example, you can write
```
<!-- NOTE -->
Jollity is still a work in progress.
<!-- NOTE -->
```
and use Jollity to produce
<div class="alert alert-warning">
<strong>Note:</strong> Jollity is still a work in progress.
</div>

You can also define your own special code comments for Jollity to process.
For example, you can write alternative solutions or draft code:
```py
def reverse_sequence(items: list) -> list:
    return items[::-1]
    # skip: not yet correct
    return [items[i] for i in range(len(items), 0, -1)]
    # /skip
```
and use Jollity to remove all lines from `# skip` to `# /skip`
from the published notebook.

For more details on how to use Jollity and what it can do, see the
[manual](doc/manual.ipynb).

Jollity doesn't convert notebooks to other formats,
nor does it check the code style, as there are tools for those purposes.
For more on the role of automation in publishing notebooks, see
[the guide](https://opencomputinglab.github.io/educational-jupyter-notebook-qa-automation)
by my colleague Tony Hirst.

<p xmlns:cc="http://creativecommons.org/ns#"
xmlns:dct="http://purl.org/dc/terms/">
<span property="dct:title">The text in this repository</span> is copyright
© 2021 by <span property="cc:attributionName">Michel Wermelinger</span>
and licensed under a
<a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1"
target="_blank" rel="license noopener noreferrer"
style="display:inline-block;">Creative Commons Attribution 4.0 International
<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;"
src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">
<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;"
src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1">
</a> license.</p>

The code in this repository is copyright © 2021 by Michel Wermelinger
and licensed under an [MIT License](LICENSE.txt).
