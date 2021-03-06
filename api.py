"""
Functions to be exported
"""

import os
import sys
from lxml import etree, cssselect
from cStringIO import StringIO
from jinja2 import Template
import requests
from lxml.etree import ElementTree
from itertools import count
from subprocess import call
from IPython.display import HTML, Javascript, display


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


# Counter
_id_counter = count(start=1, step=1)


# Generate unique id
def get_id(prefix='svg', suffix=''):
    """Generate unique id"""
    return '-'.join([
        str(x) for x in filter(bool, [
            prefix,
            os.getpid(),
            _id_counter.next(),
            suffix,
        ])])


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

    def show(self, show_script=False):
        """Show SVG in IPython notebook
        @param show_script bool Shows generated script to *stderr*
        This function should be taken away for reuse outside IPython eventually"""
        if not self.display_config:
            raise Exception("This object does not have a display_config attribute.")

        copy = ElementTree(self.etree.getroot())
        this_id = get_id()
        copy.getroot().attrib['id'] = this_id
        io = StringIO()
        copy.write(io)

        template = Template('''
            require.config({
                paths: {
                    d3: '{{ static_url }}d3',
                    dynsvg: '{{ static_url }}dynsvg'
                },
                // Bust cache
                urlArgs: "bust=" + (new Date()).getTime()
            });
            require(['d3', 'dynsvg'], function (d3, dynsvg) {
                dynsvg.makeConnection('{{ ws_url}}', '#{{this_id}}');

            }, function (err) {
                console.error("Error", err);
            });
        ''')

        output = template.render(
            this_id=this_id,
            **self.display_config
        )

        display(HTML(io.getvalue()))
        if show_script:
            sys.stderr.write(output)
        display(Javascript(output))

        # return HTML(output)

    def update(self, elem_id, data):
        """Sends update to the client via websocket connection.
        Websocket connection is made through pusher interface."""
        payload = {elem_id: data}
        req = requests.post(self.display_config['pusher_url'], json=payload)
        return req

    def external_edit(self):
        """Call svg program"""
        platform = sys.platform
        if platform == 'darwin':
            call('')
        elif 'linux' in platform:
            raise NotImplemented(platform)
        elif 'win' in platform:
            raise NotImplemented(platform)


def load_svg(path):
    """Starts the webserver if nesseary"""
    from server import start_webserver
    # FIXME: Second call needs to get the exiting port
    ok, port = start_webserver()
    print port
    config_for_ipython = dict(
        static_url='http://localhost:{port}/static/'.format(port=port),
        ws_url='ws://localhost:{port}/ws'.format(port=port),
        pusher_url='http://localhost:{port}/pusher'.format(port=port),
    )
    return DSVG(path, display_config=config_for_ipython)
