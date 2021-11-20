"""m269.py - process M269 notebooks with Jollity

M269 is the algorithms and data structures module at The Open University, UK.

The M269 book is automatically produced by a Python script
that contains code very similar to the below.
"""

import jollity
import logging

MAXL = 69                               # log code lines longer than this
URLs = {                                # links that change yearly
    # in the script, this dictionary contains links to internal university sites
    # the next two lines just illustrate what this dictionary is for
    'm269': 'https://www.open.ac.uk/courses/modules/m269',
    'mu123': 'https://www.open.ac.uk/courses/modules/mu123',
}

# words before and after a digit requiring a non-breaking space
BEFORE = r'block|part|unit|chapter|section|index|step|length|TMA'
AFTER = r'ns|µs|ms|s|h|day|bit|byte|MB|GB'

# preamble of each extracted code file; the script contains the full notice
NOTICE = """# The code below was automatically extracted from..."""

logging.basicConfig(
    format='%(levelname)s:%(message)s',
    filename='log.txt', filemode='w',
)

def for_execution(nb, notime:bool, filename:str):
    """Process notebook nb before it's executed."""
    # separate special comments and headings into their own Markdown cells
    jollity.split_md(nb, ['answer'], ['info', 'note', 'edit'])

    # if it's the first notebook of a chapter, add a reminder at the end
    if 'introduction' in filename:
        jollity.append(nb, """\n
Before starting to work on this chapter, check the
[M269 website](m269) for relevant news and errata.""")

    # strip space from start/end of a cell
    jollity.replace_re(nb, 'all', [ (r'^\s+', ''), (r'\s+$', '') ])

    # replace ^0, ..., ^9, ^n, ^i with corresponding Unicode superscripts
    jollity.replace_str(nb, 'all', jollity.POWERS)
    # replace quick-to-type characters, one for one
    jollity.replace_char(nb, 'all', ('«»“”øØ·',
                                     '││⌊⌋Θ𝛰×'))

    # the following don't apply to code cells, to Markdown headings and
    # to fenced blocks

    # replace em-dash with minus (Unicode U+2212, HTML &minus;)
    jollity.replace_char(nb, 'md:text md:note md:info md:edit', ('—', '−'))

    jollity.replace_re(nb, 'md:text md:info md:note md:edit', [
        # avoid a Jupyter bug that doesn't render some italics text
        # replace _text_ with *text* inside [] or || or :] (slice)
        (r'([\[│:])_([A-Za-z0-9 ]+)_([\]│])', r'\1*\2*\3'),
        # replace _text_ with *text* before exponents
        (r'_([A-Za-z0-9 ]+)_([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ])', r'*\1*\2'),

        # replace one or more spaces with one non-breaking space
        (fr'(?i)({BEFORE}) +(\d)', r'\1&nbsp;\2'),  # ?i: ignore case
        (fr'(\d) +({AFTER})', r'\1&nbsp;\2'),
    ])

    # expand abbreviated URLs, then check all
    # skip headings because they don't have links in the M269 book
    jollity.expand_urls(nb, 'md:text md:note md:info md:edit', URLs)
    jollity.check_urls(nb, 'md:text md:note md:info md:edit')

    # report invisible line breaks
    jollity.check_breaks(nb, 'md:text md:note md:info md:edit')

    # the following only apply to specific Markdown cells

    # report missing heading levels
    jollity.check_levels(nb)

    # put NOTE and INFO text within alert boxes
    jollity.replace_re(nb, 'md:note', [
        (r'^(.)', r'<div class="alert alert-warning">\n**Note:** \1'),
        (r'(.)$', r'\1\n</div>')
    ])
    jollity.replace_re(nb, 'md:info', [
        (r'^(.)', r'<div class="alert alert-info">\n**Info:** \1'),
        (r'(.)$', r'\1\n</div>')
    ])

    # the following only applies to code

    if notime:      # comment out the IPython timing commands
        # ?m is multiline mode to match at start of each line
        jollity.replace_re(nb, 'code', (r'(?m)^( *)(%time)', r'\1# \2'))

    # remove code marked as to be skipped
    # ?s allows . to match newlines
    # *? is non-greedy match to stop at first /skip
    jollity.replace_re(nb, 'code', (r'(?ms)^\s*# skip.*?# /skip\n', ''))

    # report long lines
    jollity.check_lengths(nb, 'code', MAXL)

def for_distribution(nb_file, py_file):
    """Process notebook before it's put on the website."""
    with open(nb_file, 'r') as file:
        nb = nbformat.read(file, 4)

    if code := jollity.extract_code(nb):
        with open(py_file, 'w') as file:
            file.write(NOTICE)
            # comment out IPython's magic commands before writing Python file
            # keep the indentation
            file.write(re.sub(r'(?m)^(\s*)%', r'\1# %', code))

    # NOTE and INFO Markdown text is inside <div>, so convert it to HTML
    jollity.replace_re(nb, 'md:note md:info', [
        # [text](url)   -->     <a href="url">text</a>
        (r'\[([\w\s()]+)\]\((.+)\)', r'<a href="\2">\1</a>'),

        # `text`        -->     <code>text</code>
        (r'`([\w\s(){}[\]\.]+)`', r'<code>\1</code>'),

        # **text**      -->     <strong>text</strong>
        (r'\*\*([\w\s():]+)\*\*', r'<strong>\1</strong>'),

        # _text_ and *text* --> <em>text</em>
        (r'_([a-zA-Z\d\s()]+)_', r'<em>\1</em>'),   # don't use \w: it matches _
        (r'\*([a-zA-Z\d\s()]+)\*', r'<em>\1</em>'),
    ])

    # fill the empty Markdown answer cells with boilerplate text
    jollity.replace_str(nb, 'md:answer', ('', '_Write your answer here._'))

    # remove cells that are empty or have only space (there should be none)
    jollity.remove_cells(nb, 'all', r'^\s*$')
    # remove metadata: don't leave traces of Jollity
    jollity.remove_metadata(nb, 'all')  #

    with open(nb_file, 'w') as file:
        nbformat.write(nb, file)

# at the end, the script does
print('See log.txt for the warning and error messages.')
