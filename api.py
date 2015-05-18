"""
Functions to be exported
"""

from lxml import etree, cssselect
from cStringIO import StringIO
from jinja2 import Template


class SVGNode(object):
    """
    Wraps LXML nodes. It provides properties for their attributes so they can
    be binded to Formulas and run in a reactive fashion.
    """
    def __init__(self, svg, node):
        """

        """
        self.parent = svg
        self.node = node

    @property
    def id(self):
        return self.node.attrib['id']

    def __str__(self):
        return '<SVGNode {%s} (%s)>' % (self.id, self.node.tag)

    def __setattr__(self, name, value):
        """Sets an attribtue, that may be a formula"""
        pass

    __repr__ = __str__


class DSVG(object):
    """Makes a SVG dynamic.

    Internally talks to lxml to handle SVG efficiently.
    """
    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
    }

    def __init__(self, path=None, source=None, display_config=None):
        # FIXME: Make this work more in IPython.display.SVG way
        assert bool(path) ^ bool(source), "Source and path cannot be used at the same time"
        if path:
            self.etree = etree.parse(path)
        else:
            fp = StringIO()
            fp.write(source)
            fp.seek(0)
            self.etree = etree.parse(fp)
        self._node_cache = {}

        self.display_config = display_config

    @classmethod
    def from_file():
        pass

    @classmethod
    def from_string():
        pass

    def __getitem__(self, element_id):
        """
        Returns a wrapped element whose id matches
        i.e: svg['node.style'] = 'A**2'
        """
        if element_id not in self._node_cache:
            self._node_cache[element_id] = self.get_by_selector(element_id)
        return self._node_cache[element_id]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise

    def __dir__(self):
        """For better autocompletion"""
        print "Called dir..."
        res = dir(type(self)) + list(self.__dict__.keys())
        if not self._node_cache:
            self._fill_cache()
        res.extend(self._node_cache.keys())
        return res

    @property
    def base_selector(self):
        """Base selector for queries in DOM"""
        return 'svg|g > '

    def css_select(self, query):
        selector = self.base_selector + query
        try:
            nodes = cssselect.CSSSelector(query, namespaces=self.namespaces)(self.etree)
        except cssselect.SelectorSyntaxError as e:
            raise ValueError('%s generated error: %s' % (selector, e))
        return nodes

    def _fill_cache(self):
        nodes = self.css_select('svg|*[id]')
        self._node_cache = {
            node.attrib.id: self.nodeFactory(node) for node in self.css_select(nodes)
        }

    @property
    def nodes(self):
        # Inspired in https://github.com/
        # zacharyvoase/glyphicons-splitter/blob/master/extract_icons.py
        if not self._node_cache:
            self._fill_cache()
        return self._node_cache.values()

    def get_by_selector(self, elem_id):
        selector = 'svg|*#{}'.format(elem_id)

        nodes = self.css_select(selector)

        count = len(nodes)
        if count == 0:
            raise ValueError("Element #%s does not exist" % elem_id)
        elif count != 1:
            raise ValueError("Too many elements with id %s" % elem_id)
        return self.nodeFactory(nodes[0])

    def nodeFactory(self, node):
        # Does not fill cache, there's an speciallized method for that
        node = SVGNode(self, node)
        return node

    def display(self):
        """Show in IPython notebook

        This function should be taken away for reuse outside IPython eventually"""
        if not self.display_config:
            raise Exception("This object does not have a display_config attribute.")
        from IPython.display import HTML
        io = StringIO()
        self.etree.write(io)

        template = Template('''
            {{svg}}
            <script tyle="text/javascript">
                require.config({
                    paths: {
                        d3: '{{ static_url }}d3',
                        dynsvg: '{{ static_url }}dynsvg'
                    }
                });
                require(['d3', 'dynsvg'], function (d3, dynsvg) {
                    alert("Fooo");
                }, function (err) {
                    console.error("Error", err);
                });
            </script>
        ''')

        output = template.render(
            svg=io.getvalue(),
            **self.display_config
        )
        return HTML(output)


def load_svg(path):
    """Starts the webserver if nesseary"""
    from server import start_webserver
    # FIXME: Second call needs to get the exiting port
    ok, port = start_webserver()
    print port
    config_for_ipython = dict(
        static_url='http://localhost:{port}/static/'.format(port=port)
    )
    return DSVG(path, display_config=config_for_ipython)
