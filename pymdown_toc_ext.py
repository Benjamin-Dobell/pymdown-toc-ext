from markdown.extensions.toc import TocExtension, TocTreeprocessor
import json

def tokens_to_dicts(tokens):
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

def insert_ext_token(tokens, ext_token, token_dict, parent_token_dict, ext_token_dict):
    [token, parent_id, previous_id] = ext_token

    if 'level' not in token:
        id = token['id']

        if parent_id:
            parent = token_dict.get(parent_id)

            if not parent:
                ext_parent = ext_token_dict.get(parent_id)
                if ext_parent:
                    parent = insert_ext_token(tokens, ext_parent, token_dict, parent_token_dict, ext_token_dict)

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
                    previous = insert_ext_token(tokens, ext_previous, token_dict, parent_token_dict, ext_token_dict)

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

def insert_ext_tokens(tokens, ext_tokens, token_dict, parent_token_dict):
    ext_token_dict = {}

    for ext_token in ext_tokens:
        ext_token_dict[ext_token[0]['id']] = ext_token

    for ext_token in ext_tokens:
        insert_ext_token(tokens, ext_token, token_dict, parent_token_dict, ext_token_dict)

def token_name_lower(token):
    return token['name'].lower()

def sort_tokens(tokens, behavior):
    flags = set(behavior.split(' '))

    reverse = True if 'reverse' in flags else False
    tokens.sort(key = token_name_lower, reverse=reverse)

class TocExtTreeprocessor(TocTreeprocessor):
    def __init__(self, md, config):
        super().__init__(md, config)

    # Ssh ssh. Quiet now. This is fine. Not likely to break at all.
    def build_toc_div(self, toc_tokens):
        ext_tokens = []

        token_dict, parent_token_dict = tokens_to_dicts(toc_tokens)
        sort_token_ids = {}
        sort_root = None

        for el in self.doc.iter():
            attrib = el.attrib
            if 'id' in attrib:
                id = attrib['id']

                if 'data-toc-label' in attrib:
                    token = {
                        'id': id,
                        'name': attrib['data-toc-label'],
                        'children': []
                    }

                    parent_id = attrib['data-toc-parent'] if 'data-toc-parent' in attrib else None
                    previous_id = attrib['data-toc-previous'] if 'data-toc-previous' in attrib else None

                    if parent_id == id:
                        parent_id = None

                    if previous_id == id:
                        previous_id = None

                    ext_tokens.append([
                        token,
                        parent_id,
                        previous_id
                    ])

                    del attrib['data-toc-label']
                    if parent_id:
                        del attrib['data-toc-parent']
                    if previous_id:
                        del attrib['data-toc-previous']

                if 'data-toc-sort' in attrib:
                    sort_token_ids[id] = attrib['data-toc-sort']
                    del attrib['data-toc-sort']

            if 'data-toc-root-sort' in attrib:
                sort_root = attrib['data-toc-root-sort']
                del attrib['data-toc-root-sort']

        insert_ext_tokens(toc_tokens, ext_tokens, token_dict, parent_token_dict)

        for id, behavior in sort_token_ids.items():
            token = token_dict.get(id)
            sort_tokens(token['children'], behavior)

        if sort_root:
            sort_tokens(toc_tokens, sort_root)

        return super().build_toc_div(toc_tokens)

    def run(self, doc):
        self.doc = doc
        try:
            super().run(doc)
        finally:
            self.doc = None


class TocExtExtension(TocExtension):

    TreeProcessorClass = TocExtTreeprocessor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
