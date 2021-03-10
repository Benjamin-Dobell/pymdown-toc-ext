# pymdown-toc-ext: Table of Contents (Extended)

An extension for [Python-Markdown](https://python-markdown.github.io) which extends the built-in
[toc](https://python-markdown.github.io/extensions/toc/) with additional capabilities to customize the generated table
of contents.

## Setup

### Prerequisites

Aside from Python-Markdown itself, you'll want to enable the official Python-Markdown
[attr_list](https://python-markdown.github.io/extensions/attr_list/) extension.

### Installation

```sh
pip install pymdown-toc-ext
```

### Python-Markdown API

Please refer to https://python-markdown.github.io/extensions/

### MkDocs

In `mkdocs.yml` under `markdown_extensions` replace `toc` with `toc_ext` i.e.

```yaml
markdown_extensions:
  - toc_ext
```

### Configuration

This extension extends the built-in Markdown `toc` extensions. All
[its configuration options](https://python-markdown.github.io/extensions/toc/) are supported. 

## Usage

pymdown-toc-ext looks for the presence of `data-toc-*` attributes on Markdown elements. Given Markdown itself doesn't
provide support for adding attributes, this is why the Markdown `attr_list` extension is required.

### Inserting a new entry

The purpose of the Table of Contents is to provide links to some point in your document. The standard `toc` extension
just supports Markdown headers, however we'll support any element with both and ID and the `data-toc-label` attribute.

```markdown
[](){: #top data-toc-label="Goto Top" }
```

This will insert an entry with the text "Goto Top" linking to our empty (i.e. invisible) anchor with the ID `top`.

_**Note**: We strip `data-toc-*` attributes that we consume. So the above will simply generate `<a id="top" href=""></a>`._

### Inserting a child entry

By default, we insert entries at the _top_ of the Table of Contents. However, we may wish to insert the entry as a child
of another entry. This is achieved by the inclusion of the `data-toc-parent` attribute specifying the ID of another TOC
entry.

```markdown

## Category 1

[](){: #intro data-toc-label="Intro" data-toc-parent="category-1" } Some introductory text that doesn't warrant a heading.

## Category 2

[](){: #top data-toc-label="Technobabble" data-toc-parent="glossary" }**Technobabble** is really important:

* We want readers to understand the concept before moving on. 
* We don't want unnecessary headings breaking the page's flow.
* We also want this definition appearing in the Table of Contents, for easy lookup.

## Glossary

### Peripheral

Of secondary or minor importance.
```

The above will generate:

* Category 1
    * Intro
* Category 2
* Glossary
    * Technobabble
    * Peripheral
    
### Inserting after another entry (manual ordering)

In the above example, we ended up with "Technobabble" appearing before "Peripheral". Perhaps we wanted the entries to
appear in alphabetical order.

_Instead_ of specifying a parent, we can specify `data-toc-previous`, with the ID of the element that our entry should
appear after.

```markdown

## Alphabet

[](){: #b data-toc-label="B" data-toc-previous="a" } B.
[](){: #a data-toc-label="A" data-toc-parent="alphabet" } A.
[](){: #c data-toc-label="C" data-toc-previous="b" } C.
```

The above will generate:

* Alphabet
    * A
    * B
    * C


### Sorting

Manual ordering each entry can be tedious. Frequently we just want to alphabetically sort child entries. We can mark an
entry as sorted by setting `data-toc-sort`.

The example above can therefore be alternatively expressed as:

```markdown
## Alphabet {: data-toc-sort }

[](){: #b data-toc-label="B" data-toc-parent="alphabet" } B.
[](){: #a data-toc-label="A" data-toc-parent="alphabet" } A.
[](){: #c data-toc-label="C" data-toc-parent="alphabet" } C.
```

#### Reverse

Reverse ordering is supported by `data-toc-sort="reverse"` e.g.


```markdown
## Alphabet {: data-toc-sort="reverse" }

[](){: #b data-toc-label="B" data-toc-parent="alphabet" } B.
[](){: #a data-toc-label="A" data-toc-parent="alphabet" } A.
[](){: #c data-toc-label="C" data-toc-parent="alphabet" } C.
```

will generate:

* Alphabet
  * C
  * B
  * A

#### Top Level (Root) Sorting

The top level entries don't have a parent that you can mark as sorted. Instead `data-toc-root-sort` may appear
_anywhere_ in your document. Otherwise, it behaves just like `data-toc-sort` on a TOC entry e.g.

Both:

```markdown
[](){: #b data-toc-label="B" data-toc-root-sort } B.
[](){: #a data-toc-label="A" } A.
[](){: #c data-toc-label="C" } C.
```

and: 

```markdown
## B {: data-toc-root-sort }

## A

## C
```

will result in the table of contents: 

* A
* B
* C

## Contributing

Contributions welcome.

### Development

At the time of writing pip cannot install editable poetry packages.

To appease pip, you can generate a `setup.py`  with:

```sh
poetry build --format sdist && tar -xvf dist/*-`poetry version -s`.tar.gz -O '*/setup.py' > setup.py
```

You'll then be able to, in another Python project, install your local editable package with:

```sh
pip install -e /path/to/pymdown-toc/ext
```
