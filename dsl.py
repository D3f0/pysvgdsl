from __future__ import print_function
from rx.subjects import Subject
from functools import partial
import re
from bunch import Bunch
from logging import getLogger


logger = getLogger(__name__)


_var_regex = re.compile(r'(?P<ns>\w+)\.(?P<var>[\w\d_]+)\.(?P<attr>\w+)')


class ContextDict(object):
    """
    It hold the structure:
        ns -> [TAG, TAG, TAG]
    """
    def __init__(self, node_factory=None, **kwargs):
        """
        @param node_factory
        """
        # assert node_factory is None or callable(node_factory), "Invalid node_factory"
        self.node_factory = node_factory
        self.variables = {}

    def __getitem__(self, name):
        try:
            self.variables[name]
        except KeyError:
            if self.node_factory:
                new = self.node_factory(name)
                self.variables[name] = new
                return new

    def __getattr__(self, name):
        return self.variables[name]

    def __setitem__(self, name, value):
        self.variables[name] = value

    def __dir__(self):
        return self.variables.keys()

    def __str__(self):
        return '<ContextDict %s>' % (','.join(self.variables.keys()[:5]))

    __repr__ = __str__


class Context(object):
    """
    Collection of variables that belong to one or more namespaces:
        [TAG {attr1, attr2, ...}, TAG {attr1, attr2, ...}]
    """
    def __init__(self):
        self.namespaces = Bunch()

    def add_ns(self, name, node_factory=None):
        """
        Validator checks if a vriable is OK in the namespace
        """
        if not self.has_ns(name):
            # Check if context should be parametrized
            self.namespaces[name] = ContextDict(node_factory=node_factory)

    def has_ns(self, name):
        return name in self.namespaces

    def update(self, **values):
        pass

    def get_value(self, name):
        """Fully quialified variable name, for example ai.E4ABAR01.value"""
        ns, varname, attribute = name.split('.')
        return self.namespaces[ns][varname][attribute].value

    def get_observable(self, name):
        """Fully quialified vairable name, for example ai.E4ABAR01.value"""

    def __getitem__(self, fqname):
        match = _var_regex.search(fqname)
        assert match, "%s did not work" % fqname
        ns, var, attr = match.groups()
        return self.namespaces[ns][var]

    def __getattr__(self, name):
        return self.namespaces[name]

    def __str__(self):
        return "<Context %s>" % (','.join(self.namespaces.keys()))

    def __dir__(self):
        """For autocompletion"""
        print("Suggestions...")
        try:
            suggestions = super(Context, self).__dir__()
        except Exception:
            suggestions = []
        suggestions.append(self.namespaces.keys())
        return suggestions


class FormulaManager(object):
    """Holds formulas"""

    def __init__(self, context=None, namespaces=None):
        if context:
            self.context = context
        else:
            # Construct default context
            self.context = Context()
        if namespaces:
            if isinstance(namespaces, basestring):
                self.context.add_ns(namespaces)
            else:
                map(self.context.add_ns, namespaces)
        self.formulas = []

    def add_formula(self, text, target=None, attribute=None):
        """Creates an instance of formula"""
        instance = Formula(text, context=self.context)
        self.formulas.append(instance)


class Formula(object):

    def __init__(self, text, target=None, context=None):
        assert context is not None, "Context cannot be null"
        self.context = context

        if not target:
            self.target, self.text = self.split_target_text(text)
        else:
            self.text = text
            self.target = target

    ASSIGNMENT_CHAR = '='

    def split_target_text(self, text):
        """Validates and splits a X3 = F(X1, X2) into X1, F(X1, X2)"""
        assignments = text.count(self.ASSIGNMENT_CHAR)
        if assignments == 0:
            raise ValueError("No assignments in %s" % text)
        elif assignments > 1:
            pass
            # TODO: Better validation
            # raise ValueError("More than one assignments in %s" % text)
        return text.split(self.ASSIGNMENT_CHAR, 1)

    def bind_changes(self, variables):
        for var in variables:
            var_obj = self.context[var]
            print("Binding variables of ", var, var_obj)

    _text = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        # TODO: Validate
        self.bind_changes(self.extract_vairables(value))
        self._text = value

    @staticmethod
    def extract_vairables(text):
        """Constructs a regex to extract all variables from formula text"""
        return [v.group() for v in _var_regex.finditer(text)]

    def evaluate(self):
        """target.attribtue = evaluation"""
        new_value = eval(self.text, self.context)
        if new_value != self.old_value:
            self.target.value = new_value

    def __str__(self):
        return self.text


class MultiAttrNode(object):
    """Holds values but also can show itself inside a IPython notebook"""
    def __init__(self, name, description, **initials):
        assert bool(initials), "Initial values empty"
        self.name = name
        self.description = description
        self.values = initials
        self.subjects = {name: Subject() for name in self.values.keys()}

    def show(self):
        from IPython.html.widgets import HBox, VBox, HTML
        return VBox([
            HTML(self.name),
            HBox([self.create_widget(n) for n in self.values.keys()])
        ])

    def create_widget(self, name):
        from IPython.html.widgets import IntSlider, HTML, HBox
        w = IntSlider(value=self[name])

        def callback(_name, new_value):
            self[name] = new_value

        w.on_trait_change(
            name='value', handler=callback
        )
        return HBox([HTML('<h4>%s</h4>%s' % (name, self.description or '')), w])

    def __getitem__(self, name):
        return self.values[name]

    __getattr__ = __getitem__

    def __setitem__(self, name, value):
        assert name in self.values, "Invalid value %s" % name
        self.values[name] = value
        self.subjects[name].on_next(value)

    def __getattr__(self, name):
        print(name)
        return object.__getattr__(self, name)

    def __str__(self):
        return '<MultiAttrNode {name} {description}>'.format(
            name=self.name,
            description=self.description or '.'
        )

    __repr__ = __str__


class SMVEFormulaManager(FormulaManager):
    def __init__(self, *args, **kwargs):
        super(SMVEFormulaManager, self).__init__(*args, **kwargs)
        self.context = Context()

        def ai_factory(name):
            return MultiAttrNode(name, None, value=1, q=1, escala=1)

        def di_factory(name):
            return MultiAttrNode(name, None, value=1, q=1)

        def eg_factory(name):
            return MultiAttrNode(name, None, text='0', fill='black', stroke='green')

        self.context.add_ns('ai', ai_factory)
        self.context.add_ns('di', di_factory)
        self.context.add_ns('eg', eg_factory)
