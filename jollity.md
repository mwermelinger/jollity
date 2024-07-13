# Jollity

Initially just a library of functions on nb objects.
Use Python's logging. Latter convert log to nb with links to error locations.

---

## Features
### Comments

Must be removed before expanding special comments.
Must test with
```
<!-- INFO --
...
<!-- INFO -->
```

### MD lint

Report if

- jumping from level n to level > n+1
- mismatch of pipes in header and separator of tables
- 2+ spaces at end of line

### Navigation

Cross-links
Myst has `(target)=` to set label before header.

Expand URLs in `[...](url)` using dict. Then resolve
cross-refs. They should be case insensitive, as in pandoc.

### Code

Report if cell throws error, unless it's tagged (or metadata) otherwise.

Extract code from nb. nbconvert to python starts with
```
#!/usr/bin/env python
# coding: utf-8
```

and then precedes each code cell with `# In[4]`.
Code has two blank lines before and after.

GH Md allows any text after code fence,
but Atom/Hydrogen doesn't cope with that:
Atom doesn't highlight code properly and Hydrogen doesn't run it.
```py hello
x = 5
```

### Other
Make cells non-deletable.

def open_nb(name: str) -> NoteBookNode:
    """Open the named file and return the notebook object."""
    nb = nbformat.read(name, nbformat.current_nb_format)
    folder_name, file_name = os.path.split(name)
    match = re.match(r'(\d+)(-introduction|_[\dA])', file_name)
    chapter = section = 0
    if match:
        chapter = int(match.group(1))
        if match.group(2)[0] == '_':
            section = int(match.group(2)[1:], 16)
    nb.metadata['jollity'] = {
        'folder': folder_name,
        'file': file_name,
        'chapter', chapter,
        'section': section,
    }
    return nb

---

## Why not other approaches?

In a nutshell: CommonMark, Myst, CriticMark etc use special characters and
hence render poorly in GitHub Markdown used by Jupyter.

For example, CommonMark includes `% comment` and
YAML headers are rendered with horizontal line in Jupyter.
```
---
key: value
---
```

Myst has general syntax for directives and roles that can be user defined:
``{role}`text` `` and

````
```{directive}
:option: value

content
```
````

Pandoc has general syntax for extra info after header, code fence or image: `{#id .class key=val}`.

In Jupyter Book, notebooks are intermediate format towards HTML, not final format. Running individual cells (or notebook?) in Binder is not most convenient. Can change and apply changes to HTML book?

nbconvert converts each nb separately eg to PDF. Although the resources dict is passed from each preprocessor to the next, they're all processing the same nb.

## Plans

- add multi-file features:
    - input is full list of nbs eg [cover, [ch1intro, 1.1, …], [ch2intro, …], …]
    - add toc to each intro
    - add prev/next footer/header
    - handle xrefs
- tell both Jupyter WG Teams about updates
- once stable tell authors of book on teaching w/ Jupyter
- present at a Jupyter Conference?
