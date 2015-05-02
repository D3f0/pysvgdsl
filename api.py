"""
Functions to be exported
"""

from lxml import etree, cssselect


class SVGNode(object):
    """
    Wraps LXML nodes. It provides properties for their attributes so they can
    be binded to Formulas and run in a reactive fashion.
    """
    def __init__(self, etree_node):
        self._etree_node = etree_node

    @property
    def id(self):
        return self._etree_node.attrib['id']

    def __str__(self):
        return '<SVGNode {%s}>' % self.id

    __repr__ = __str__


class SVG(object):
    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
    }

    def __init__(self, path):
        self.etree = etree.parse(path)
        self._node_cache = {}

    def elements(self):
        pass

    def __getitem__(self, element_id):
        """
        Returns a wrapped element whose id matches
        i.e: svg['node.style'] = 'A**2'
        """
        if element_id not in self._node_cache:
            self._node_cache[element_id] = self.get_by_selector(element_id)
        return self._node_cache[element_id]

    @property
    def base_selector(self):
        return 'svg|g > '

    def nodes(self):
        # Inspired in https://github.com/
        # zacharyvoase/glyphicons-splitter/blob/master/extract_icons.py
        selector = self.base_selector + 'svg|*'
        nodes = cssselect.CSSSelector(selector, namespaces=self.namespaces)(self.etree)
        return [self.nodeFactory(node) for node in nodes]

    def get_by_selector(self, elem_id):
        selector = self.base_selector + 'svg|*#{}'.format(elem_id)
        try:
            nodes = cssselect.CSSSelector(selector, namespaces=self.namespaces)(
                self.etree
            )
        except cssselect.SelectorSyntaxError as e:
            raise ValueError('%s generated error: %s' % (selector, e))
        count = len(nodes)
        if count == 0:
            raise ValueError("Element #%s does not exist" % elem_id)
        elif count != 1:
            raise ValueError("Too many elements with id %s" % elem_id)
        return self.nodeFactory(nodes[0])

    def nodeFactory(self, node):
        node = SVGNode(node)
        self._node_cache[node.id] = node
        return node
