"""
Functions to be exported
"""
from lxml import etree


etree.register_namespace("", "http://www.w3.org/2000/svg")


class SVGNode(object):
    """
    Wraps LXML nodes. It provides properties for their attributes so they can
    be binded to Formulas and run in a reactive fashion.
    """
    pass


class SVG(object):
    def __init__(self, path):
        self.etree = etree.parse(open(path, 'r'))

    def elements(self):
        pass

    def __getitem__(self, element_id):
        """
        Returns a wrapped element whose id matches
        """
        pass

    def nodes(self):
        return [self.nodeFactory(n) for n in self.etree.iter()]

    def nodeFactory(self, node):
        return SVGNode(node)
