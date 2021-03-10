from xml.etree.ElementTree import Element, SubElement

from markdown.extensions.toc import TocExtension, TocTreeprocessor

__monkey_patched = False

def _monkey_patch_mkdocs():
    if __monkey_patched:
        return
    try:
        _monkey_patched = True
        mkdocs_toc = __import__('mkdocs.structure.toc').structure.toc

        class AnchorLinkExt(mkdocs_toc.AnchorLink):
            def __init__(self, title, id, level, url):
                super().__init__(title, id, level)
                self._url = url

            @mkdocs_toc.AnchorLink.url.getter
            def url(self):
                return self._url if self._url else super().url

        def _parse_toc_token(token):
            anchor = AnchorLinkExt(token['name'], token['id'], token['level'], token.get('url'))
            for i in token['children']:
                anchor.children.append(_parse_toc_token(i))
            return anchor

        # This is absurdly fragile
        mkdocs_toc._parse_toc_token = _parse_toc_token
    except ImportError:
        pass

def _tokens_to_dicts(tokens):
    token_dict = {}
    parent_token_dict = {}

    def visit(token):
        token_dict[token['id']] = token

        for child in token['children']:
            parent_token_dict[child['id']] = token
            visit(child)

    for token in tokens:
        visit(token)

    return token_dict, parent_token_dict

def _insert_ext_token(tokens, ext_token, token_dict, parent_token_dict, ext_token_dict):
    [token, parent_id, previous_id] = ext_token

    if 'level' not in token:
        id = token['id']

        if parent_id:
            parent = token_dict.get(parent_id)

            if not parent:
                ext_parent = ext_token_dict.get(parent_id)
                if ext_parent:
                    parent = _insert_ext_token(tokens, ext_parent, token_dict, parent_token_dict, ext_token_dict)

            if not parent:
                return None

            token['level'] = parent['level'] + 1

            parent['children'].insert(0, token)
            token_dict[id] = token
            parent_token_dict[id] = parent

            return token
        elif previous_id:
            previous = token_dict.get(previous_id)

            if not previous:
                ext_previous = ext_token_dict.get(previous_id)
                if ext_previous:
                    previous = _insert_ext_token(tokens, ext_previous, token_dict, parent_token_dict, ext_token_dict)

            if not previous:
                return None

            parent = parent_token_dict.get(previous['id'])
            siblings = parent['children'] if parent else tokens

            token['level'] = previous['level']

            siblings.insert(siblings.index(previous) + 1, token)
            token_dict[id] = token
            parent_token_dict[id] = parent
        else:
            token['level'] = 1

            tokens.insert(0, token)
            token_dict[id] = token

    return token

def _insert_ext_tokens(tokens, ext_tokens, token_dict, parent_token_dict):
    ext_token_dict = {}

    for ext_token in ext_tokens:
        ext_token_dict[ext_token[0]['id']] = ext_token

    for ext_token in ext_tokens:
        _insert_ext_token(tokens, ext_token, token_dict, parent_token_dict, ext_token_dict)

def _token_name_lower(token):
    return token['name'].lower()

def _sort_tokens(tokens, behavior):
    flags = set(behavior.split(' '))

    reverse = True if 'reverse' in flags else False
    tokens.sort(key = _token_name_lower, reverse=reverse)

def _populate_toc_level_element(parent, toc_list):
    ul = SubElement(parent, 'ul')
    for token in toc_list:
        li = SubElement(ul, 'li')
        anchor = SubElement(li, 'a')
        anchor.text = token['name']
        anchor.attrib['href'] = token['url'] if 'url' in token else '#' + token['id']
        if token['children']:
            _populate_toc_level_element(li, token['children'])
    return ul

def _build_toc_element(toc_tokens, title):
    div = Element('div')
    div.attrib['class'] = 'toc'
    if title:
        header = SubElement(div, 'span')
        header.attrib['class'] = 'toctitle'
        header.text = title
    _populate_toc_level_element(div, toc_tokens)
    return div

class TocExtTreeprocessor(TocTreeprocessor):
    def __init__(self, md, config):
        super().__init__(md, config)

    # Ssh ssh. Quiet now. This is fine. Not likely to break at all.
    def build_toc_div(self, toc_tokens):
        ext_tokens = []

        token_dict, parent_token_dict = _tokens_to_dicts(toc_tokens)
        sort_token_ids = {}
        sort_root = None

        for el in self.doc.iter():
            attrib = el.attrib

            if 'id' in attrib:
                id = attrib['id']

                if 'data-toc-omit' in attrib:
                    token = token_dict.get(id)
                    if token:
                        parent_token = parent_token_dict.get(id)
                        siblings = parent_token['children'] if parent_token else toc_tokens
                        index = siblings.index(token)
                        siblings[index:index+1] = token['children']

                        del token_dict[id]
                        if id in parent_token_dict:
                            del parent_token_dict[id]
                        for child in token['children']:
                            parent_token_dict[child['id']] = parent_token
                    continue

                if 'data-toc-sort' in attrib:
                    sort_token_ids[id] = attrib['data-toc-sort']
                    del attrib['data-toc-sort']

                if 'data-toc-label' in attrib:
                    token = {
                        'id': id,
                        'name': attrib['data-toc-label'],
                        'children': []
                    }

                    if 'data-toc-url' in attrib:
                        token['url'] = attrib['data-toc-url']
                        del attrib['data-toc-url']

                    parent_id = attrib['data-toc-child-of'] if 'data-toc-child-of' in attrib else None
                    if parent_id == id:
                        parent_id = None

                    previous_id = attrib['data-toc-after'] if 'data-toc-after' in attrib else None
                    if previous_id == id:
                        previous_id = None

                    ext_tokens.append([
                        token,
                        parent_id,
                        previous_id
                    ])

                    del attrib['data-toc-label']
                    if parent_id:
                        del attrib['data-toc-child-of']
                    if previous_id:
                        del attrib['data-toc-after']

            if 'data-toc-root-sort' in attrib:
                sort_root = attrib['data-toc-root-sort']
                del attrib['data-toc-root-sort']

        _insert_ext_tokens(toc_tokens, ext_tokens, token_dict, parent_token_dict)

        for id, behavior in sort_token_ids.items():
            token = token_dict.get(id)
            _sort_tokens(token['children'], behavior)

        if sort_root:
            _sort_tokens(toc_tokens, sort_root)

        toc_element = _build_toc_element(toc_tokens, self.title)

        if 'prettify' in self.md.treeprocessors:
            self.md.treeprocessors['prettify'].run(toc_element)

        return toc_element

    def run(self, doc):
        self.doc = doc
        try:
            super().run(doc)
        finally:
            self.doc = None


class TocExtExtension(TocExtension):

    TreeProcessorClass = TocExtTreeprocessor

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, config):
        self.__config = z = {**self.__config, **config}

    def __init__(self, **kwargs):
        self.__config = {
            "patch_mkdocs": [True,
                       'Whether we should patch mkdocs to enable support for'
                       'custom URLs in its TOCs. Defaults to True']
        }
        super().__init__(**kwargs)
        if self.config['patch_mkdocs'][0]:
            _monkey_patch_mkdocs()
