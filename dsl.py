from rx.subject import BehaviorSubject


class ValueStore(object):
    def get_inital_value(self, name):
        """
        DB lookups, etc.
        """
        raise NotImplementedError("Error")


class ValueStoreDjango(object):

    def get_inital_value(self, name):
        if 'DI' in name.upper():
            return 0
        elif 'AI' in name.upper():
            return 0
        else:
            return '0'


class ValueCollection(object):
    def __init__(self, value_store=None):
        self.values = {}
        self.value_store = value_store

    def get(self, name):
        if name not in self.values:
            self.values[name] = self.create(name)
        return self.values[name]

    def create(self, name):
        initial = self.value_store.get_inital_value(name)
        subject = BehaviorSubject(initial)
        return subject


